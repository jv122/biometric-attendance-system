from app import app, db
from models import Admin, Faculty, Subject
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def init_db():
    # Remove existing database to ensure clean state with new schema
    db_path = os.path.join('database', 'attendance.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    with app.app_context():
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
            print("Created Admin: admin@college.edu")
            
        # Create default Faculty
        if not Faculty.query.first():
            faculty = Faculty(
                name='Dr. Smith',
                email='faculty@college.edu',
                password=generate_password_hash('faculty123'),
                contact_no=9876543210
            )
            db.session.add(faculty)
            print("Created Faculty: faculty@college.edu")
            
        # Create Default Subjects
        subjects = [
            Subject(name='Mathematics-I', class_name='FY'),
            Subject(name='Physics-I', class_name='FY'),
            Subject(name='Computer Science-I', class_name='FY'),
            Subject(name='Data Structures', class_name='SY'),
            Subject(name='Algorithms', class_name='SY'),
            Subject(name='Operating Systems', class_name='TY'),
            Subject(name='AI & ML', class_name='TY'),
        ]
        
        for sub in subjects:
            existing = Subject.query.filter_by(name=sub.name, class_name=sub.class_name).first()
            if not existing:
                db.session.add(sub)
        
        db.session.commit()
        print("Initialized database with new schema, hashed passwords, and subjects.")

if __name__ == '__main__':
    init_db()
