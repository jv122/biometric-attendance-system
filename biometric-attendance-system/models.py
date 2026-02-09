from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

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
    status = db.Column(db.String(20), nullable=False)  # Present/Absent/Late
    method = db.Column(db.String(20), default='FaceID') # FaceID / Manual
    
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'date', name='unique_attendance_per_day'),
    )
    
    def __repr__(self):
        return f'<AttendanceRecord {self.record_id}>'
