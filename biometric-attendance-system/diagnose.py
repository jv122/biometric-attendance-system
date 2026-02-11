"""Detailed error diagnosis"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=== Database Connection Diagnostic ===\n")

try:
    from sqlalchemy import create_engine, text
    from config import DATABASE_URI
    
    print("1. Connection string loaded")
    print("   Format: postgresql://postgres:****@db.xxx.supabase.co:5432/postgres?sslmode=require\n")
    
    print("2. Creating engine...")
    engine = create_engine(DATABASE_URI, echo=False)
    print("   Engine created\n")
    
    print("3. Attempting connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("   SUCCESS!\n")
        
except Exception as e:
    print(f"   FAILED\n")
    print(f"Error Details:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}\n")
    
    # Check for common issues
    error_msg = str(e).lower()
    
    if "password authentication failed" in error_msg:
        print("DIAGNOSIS: Incorrect password")
        print("SOLUTION: Check your Supabase database password")
    elif "could not connect" in error_msg or "connection refused" in error_msg:
        print("DIAGNOSIS: Cannot reach database server")
        print("SOLUTION: Check internet connection and Supabase project status")
    elif "ssl" in error_msg:
        print("DIAGNOSIS: SSL connection issue")
        print("SOLUTION: Ensure sslmode=require is in connection string")
    elif "does not exist" in error_msg:
        print("DIAGNOSIS: Database or user does not exist")
        print("SOLUTION: Verify Supabase project is active")
    else:
        print("DIAGNOSIS: Unknown error")
        print("Full error:")
        import traceback
        traceback.print_exc()
    
    sys.exit(1)

print("=== All Tests Passed ===")
