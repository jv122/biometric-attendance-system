"""
Database Configuration Module
Handles database connection for both SQLite and PostgreSQL
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database type from environment (default to sqlite for backward compatibility)
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite').lower()

def get_database_uri():
    """
    Returns the appropriate database URI based on DATABASE_TYPE
    """
    if DATABASE_TYPE == 'postgresql':
        # Try to get full DATABASE_URL first (common in cloud deployments)
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Supabase and some services use postgres:// but SQLAlchemy needs postgresql://
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url
        
        # Otherwise, build from individual components
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'attendance_db')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        return f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    else:
        # Default to SQLite
        db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'database', 
            'attendance.db'
        )
        return f'sqlite:///{db_path}'

# Export the database URI
DATABASE_URI = get_database_uri()

# Print configuration on import (helpful for debugging)
if __name__ != '__main__':
    print(f"Database Configuration: Using {DATABASE_TYPE.upper()}")
