from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    
    a_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Increased length for hash
    contact_no = db.Column(db.BigInteger, unique=True, nullable=False)
    
    def get_id(self):
        return f'admin_{self.a_id}'
    
    def __repr__(self):
        return f'<Admin {self.name}>'

class Faculty(UserMixin, db.Model):
    __tablename__ = 'faculty'
    
    faculty_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Increased length for hash
    contact_no = db.Column(db.BigInteger, unique=True, nullable=False)
    
    def get_id(self):
        return f'faculty_{self.faculty_id}'
        
    def __repr__(self):
        return f'<Faculty {self.name}>'

class Student(UserMixin, db.Model):
    __tablename__ = 'student'
    
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    enrollment_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False, default='scrypt:32768:8:1$default$default') # Default hash for migration safety
    class_name = db.Column(db.String(10), nullable=False)  # FY/SY/TY
    semester = db.Column(db.Integer, nullable=False, default=1) # 1-6
    face_encoding = db.Column(db.Text, nullable=False)  # JSON string
    photo_url = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    admission_date = db.Column(db.Date, default=datetime.utcnow)
    
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True)
    
    def get_id(self):
        return f'student_{self.student_id}'
    
    def __repr__(self):
        return f'<Student {self.name}>'

class Subject(db.Model):
    __tablename__ = 'subject'
    
    subject_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(10), nullable=False) # FY/SY/TY
    semester = db.Column(db.Integer, nullable=False, default=1) # 1-6
    
    attendance_records = db.relationship('AttendanceRecord', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.name} ({self.class_name})>'

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_session'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    class_name = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, default=10)
    status = db.Column(db.String(20), default='Active') # Active, Ended, Reopened
    
    records = db.relationship('AttendanceRecord', backref='session', lazy=True)

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_record'
    
    record_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present/Absent/Late/Leave
    method = db.Column(db.String(20), default='FaceID') # FaceID / Manual / Leave
    
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'date', name='unique_attendance_per_day'),
    )
    
    def __repr__(self):
        return f'<AttendanceRecord {self.record_id}>'

class LeaveApplication(db.Model):
    __tablename__ = 'leave_application'
    
    leave_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    leave_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending/Approved/Rejected
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id'), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    
    # Relationships
    student = db.relationship('Student', backref='leave_applications', foreign_keys=[student_id])
    subject = db.relationship('Subject', backref='leave_applications', foreign_keys=[subject_id])
    approver = db.relationship('Faculty', backref='approved_leaves', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<LeaveApplication {self.leave_id} - {self.status}>'

class Timetable(db.Model):
    __tablename__ = 'timetable'
    
    timetable_id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room_number = db.Column(db.String(20), nullable=True)
    
    # Relationships
    subject = db.relationship('Subject', backref='timetable_slots', foreign_keys=[subject_id])
    faculty = db.relationship('Faculty', backref='timetable_slots', foreign_keys=[faculty_id])
    
    def __repr__(self):
        return f'<Timetable {self.timetable_id} - {self.class_name}>'
