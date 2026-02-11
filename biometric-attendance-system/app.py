from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from models import db, Admin, Faculty, Student, AttendanceRecord, Subject, LeaveApplication, Timetable, AttendanceSession
from face_recognition_api import encode_face_from_image, encode_face_from_array, find_matching_student, detect_faces_in_frame
from datetime import datetime, date, time
import datetime as dt
import json
import os
from dotenv import load_dotenv
from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

# Load environment variables
load_dotenv()
import cv2
import numpy as np
import pandas as pd
from io import BytesIO
import base64
from config import DATABASE_URI, DATABASE_TYPE

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Database Configuration - PostgreSQL (Supabase) or SQLite (local)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Production: Use Supabase PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print("DEBUG: Using PostgreSQL (Supabase)")
else:
    # Development: Use local SQLite or use DATABASE_URI from config
    if DATABASE_URI:
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    else:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'attendance.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    print(f"DEBUG: Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Session Configuration for Local Dev
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False # Important for HTTP
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = False

from flask_wtf.csrf import CSRFProtect, generate_csrf

# Initialize extensions
db.init_app(app)
# CSRF TEMPORARILY DISABLED FOR DEBUGGING
# csrf = CSRFProtect(app)
# app.jinja_env.globals['csrf_token'] = generate_csrf
login_manager = LoginManager()

# @app.context_processor
# def inject_csrf_token():
#     return dict(csrf_token=generate_csrf)

# Provide dummy csrf_token function when CSRF is disabled
def dummy_csrf_token():
    """Dummy CSRF token function that returns empty string when CSRF is disabled"""
    return ''

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=dummy_csrf_token)

print("DEBUG: App Configuration Loaded. CSRF DISABLED.")

login_manager.init_app(app)
login_manager.login_view = 'login'

# Setup directories
os.makedirs('database', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    print(f"DEBUG: load_user called with {user_id}")
    if user_id.startswith('admin_'):
        return Admin.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('faculty_'):
        return Faculty.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('student_'):
        return Student.query.get(int(user_id.split('_')[1]))
    return None


# --- Admin helpers (safe) ---
def create_default_accounts():
    """Create default admin, faculty and some subjects if they don't exist.
    This is safer than running a full init (no drop_all).
    """
    from werkzeug.security import generate_password_hash
    from models import Subject

    with app.app_context():
        created = []
        if not Admin.query.filter_by(email='admin@college.edu').first():
            admin = Admin(
                name='System Admin',
                email='admin@college.edu',
                password=generate_password_hash('admin123'),
                contact_no=1234567890
            )
            db.session.add(admin)
            created.append('admin')

        if not Faculty.query.filter_by(email='faculty@college.edu').first():
            faculty = Faculty(
                name='Dr. Smith',
                email='faculty@college.edu',
                password=generate_password_hash('faculty123'),
                contact_no=9876543210
            )
            db.session.add(faculty)
            created.append('faculty')

        # Ensure some default subjects
        subjects = [
            ('Mathematics-I','FY',1),
            ('Physics-I','FY',1),
            ('Computer Science-I','FY',2),
        ]
        for name, class_name, sem in subjects:
            existing = Subject.query.filter_by(name=name, class_name=class_name, semester=sem).first()
            if not existing:
                db.session.add(Subject(name=name, class_name=class_name, semester=sem))
                created.append(f'subject:{name}')

        if created:
            db.session.commit()
        return created


# Protected HTTP endpoint to create defaults when you cannot run commands on the host
@app.route('/internal/create-defaults', methods=['POST'])
def http_create_defaults():
    token = request.args.get('token') or request.headers.get('X-Init-Token')
    if not token or token != os.environ.get('INIT_DB_TOKEN'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        created = create_default_accounts()
        return jsonify({'success': True, 'created': created}), 200
    except Exception as e:
        logger.exception('Error creating default accounts')
        return jsonify({'success': False, 'error': str(e)}), 500

# Custom Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Resource not found'}), 404
    return render_template('login.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f'Internal server error: {error}')
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    return render_template('login.html', error='An error occurred. Please try again.'), 500

# --- PUBLIC ROUTES ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        user = None
        if user_type == 'admin':
            user = Admin.query.filter_by(email=email).first()
        elif user_type == 'faculty':
            user = Faculty.query.filter_by(email=email).first()
        elif user_type == 'student':
            # For students, 'email' field in form will carry enrollment number
            user = Student.query.filter_by(enrollment_number=email).first()
            
        if user:
            # Verify password hash
            if check_password_hash(user.password, password):
                print(f"DEBUG: Login successful for {email}")
                login_user(user)
                session['user_type'] = user_type
                if user_type == 'student':
                    return redirect(url_for('student_dashboard'))
                return redirect(url_for('dashboard'))
            else:
                print(f"DEBUG: Invalid password for {email}")
        else:
            print(f"DEBUG: User not found for {email} ({user_type})")
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

# --- DASHBOARD & CORE ---
@app.route('/dashboard')
@login_required
def dashboard():
    user_type = session.get('user_type', 'faculty')
    
    # Stats for Dashboard
    student_count = Student.query.count()
    subject_count = Subject.query.count()
    today_attendance = AttendanceRecord.query.filter_by(date=date.today()).count()
    
    # Chart Data: Last 7 Days
    dates = []
    counts = []
    for i in range(6, -1, -1):
        d = date.today() - dt.timedelta(days=i)
        c = AttendanceRecord.query.filter_by(date=d).count()
        dates.append(d.strftime('%d %b'))
        counts.append(c)
        
    # Chart Data: Today's Status
    present = today_attendance
    # Approximate absent (Total Students * Total Lectures Today - Present)
    # This is complex to get exact without schedule, so we'll use a simplified metric:
    # Present vs Registered Students (assuming 1 lecture/student/day for demo)
    absent = max(0, student_count - present) 
    
    return render_template('dashboard.html', 
                         user_type=user_type, 
                         user=current_user,
                         stats={
                             'students': student_count,
                             'subjects': subject_count,
                             'today': today_attendance
                         },
                         chart_data={
                             'dates': json.dumps(dates),
                             'counts': json.dumps(counts),
                             'present': present,
                             'absent': absent
                         })
                         
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if session.get('user_type') != 'student':
        return redirect(url_for('dashboard'))
        
    student = current_user
    
    # Calculate Attendance
    total_records = AttendanceRecord.query.filter_by(student_id=student.student_id).all()
    attended = [r for r in total_records if r.status == 'Present']
    
    total_lectures = len(total_records) # Simplified: Assuming only records exist for classes held
    # To be more accurate, we'd need a timetable or "total lectures held" metric per subject.
    # For this dashboard in this codebase context, we'll show Stats based on marked records.
    
    present_count = len(attended)
    absent_count = total_lectures - present_count
    percentage = (present_count / total_lectures * 100) if total_lectures > 0 else 0
    
    return render_template('student_dashboard.html', 
                           student=student,
                           total=total_lectures,
                           present=present_count,
                           absent=absent_count,
                           percentage=round(percentage, 1),
                           recent_records=total_records[-10:][::-1]) # Last 10 reversed

# --- STUDENT MANAGEMENT ---
@app.route('/students')
@login_required
def students():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    students = Student.query.all()
    return render_template('students.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            enrollment_number = request.form.get('enrollment_number')
            class_name = request.form.get('class_name')
            dob_str = request.form.get('dob')
            password = request.form.get('password') # Optional, default if empty
            photo = request.files.get('photo')
            
            if not all([name, enrollment_number, class_name, photo, dob_str]):
                flash('All fields are required', 'error')
                return redirect(url_for('add_student'))

            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid date format")
                return redirect(url_for('add_student'))

                                
    

                
            # Check for duplicates
            if Student.query.filter_by(enrollment_number=enrollment_number).first():
                flash(f'Student with enrollment {enrollment_number} already exists', 'error')
                return redirect(url_for('add_student'))

            # Save photo
            filename = secure_filename(f"{enrollment_number}_{photo.filename}")
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            
            # Encode face
            try:
                face_encoding = encode_face_from_image(photo_path)
                if face_encoding is None:
                    flash('No face detected in photo. Please upload a clear photo with visible face.', 'error')
                    return redirect(url_for('add_student'))
            except ImportError as ie:
                flash(f'Error processing image: {str(ie)}', 'error')
                return redirect(url_for('add_student'))
            

            student = Student(
                name=name,
                enrollment_number=enrollment_number,
                class_name=class_name,
                password=generate_password_hash(password) if password else generate_password_hash('123456'),
                face_encoding=json.dumps(face_encoding),
                photo_url=photo_path,
                dob=dob,
                admission_date=date.today()
            )
            db.session.add(student)
            db.session.commit()
            
            flash('Student added successfully', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            
    return render_template('add_student.html')

@app.route('/delete_student/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student = Student.query.get_or_404(id)
    
    # Delete photo file if it exists
    if student.photo_url and os.path.exists(student.photo_url):
        try:
            os.remove(student.photo_url)
        except:
            pass
            
    # Delete records and student
    AttendanceRecord.query.filter_by(student_id=id).delete()
    db.session.delete(student)
    db.session.commit()
    
    flash('Student deleted successfully', 'success')
    return redirect(url_for('students'))

# --- FACULTY MANAGEMENT ---
@app.route('/faculty')
@login_required
def faculty():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    faculty_list = Faculty.query.all()
    return render_template('faculty.html', faculty_list=faculty_list)

@app.route('/add_faculty', methods=['GET', 'POST'])
@login_required
def add_faculty():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        contact_no = request.form.get('contact_no')
        
        if not all([name, email, password, contact_no]):
            flash('All fields are required', 'error')
            return redirect(url_for('add_faculty'))
            
        if Faculty.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('add_faculty'))
            
        # validate contact number is numeric
        try:
            contact_no_int = int(contact_no)
        except Exception:
            flash('Contact number must be numeric', 'error')
            return redirect(url_for('add_faculty'))

        new_faculty = Faculty(
            name=name,
            email=email,
            password=generate_password_hash(password),
            contact_no=contact_no_int
        )

        try:
            db.session.add(new_faculty)
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            logger.exception('Database integrity error while adding faculty')
            # Check common unique constraint conflicts
            if 'unique' in str(ie).lower() or 'duplicate' in str(ie).lower():
                flash('Email or contact number already exists', 'error')
            else:
                flash('Database error while adding faculty', 'error')
            return redirect(url_for('add_faculty'))
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('Database error while adding faculty')
            flash('An unexpected database error occurred', 'error')
            return redirect(url_for('add_faculty'))

        flash('Faculty added successfully', 'success')
        return redirect(url_for('faculty'))
        
    return render_template('add_faculty.html')

@app.route('/delete_faculty/<int:id>', methods=['POST'])
@login_required
def delete_faculty(id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
        
    faculty_member = Faculty.query.get_or_404(id)
    db.session.delete(faculty_member)
    db.session.commit()
    
    flash('Faculty member deleted', 'success')
    return redirect(url_for('faculty'))

# --- SUBJECT MANAGEMENT ---
@app.route('/subjects')
@login_required
def subjects():
    subjects = Subject.query.all()
    return render_template('subjects.html', subjects=subjects)

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
        
    name = request.form.get('name')
    class_name = request.form.get('class_name')
    
    if name and class_name:
        sub = Subject(name=name, class_name=class_name)
        db.session.add(sub)
        db.session.commit()
        flash('Subject added successfully', 'success')
    
    return redirect(url_for('subjects'))

@app.route('/delete_subject/<int:id>', methods=['POST'])
@login_required
def delete_subject(id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
        
    sub = Subject.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash('Subject deleted', 'success')
    return redirect(url_for('subjects'))

# --- ATTENDANCE ---
@app.route('/attendance')
@login_required
def attendance():
    if session.get('user_type') != 'faculty':
        return redirect(url_for('dashboard'))
    
    return render_template('attendance.html')

@app.route('/api/get_subjects/<class_name>')
@login_required
def get_subjects(class_name):
    semester = request.args.get('semester')
    query = Subject.query.filter_by(class_name=class_name)
    
    if semester:
        try:
            semester_int = int(semester)
            query = query.filter_by(semester=semester_int)
        except ValueError:
            pass  # Ignore invalid semester
    
    subjects = query.all()
    return jsonify([{'id': s.subject_id, 'name': s.name} for s in subjects])

@app.route('/api/recognize_face', methods=['POST'])
@login_required
def recognize_face():
    try:
        from face_recognition_api import analyze_faces
        from sqlalchemy.exc import IntegrityError
        
        data = request.get_json()
        image_data = data.get('image')
        class_name = data.get('class_name')
        subject_id = data.get('subject_id')
        
        if not all([image_data, class_name, subject_id]):
            return jsonify({'success': False, 'error': 'Missing data'})
            
        # Decode image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 1. Analyze Faces (Get Encodings + Liveness)
        faces_data = analyze_faces(frame)
        if not faces_data:
            return jsonify({'success': True, 'results': [], 'message': 'No faces detected'})
            
        # 2. Load Class Students (Optimization: Single DB query)
        students = Student.query.filter_by(class_name=class_name).all()
        # Pre-load encodings into memory to avoid JSON parsing in loop
        known_faces = []
        for s in students:
            if s.face_encoding:
                try:
                    known_faces.append({
                        'student': s,
                        'encoding': json.loads(s.face_encoding)
                    })
                except:
                    continue

        results = []
        today = date.today()
        
        # Get active session for this faculty and subject
        active_session = AttendanceSession.query.filter_by(
            faculty_id=current_user.faculty_id,
            subject_id=subject_id,
            status='Active'
        ).order_by(AttendanceSession.start_time.desc()).first()
        
        # Also check for reopened session
        if not active_session:
            active_session = AttendanceSession.query.filter_by(
                faculty_id=current_user.faculty_id,
                subject_id=subject_id,
                status='Reopened'
            ).order_by(AttendanceSession.start_time.desc()).first()
        
        session_id = active_session.id if active_session else None
        
        # 3. Match Each Detected Face
        for face in faces_data:
            unknown_encoding = face['encoding']
            is_live = face['is_smiling']
            
            best_match = None
            best_distance = 1.0  # Start with worst possible distance
            tolerance = 0.45  # Standardized tolerance threshold

            
            # Find best match from loaded students
            import face_recognition
            if known_faces:
                for entry in known_faces:
                    dist = face_recognition.face_distance([np.array(entry['encoding'])], np.array(unknown_encoding))[0]
                    # Debug print to help tune threshold
                    if dist < 0.6:
                         print(f"DEBUG: Checking {entry['student'].name} - Distance: {dist}")
                         
                    if dist < best_distance:
                        best_distance = dist
                        best_match = entry['student']
            
            # Check if best match meets threshold
            if best_match and best_distance < tolerance:
                print(f"MATCH FOUND: {best_match.name} with distance {best_distance}")
                
                # LIVENESS CHECK
                if not is_live:
                    results.append({
                        'status': 'liveness_failed',
                        'name': best_match.name,
                        'enrollment': best_match.enrollment_number,
                        'message': 'Please Smile',
                        'location': face['location']
                    })
                    continue
                
                # 4. Transaction Handling per Student (Prevent Duplicates)
                try:
                    # Check existence first (cleaner than relying solely on IntegrityError for feedback)
                    existing = AttendanceRecord.query.filter_by(
                        student_id=best_match.student_id,
                        date=today,
                        subject_id=subject_id
                    ).first()
                    
                    if existing:
                        results.append({
                            'status': 'existing',
                            'name': best_match.name,
                            'enrollment': best_match.enrollment_number,
                            'message': 'Already Marked',
                            'location': face['location']
                        })
                    else:
                        # Determine status based on session status
                        if active_session and active_session.status == 'Reopened':
                            record_status = 'Late'
                        else:
                            record_status = 'Present'
                        
                        # Attempt Insert
                        record = AttendanceRecord(
                            date=today,
                            time=datetime.now().time(),
                            status=record_status,
                            method='FaceID',
                            student_id=best_match.student_id,
                            faculty_id=current_user.faculty_id,
                            subject_id=subject_id,
                            session_id=session_id
                        )
                        db.session.add(record)
                        db.session.commit()
                        
                        results.append({
                            'status': 'marked',
                            'name': best_match.name,
                            'enrollment': best_match.enrollment_number,
                            'message': 'Marked Present',
                            'location': face['location']
                        })
                except IntegrityError:
                    db.session.rollback() # Important!
                    results.append({
                        'status': 'existing',
                        'name': best_match.name,
                        'enrollment': best_match.enrollment_number,
                        'message': 'Already Marked (Duplicate)',
                        'location': face['location']
                    })
                except Exception as e:
                    db.session.rollback()
                    print(f"Error marking for {best_match.name}: {e}")
                    results.append({'status': 'error', 'message': str(e), 'location': face['location']})
            else:
                results.append({'status': 'unknown', 'message': 'Unknown Face', 'location': face['location']})

        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# --- SESSION MANAGEMENT API ---
@app.route('/api/session_status')
@login_required
def session_status():
    """Get the current active session for the faculty member"""
    if session.get('user_type') != 'faculty':
        return jsonify({'active': False})
    
    active_session = AttendanceSession.query.filter_by(
        faculty_id=current_user.faculty_id,
        status='Active'
    ).order_by(AttendanceSession.start_time.desc()).first()
    
    if active_session:
        # Calculate remaining time
        elapsed = datetime.now() - active_session.start_time
        remaining_seconds = (active_session.duration_minutes * 60) - elapsed.total_seconds()
        remaining_minutes = max(0, int(remaining_seconds / 60))
        
        return jsonify({
            'active': True,
            'session_id': active_session.id,
            'class_name': active_session.class_name,
            'subject_id': active_session.subject_id,
            'status': active_session.status,
            'remaining_minutes': remaining_minutes
        })
    
    # Check for reopened session
    reopened_session = AttendanceSession.query.filter_by(
        faculty_id=current_user.faculty_id,
        status='Reopened'
    ).order_by(AttendanceSession.start_time.desc()).first()
    
    if reopened_session:
        return jsonify({
            'active': True,
            'session_id': reopened_session.id,
            'class_name': reopened_session.class_name,
            'subject_id': reopened_session.subject_id,
            'status': reopened_session.status,
            'remaining_minutes': 0
        })
    
    return jsonify({'active': False})

@app.route('/api/start_session', methods=['POST'])
@login_required
def start_session():
    """Start a new attendance session"""
    if session.get('user_type') != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    print(f"DEBUG: start_session received data: {data}") # DEBUG LOG
    class_name = data.get('class_name')
    subject_id = data.get('subject_id')
    duration = data.get('duration', 10)
    
    if not all([class_name, subject_id]):
        print("DEBUG: Missing required fields for start_session") # DEBUG LOG
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    # Check if there's already an active session
    existing = AttendanceSession.query.filter_by(
        faculty_id=current_user.faculty_id,
        status='Active'
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'An active session already exists'})
    
    # Create new session
    new_session = AttendanceSession(
        faculty_id=current_user.faculty_id,
        subject_id=subject_id,
        class_name=class_name,
        duration_minutes=duration,
        status='Active'
    )
    
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session_id': new_session.id,
        'message': 'Session started successfully'
    })

@app.route('/api/end_session', methods=['POST'])
@login_required
def end_session():
    """End the current attendance session and mark absentees"""
    if session.get('user_type') != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'message': 'Session ID required'})
    
    attendance_session = AttendanceSession.query.filter_by(
        id=session_id,
        faculty_id=current_user.faculty_id
    ).first()
    
    if not attendance_session:
        return jsonify({'success': False, 'message': 'Session not found'})
    
    if attendance_session.status == 'Ended':
        return jsonify({'success': False, 'message': 'Session already ended'})
    
    # Mark session as ended
    attendance_session.status = 'Ended'
    attendance_session.end_time = datetime.now()
    
    # Get all students in the class
    students = Student.query.filter_by(class_name=attendance_session.class_name).all()
    
    # Get students already marked present
    marked_student_ids = {r.student_id for r in AttendanceRecord.query.filter_by(
        date=attendance_session.start_time.date(),
        subject_id=attendance_session.subject_id,
        status='Present'
    ).all()}
    
    # Mark absent students
    absent_count = 0
    for student in students:
        if student.student_id not in marked_student_ids:
            # Check if already marked absent
            existing = AttendanceRecord.query.filter_by(
                student_id=student.student_id,
                date=attendance_session.start_time.date(),
                subject_id=attendance_session.subject_id
            ).first()
            
            if not existing:
                absent_record = AttendanceRecord(
                    date=attendance_session.start_time.date(),
                    time=datetime.now().time(),
                    status='Absent',
                    method='Auto',
                    student_id=student.student_id,
                    faculty_id=current_user.faculty_id,
                    subject_id=attendance_session.subject_id,
                    session_id=attendance_session.id
                )
                db.session.add(absent_record)
                absent_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Session ended. {absent_count} students marked as absent.'
    })

@app.route('/api/reopen_session', methods=['POST'])
@login_required
def reopen_session():
    """Reopen an ended session for late marking"""
    if session.get('user_type') != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'message': 'Session ID required'})
    
    attendance_session = AttendanceSession.query.filter_by(
        id=session_id,
        faculty_id=current_user.faculty_id
    ).first()
    
    if not attendance_session:
        return jsonify({'success': False, 'message': 'Session not found'})
    
    if attendance_session.status != 'Ended':
        return jsonify({'success': False, 'message': 'Only ended sessions can be reopened'})
    
    # Reopen the session
    attendance_session.status = 'Reopened'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Session reopened. Late arrivals will be marked as Late.'
    })

@app.route('/manual_attendance', methods=['GET', 'POST'])
@login_required
def manual_attendance():
    if session.get('user_type') != 'faculty':
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        status = request.form.get('status', 'Present')
        
        if student_id and subject_id:
            # Check if exists
            existing = AttendanceRecord.query.filter_by(
                student_id=student_id,
                date=date.today(),
                subject_id=subject_id
            ).first()
            
            if not existing:
                record = AttendanceRecord(
                    date=date.today(),
                    time=datetime.now().time(),
                    status=status,
                    method='Manual',
                    student_id=student_id,
                    faculty_id=current_user.faculty_id,
                    subject_id=subject_id
                )
                db.session.add(record)
                db.session.commit()
                flash('Attendance marked manually', 'success')
            else:
                flash('Attendance already exists', 'warning')
                
        return redirect(url_for('manual_attendance', class_name=request.form.get('class_name')))

    # GET request mainly for UI population
    class_name = request.args.get('class_name')
    students = []
    if class_name:
        students = Student.query.filter_by(class_name=class_name).all()
        
    return render_template('manual_attendance.html', students=students, class_name=class_name)

# --- REPORTS ---
@app.route('/reports')
@login_required
def reports():
    user_type = session.get('user_type', 'faculty')
    return render_template('reports.html', user_type=user_type)

@app.route('/api/get_attendance')
@login_required
def get_attendance():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    class_name = request.args.get('class_name')
    
    # Validate date range
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            if start > end:
                return jsonify({'success': False, 'error': 'Start date must be before end date'})
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format'})
    
    query = db.session.query(
        AttendanceRecord, Student, Subject, Faculty
    ).join(Student).join(Subject).join(Faculty)
    
    if start_date:
        query = query.filter(AttendanceRecord.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(AttendanceRecord.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if class_name:
        query = query.filter(Student.class_name == class_name)
        
    if session.get('user_type') == 'faculty':
        query = query.filter(AttendanceRecord.faculty_id == current_user.faculty_id)
        
    records = query.all()
    
    result = []
    for r, s, sub, f in records:
        result.append({
            'date': r.date.strftime('%Y-%m-%d'),
            'time': str(r.time),
            'lecture_number': '-', # Not tracked in DB
            'student_name': s.name,
            'enrollment_number': s.enrollment_number,
            'class_name': s.class_name,
            'subject': sub.name,
            'status': r.status,
            'method': r.method,
            'faculty_name': f.name
        })
        
    return jsonify({'success': True, 'data': result})

@app.route('/api/export_attendance')
@login_required
def export_attendance():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    class_name = request.args.get('class_name')
    fmt = request.args.get('format', 'csv')
    
    query = db.session.query(
        AttendanceRecord, Student, Subject, Faculty
    ).join(Student).join(Subject).join(Faculty)
    
    if start_date:
        query = query.filter(AttendanceRecord.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(AttendanceRecord.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if class_name:
        query = query.filter(Student.class_name == class_name)
        
    if session.get('user_type') == 'faculty':
        query = query.filter(AttendanceRecord.faculty_id == current_user.faculty_id)
        
    records = query.all()
    
    data = []
    for r, s, sub, f in records:
        data.append({
            'Date': r.date.strftime('%Y-%m-%d'),
            'Time': str(r.time),
            'Student Name': s.name,
            'Enrollment': s.enrollment_number,
            'Class': s.class_name,
            'Subject': sub.name,
            'Status': r.status,
            'Method': r.method,
            'Faculty': f.name
        })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    if fmt == 'excel':
        df.to_excel(output, index=False, engine='openpyxl')
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f'attendance_report_{date.today()}.xlsx'
    else:
        df.to_csv(output, index=False)
        mimetype = 'text/csv'
        filename = f'attendance_report_{date.today()}.csv'
        
    output.seek(0)
    
    return send_file(
        output,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        
        if not check_password_hash(current_user.password, current_pw):
            flash('Incorrect current password', 'error')
            return redirect(url_for('change_password'))
            
        current_user.password = generate_password_hash(new_pw)
        db.session.commit()
        flash('Password updated successfully', 'success')
        
        if session.get('user_type') == 'student':
            return redirect(url_for('student_dashboard'))
        return redirect(url_for('dashboard'))
        
    return render_template('change_password.html')

@app.route('/defaulters')
@login_required
def defaulters():
    students = Student.query.all()
    defaulter_list = []
    
    for student in students:
        # Calculate Percentage
        total_records = AttendanceRecord.query.filter_by(student_id=student.student_id).count()
        # Simplified: Assuming 1 total 'possible' class per day since admission (Demo logic)
        # In real app: Count unique (Subject, Date) from Timetable
        possible_classes = max(1, (date.today() - student.admission_date).days + 1)
        
        # Or simpler for demo: Just use Records as "Attended" and total as fixed number or relative
        # Let's use: (Present / Total records entries) if records exist, else 0
        # If no records, technically 0%
        
        attended = AttendanceRecord.query.filter_by(student_id=student.student_id, status='Present').count()
        
        # For a better demo metric:
        # Let's assume total classes = total subjects * records today? No.
        # Let's just use: Percentage = (Attended / Valid Records) * 100
        # If a student has 5 records and was present in 3, that's 60%
        
        total_marked = total_records
        if total_marked == 0:
            percentage = 0
        else:
            percentage = (attended / total_marked) * 100
            
        if percentage < 75:
            defaulter_list.append({
                'name': student.name,
                'enrollment': student.enrollment_number,
                'class': student.class_name,
                'attended': attended,
                'total': total_marked,
                'percentage': round(percentage, 1)
            })
            
    return render_template('defaulters.html', defaulters=defaulter_list)

# --- LEAVE MANAGEMENT ---
@app.route('/apply_leave', methods=['GET', 'POST'])
@login_required
def apply_leave():
    if session.get('user_type') != 'student':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        leave_date_str = request.form.get('leave_date')
        reason = request.form.get('reason')
        
        if not all([subject_id, leave_date_str, reason]):
            flash('All fields are required', 'error')
            return redirect(url_for('apply_leave'))
        
        try:
            leave_date = datetime.strptime(leave_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('apply_leave'))
        
        # Check if leave already applied for this date and subject
        existing = LeaveApplication.query.filter_by(
            student_id=current_user.student_id,
            subject_id=subject_id,
            leave_date=leave_date
        ).first()
        
        if existing:
            flash('You have already applied for leave on this date for this subject', 'warning')
            return redirect(url_for('apply_leave'))
        
        leave = LeaveApplication(
            student_id=current_user.student_id,
            subject_id=subject_id,
            leave_date=leave_date,
            reason=reason,
            status='Pending'
        )
        
        db.session.add(leave)
        db.session.commit()
        
        flash('Leave application submitted successfully', 'success')
        return redirect(url_for('my_leaves'))
    
    # GET request - show form
    subjects = Subject.query.filter_by(class_name=current_user.class_name).all()
    return render_template('apply_leave.html', subjects=subjects)

@app.route('/my_leaves')
@login_required
def my_leaves():
    if session.get('user_type') != 'student':
        return redirect(url_for('dashboard'))
    
    leaves = LeaveApplication.query.filter_by(student_id=current_user.student_id).order_by(LeaveApplication.applied_on.desc()).all()
    return render_template('my_leaves.html', leaves=leaves)

@app.route('/pending_leaves')
@login_required
def pending_leaves():
    user_type = session.get('user_type')
    if user_type not in ['admin', 'faculty']:
        return redirect(url_for('dashboard'))
    
    # Get pending leaves
    query = LeaveApplication.query.filter_by(status='Pending')
    
    # If faculty, only show leaves for subjects they teach
    if user_type == 'faculty':
        # Get subjects taught by this faculty
        faculty_subjects = Subject.query.join(Timetable).filter(
            Timetable.faculty_id == current_user.faculty_id
        ).all()
        subject_ids = [s.subject_id for s in faculty_subjects]
        if subject_ids:
            query = query.filter(LeaveApplication.subject_id.in_(subject_ids))
        else:
            query = query.filter(False)  # No subjects, so no leaves
    
    leaves = query.order_by(LeaveApplication.applied_on.desc()).all()
    return render_template('pending_leaves.html', leaves=leaves)

@app.route('/leave_history')
@login_required
def leave_history():
    user_type = session.get('user_type')
    if user_type not in ['admin', 'faculty']:
        return redirect(url_for('dashboard'))
    
    # Get all processed leaves (approved/rejected)
    query = LeaveApplication.query.filter(LeaveApplication.status.in_(['Approved', 'Rejected']))
    
    # If faculty, only show leaves for subjects they teach
    if user_type == 'faculty':
        faculty_subjects = Subject.query.join(Timetable).filter(
            Timetable.faculty_id == current_user.faculty_id
        ).all()
        subject_ids = [s.subject_id for s in faculty_subjects]
        if subject_ids:
            query = query.filter(LeaveApplication.subject_id.in_(subject_ids))
        else:
            query = query.filter(False)
    
    leaves = query.order_by(LeaveApplication.approval_date.desc()).all()
    return render_template('leave_history.html', leaves=leaves)

@app.route('/approve_leave/<int:leave_id>', methods=['POST'])
@login_required
def approve_leave(leave_id):
    user_type = session.get('user_type')
    if user_type not in ['admin', 'faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    leave = LeaveApplication.query.get_or_404(leave_id)
    
    # Check if faculty can approve (must teach the subject)
    if user_type == 'faculty':
        faculty_subjects = Subject.query.join(Timetable).filter(
            Timetable.faculty_id == current_user.faculty_id
        ).all()
        subject_ids = [s.subject_id for s in faculty_subjects]
        if leave.subject_id not in subject_ids:
            return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if leave.status != 'Pending':
        return jsonify({'success': False, 'message': 'Leave already processed'})
    
    
    leave.status = 'Approved'
    if user_type == 'faculty':
        leave.approved_by = current_user.faculty_id
    else:
        leave.approved_by = None  # Admin approval
    leave.approval_date = datetime.now()
    leave.remarks = request.form.get('remarks', '')
    
    # Check if attendance record already exists for this leave
    existing_record = AttendanceRecord.query.filter_by(
        student_id=leave.student_id,
        date=leave.leave_date,
        subject_id=leave.subject_id
    ).first()
    
    if not existing_record:
        # Get faculty_id properly based on user type
        if session.get('user_type') == 'faculty':
            faculty_id_for_record = current_user.faculty_id
        else:
            # Admin approval - find faculty teaching this subject from timetable
            timetable_entry = Timetable.query.filter_by(subject_id=leave.subject_id).first()
            faculty_id_for_record = timetable_entry.faculty_id if timetable_entry else None
            
            if faculty_id_for_record is None:
                # Fallback: use first available faculty
                first_faculty = Faculty.query.first()
                faculty_id_for_record = first_faculty.faculty_id if first_faculty else None
        
        if faculty_id_for_record:
            attendance_record = AttendanceRecord(
                date=leave.leave_date,
                time=datetime.now().time(),
                status='Leave',
                method='Leave',
                student_id=leave.student_id,
                faculty_id=faculty_id_for_record,
                subject_id=leave.subject_id
            )
            db.session.add(attendance_record)

    
    db.session.commit()
    
    flash('Leave approved successfully', 'success')
    return redirect(url_for('pending_leaves'))

@app.route('/reject_leave/<int:leave_id>', methods=['POST'])
@login_required
def reject_leave(leave_id):
    user_type = session.get('user_type')
    if user_type not in ['admin', 'faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    leave = LeaveApplication.query.get_or_404(leave_id)
    
    # Check if faculty can reject (must teach the subject)
    if user_type == 'faculty':
        faculty_subjects = Subject.query.join(Timetable).filter(
            Timetable.faculty_id == current_user.faculty_id
        ).all()
        subject_ids = [s.subject_id for s in faculty_subjects]
        if leave.subject_id not in subject_ids:
            return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if leave.status != 'Pending':
        return jsonify({'success': False, 'message': 'Leave already processed'})
    
    leave.status = 'Rejected'
    if user_type == 'faculty':
        leave.approved_by = current_user.faculty_id
    else:
        leave.approved_by = None  # Admin rejection
    leave.approval_date = datetime.now()
    leave.remarks = request.form.get('remarks', '')
    
    db.session.commit()
    
    flash('Leave rejected', 'info')
    return redirect(url_for('pending_leaves'))

# --- TIMETABLE MANAGEMENT ---
@app.route('/timetable', methods=['GET'])
@login_required
def timetable():
    user_type = session.get('user_type')
    
    # GET request
    if user_type == 'admin':
        slots = Timetable.query.order_by(Timetable.day_of_week, Timetable.start_time).all()
        subjects = Subject.query.all()
        faculty_list = Faculty.query.all()
    elif user_type == 'faculty':
        slots = Timetable.query.filter_by(faculty_id=current_user.faculty_id).order_by(Timetable.day_of_week, Timetable.start_time).all()
        subjects = Subject.query.all()
        faculty_list = [current_user]
    elif user_type == 'student':
        slots = Timetable.query.filter_by(class_name=current_user.class_name).order_by(Timetable.day_of_week, Timetable.start_time).all()
        subjects = Subject.query.filter_by(class_name=current_user.class_name).all()
        faculty_list = Faculty.query.all()
    else:
        slots = []
        subjects = []
        faculty_list = []
    
    return render_template('timetable.html', slots=slots, subjects=subjects, faculty_list=faculty_list, user_type=user_type)

@app.route('/add_timetable_slot', methods=['POST'])
@login_required
def add_timetable_slot():
    user_type = session.get('user_type')
    
    if user_type != 'admin':
        flash('Only admin can manage timetable', 'error')
        return redirect(url_for('timetable'))
    
    class_name = request.form.get('class_name')
    semester = int(request.form.get('semester', 1))
    subject_id = int(request.form.get('subject_id'))
    faculty_id = int(request.form.get('faculty_id'))
    day_of_week = int(request.form.get('day_of_week'))
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    room_number = request.form.get('room_number', '')
    
    try:
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except ValueError:
        flash('Invalid time format', 'error')
        return redirect(url_for('timetable'))
    
    
    # Check for conflicts
    conflicts = Timetable.query.filter_by(
        day_of_week=int(day_of_week)
    ).filter(
        or_(
            and_(
                Timetable.faculty_id == int(faculty_id),
                or_(
                    and_(Timetable.start_time <= start_time, Timetable.end_time > start_time),
                    and_(Timetable.start_time < end_time, Timetable.end_time >= end_time),
                    and_(Timetable.start_time >= start_time, Timetable.end_time <= end_time)
                )
            ),
            and_(
                Timetable.room_number == room_number,
                room_number != '',
                or_(
                    and_(Timetable.start_time <= start_time, Timetable.end_time > start_time),
                    and_(Timetable.start_time < end_time, Timetable.end_time >= end_time),
                    and_(Timetable.start_time >= start_time, Timetable.end_time <= end_time)
                )
            )
        )
    ).first()
    
    if conflicts:
        flash('Conflict detected: Faculty or room is already booked at this time', 'error')
        return redirect(url_for('timetable'))
    
    # Create slot

    slot = Timetable(
        class_name=class_name,
        semester=semester,
        subject_id=subject_id,
        faculty_id=faculty_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room_number=room_number
    )
    
    db.session.add(slot)
    db.session.commit()
    
    flash('Timetable slot added successfully', 'success')
    return redirect(url_for('timetable'))

@app.route('/delete_timetable_slot/<int:slot_id>', methods=['POST'])
@login_required
def delete_timetable_slot(slot_id):
    if session.get('user_type') != 'admin':
        flash('Only admin can delete timetable slots', 'error')
        return redirect(url_for('timetable'))
    
    slot = Timetable.query.get_or_404(slot_id)
    db.session.delete(slot)
    db.session.commit()
    
    flash('Timetable slot deleted', 'success')
    return redirect(url_for('timetable'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # SSL Context for HTTPS
    import os
    ssl_context = None
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        ssl_context = ('cert.pem', 'key.pem')
        print(" * Running with HTTPS (SSL)")
    else:
        print(" * Running with HTTP (No SSL)")
    
    print("DEBUG: app.py loaded. Checking for start_session route...")
    if 'start_session' in app.view_functions:
        print("DEBUG: start_session route FOUND!")
    else:
        print("DEBUG: start_session route NOT found!")

    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=ssl_context)
