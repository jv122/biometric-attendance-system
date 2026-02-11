"""Simple database connection test"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("Testing database connection...")
print("DATABASE_TYPE:", os.getenv('DATABASE_TYPE'))

try:
    from sqlalchemy import create_engine, text
    from config import DATABASE_URI
    
    # Mask password in output
    uri_parts = DATABASE_URI.split('@')
    if len(uri_parts) > 1:
        masked_uri = uri_parts[0].split(':')[0] + ':****@' + uri_parts[1]
    else:
        masked_uri = DATABASE_URI
    
    print("Connecting to:", masked_uri)
    
    engine = create_engine(DATABASE_URI)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("SUCCESS: Connected to PostgreSQL!")
        
except Exception as e:
    print("ERROR:", str(e))
    sys.exit(1)
