import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'attendance.db')

def migrate_db():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Reset Today's Attendance (User Request)
        today = date.today().isoformat()
        print(f"Resetting attendance for today ({today})...")
        cursor.execute("DELETE FROM attendance_record WHERE date = ?", (today,))
        print(f"Deleted {cursor.rowcount} records for today.")

        # 2. Deduplicate Remaining Historic Data
        print("Removing historic duplicates...")
        # Keep the record with the lowest record_id for each (student, subject, date) group
        cursor.execute("""
            DELETE FROM attendance_record 
            WHERE record_id NOT IN (
                SELECT MIN(record_id) 
                FROM attendance_record 
                GROUP BY student_id, subject_id, date
            )
        """)
        print(f"Deleted {cursor.rowcount} duplicate historic records.")

        # 3. Apply Unique Constraint (Schema Migration)
        print("Applying Unique Constraint...")
        
        # Renaissance Strategy: Rename -> Create New -> Copy -> Drop Old
        cursor.execute("ALTER TABLE attendance_record RENAME TO attendance_record_old")
        
        # Create new table with CONSTRAINT
        cursor.execute("""
            CREATE TABLE attendance_record (
                record_id INTEGER PRIMARY KEY,
                date DATE NOT NULL,
                time TIME NOT NULL,
                status VARCHAR(20) NOT NULL,
                method VARCHAR(20),
                student_id INTEGER NOT NULL,
                faculty_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                FOREIGN KEY(student_id) REFERENCES student(student_id),
                FOREIGN KEY(faculty_id) REFERENCES faculty(faculty_id),
                FOREIGN KEY(subject_id) REFERENCES subject(subject_id),
                CONSTRAINT unique_attendance_per_day UNIQUE (student_id, subject_id, date)
            )
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO attendance_record (record_id, date, time, status, method, student_id, faculty_id, subject_id)
            SELECT record_id, date, time, status, method, student_id, faculty_id, subject_id
            FROM attendance_record_old
        """)
        
        # Drop old
        cursor.execute("DROP TABLE attendance_record_old")
        
        conn.commit()
        print("Database fixed and optimized successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_db()
