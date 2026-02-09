from app import app, db
from sqlalchemy import text

def add_constraint():
    with app.app_context():
        # SQLite doesn't support adding constraints to existing tables easily without recreating.
        # However, since we want to be safe, we can try to rely on the application level check 
        # for existing data, but for new tables it will apply.
        # For a proper migration in SQLite, we'd need to recreate the table.
        # Given the user environment, let's just print a message that they might need to reset DB 
        # if they want strict DB-level enforcement on existing data.
        print("Model updated. To enforce strict DB constraints on EXISTING tables in SQLite, you typically need to recreate the database or use Alembic migrations.")
        print("For now, the application-level logic provided in the fix will handle duplicates.")
        
        # If the user wants to start fresh:
        # db.drop_all()
        # db.create_all()
        # print("Database recreated.")

if __name__ == '__main__':
    add_constraint()
