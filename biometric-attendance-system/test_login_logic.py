from app import app
from models import db, Admin, Faculty, Student
from werkzeug.security import check_password_hash
import os

# Force SQLite for this test
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'attendance.db')
print(f"Forcing DB to: {app.config['SQLALCHEMY_DATABASE_URI']}")

def test_login_logic():
    with app.app_context():
        print("--- Testing Login Logic ---")
        
        # Test 1: List all users to see what we have
        admins = Admin.query.all()
        faculty = Faculty.query.all()
        students = Student.query.all()
        
        print(f"Admins: {[a.email for a in admins]}")
        print(f"Faculty: {[f.email for f in faculty]}")
        print(f"Students: {[s.enrollment_number for s in students]}")
        
        # Test 2: Simulate Login for a known user
        if admins:
            target_email = admins[0].email
            print(f"\nAttempting login for Admin: {target_email}")
            user = Admin.query.filter_by(email=target_email).first()
            if user:
                print("Found in Admin table.")
            
        if faculty:
            target_email = faculty[0].email
            print(f"\nAttempting login for Faculty: {target_email}")
            user = None
            # Simulate logic
            user = Admin.query.filter_by(email=target_email).first()
            if user:
                print("Found in Admin table (Unexpected if unique!)")
            else:
                user = Faculty.query.filter_by(email=target_email).first()
                if user:
                    print("Found in Faculty table.")
                    
        # Test 3: Check Password (if we knew it, but we can't really guess it here unless default)
        # We'll just verify the hash exists
        if admins:
            print(f"\nAdmin Password Hash exists: {bool(admins[0].password)}")
            # Try default 'admin123'
            print(f"Is password 'admin123'? {check_password_hash(admins[0].password, 'admin123')}")

if __name__ == "__main__":
    test_login_logic()
