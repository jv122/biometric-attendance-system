"""Detailed database connection test"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("DATABASE CONNECTION TEST")
print("=" * 60)

# Check environment variables
db_type = os.getenv('DATABASE_TYPE', 'sqlite')
db_url = os.getenv('DATABASE_URL', 'Not set')

print(f"\n1. Environment Variables:")
print(f"   DATABASE_TYPE: {db_type}")
print(f"   DATABASE_URL: {db_url[:80]}..." if len(db_url) > 80 else f"   DATABASE_URL: {db_url}")

# Test config module
print(f"\n2. Testing config.py...")
try:
    from config import DATABASE_URI, DATABASE_TYPE
    print(f"   ✓ Config loaded successfully")
    print(f"   DATABASE_TYPE: {DATABASE_TYPE}")
    print(f"   DATABASE_URI: {DATABASE_URI[:80]}..." if len(DATABASE_URI) > 80 else f"   DATABASE_URI: {DATABASE_URI}")
except Exception as e:
    print(f"   ✗ Error loading config: {e}")
    exit(1)

# Test SQLAlchemy connection
print(f"\n3. Testing SQLAlchemy connection...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(DATABASE_URI)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"   ✓ Connection successful!")
        print(f"   PostgreSQL version: {version[:50]}...")
        
except Exception as e:
    print(f"   ✗ Connection failed!")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {str(e)}")
    print(f"\n   Full traceback:")
    import traceback
    traceback.print_exc()
    exit(1)

# Test Flask app
print(f"\n4. Testing Flask app initialization...")
try:
    from app import app, db
    with app.app_context():
        print(f"   ✓ Flask app loaded successfully")
        print(f"   Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:80]}...")
except Exception as e:
    print(f"   ✗ Error loading Flask app: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
