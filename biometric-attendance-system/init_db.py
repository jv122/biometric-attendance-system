from app import app, db
from models import Admin, Faculty, Subject
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def init_db():
    with app.app_context():
        # Drop all tables and recreate (works for both SQLite and PostgreSQL)
        print("Dropping existing tables...")
        db.drop_all()
        print("Creating tables...")
        db.create_all()
        
        # Create default Admin
        if not Admin.query.first():
            admin = Admin(
                name='System Admin',
                email='admin@college.edu',
                password=generate_password_hash('admin123'),
                contact_no=1234567890
            )
            db.session.add(admin)
            print("Created Admin: admin@college.edu / admin123")
            
        # Create default Faculty
        if not Faculty.query.first():
            faculty = Faculty(
                name='Dr. Smith',
                email='faculty@college.edu',
                password=generate_password_hash('faculty123'),
                contact_no=9876543210
            )
            db.session.add(faculty)
            print("Created Faculty: faculty@college.edu / faculty123")
            
        # Create Default Subjects with semesters
        subjects = [
            Subject(name='Mathematics-I', class_name='FY', semester=1),
            Subject(name='Physics-I', class_name='FY', semester=1),
            Subject(name='Computer Science-I', class_name='FY', semester=2),
            Subject(name='Data Structures', class_name='SY', semester=3),
            Subject(name='Algorithms', class_name='SY', semester=4),
            Subject(name='Operating Systems', class_name='TY', semester=5),
            Subject(name='AI & ML', class_name='TY', semester=6),
        ]
        
        for sub in subjects:
            existing = Subject.query.filter_by(name=sub.name, class_name=sub.class_name, semester=sub.semester).first()
            if not existing:
                db.session.add(sub)
        
        db.session.commit()
        print("Initialized database with new schema, hashed passwords, and subjects.")

if __name__ == '__main__':
    init_db()
