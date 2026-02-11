"""Write error to file"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

with open('error_log.txt', 'w', encoding='utf-8') as f:
    f.write("=== Database Connection Test ===\n\n")
    
    try:
        from sqlalchemy import create_engine, text
        from config import DATABASE_URI
        
        f.write("Creating engine...\n")
        engine = create_engine(DATABASE_URI)
        
        f.write("Connecting...\n")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            f.write("SUCCESS!\n")
            print("SUCCESS! Connection established.")
            
    except Exception as e:
        f.write(f"\nFAILED!\n\n")
        f.write(f"Error Type: {type(e).__name__}\n")
        f.write(f"Error Message: {str(e)}\n\n")
        f.write("Full Traceback:\n")
        
        import traceback
        f.write(traceback.format_exc())
        
        print("FAILED - check error_log.txt for details")
        sys.exit(1)

print("Check error_log.txt for results")
