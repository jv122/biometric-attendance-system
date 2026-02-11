import sys
import os

# Add your project directory to the sys.path
# REPLACE 'YOUR_USERNAME' with your actual PythonAnywhere username
project_home = '/home/YOUR_USERNAME/biometric-attendance'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['SECRET_KEY'] = 'a5632997eb3e063dfebf7947b3a60cd9a21ab04f7c2bd463e63f089afab214b6'

# Optional: Set database path (if needed)
# os.environ['DATABASE_URL'] = 'sqlite:////home/YOUR_USERNAME/biometric-attendance/database/attendance.db'

# Import Flask app
# PythonAnywhere expects the variable to be named 'application'
from app import app as application

# Optional: Enable debug mode (disable in production)
# application.debug = False
