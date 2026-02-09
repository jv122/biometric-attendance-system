from app import app, db, AttendanceRecord
from sqlalchemy import text

with app.app_context():
    # 1. Check for duplicates
    print("Checking for duplicate records (same student, subject, date)...")
    sql = text("""
        SELECT student_id, subject_id, date, COUNT(*) as count
        FROM attendance_record
        GROUP BY student_id, subject_id, date
        HAVING count > 1
    """)
    duplicates = db.session.execute(sql).fetchall()
    
    if duplicates:
        print(f"FOUND {len(duplicates)} sets of duplicate records!")
        for d in duplicates:
            print(f" - Student {d.student_id}, Subject {d.subject_id}, Date {d.date}: {d.count} records")
    else:
        print("No duplicate records found.")

    # 2. Check for unique index in SQLite
    print("\nChecking SQLite indices...")
    indices = db.session.execute(text("PRAGMA index_list('attendance_record')")).fetchall()
    for idx in indices:
        print(f"Index: {idx.name}, Unique: {idx.unique}")
        # Get info
        cols = db.session.execute(text(f"PRAGMA index_info('{idx.name}')")).fetchall()
        print(f"  Columns: {[c.name for c in cols]}")

    # 3. Check table info
    print("\nTable Info:")
    columns = db.session.execute(text("PRAGMA table_info('attendance_record')")).fetchall()
    for c in columns:
        print(c)
