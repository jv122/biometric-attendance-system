from app import app, db
from models import AttendanceRecord, AttendanceSession

def reset_attendance():
    """
    Clears all attendance records and sessions from the database.
    Keeps Users (Admin, Faculty, Student) and Subjects intact.
    """
    with app.app_context():
        try:
            num_records = db.session.query(AttendanceRecord).delete()
            num_sessions = db.session.query(AttendanceSession).delete()
            db.session.commit()
            print(f"Successfully deleted {num_records} attendance records.")
            print(f"Successfully deleted {num_sessions} attendance sessions.")
        except Exception as e:
            db.session.rollback()
            print(f"Error resetting attendance: {e}")

if __name__ == "__main__":
    print("WARNING: This will delete ALL attendance history.")
    confirm = input("Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        reset_attendance()
    else:
        print("Operation cancelled.")
