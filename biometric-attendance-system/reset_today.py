"""
Simple script to reset today's attendance records directly from the database
"""
import os
import sys
from datetime import date
from sqlalchemy import create_engine, text
from pathlib import Path
from config import DATABASE_URI, DATABASE_TYPE

# Create engine using configured database URI
engine = create_engine(DATABASE_URI)

try:
    with engine.connect() as conn:
        today = date.today()
        
        print("=" * 60)
        print(f"Resetting Attendance for: {today}")
        print("=" * 60)
        
        # Get count before deletion
        result = conn.execute(text("SELECT COUNT(*) FROM attendance_record WHERE date = :today"), {"today": today})
        count_before = result.scalar()
        
        print(f"\nFound {count_before} attendance record(s) for today")
        
        if count_before > 0:
            # Delete attendance records for today
            conn.execute(text("DELETE FROM attendance_record WHERE date = :today"), {"today": today})
            
            # End any active sessions for today
            conn.execute(text("""
                UPDATE attendance_session 
                SET status = 'Ended', end_time = CURRENT_TIMESTAMP 
                WHERE DATE(start_time) = :today 
                AND status IN ('Active', 'Reopened')
            """), {"today": today})
            
            conn.commit()
            
            print(f"[SUCCESS] Deleted {count_before} attendance record(s)")
            print("[SUCCESS] Ended any active sessions for today")
        else:
            print("[INFO] No attendance records found for today")
        
        print("=" * 60)
        
except Exception as e:
    print(f"[ERROR] {str(e)}")
    sys.exit(1)
