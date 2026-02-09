# Biometric Attendance System using Face Recognition

A modern web-based solution for automated student attendance tracking using facial recognition technology.

## Features

- **Secure Authentication**: Login system for Admin and Faculty
- **Face Recognition**: Real-time face detection and recognition via webcam
- **Automatic Attendance**: Marks attendance automatically when student face is recognized
- **Report Generation**: Export attendance reports in CSV/Excel format
- **Database Management**: Secure storage of student, faculty, and attendance data

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python (Flask)
- **Face Recognition**: OpenCV, face_recognition library
- **Database**: SQLite (via SQLAlchemy)

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Initialize the database:
```bash
python init_db.py
```

2. Run the Flask server:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Default Credentials

- **Admin**: 
  - Email: admin@college.edu
  - Password: admin123

- **Faculty**: 
  - Email: faculty@college.edu
  - Password: faculty123

## Project Structure

```
.
├── app.py                 # Main Flask application
├── models.py              # Database models
├── init_db.py             # Database initialization script
├── face_recognition_api.py # Face recognition utilities
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   ├── attendance.html
│   └── reports.html
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── uploads/
└── database/              # Database files
    └── attendance.db
```

## Requirements

- Python 3.8+
- Webcam (HD recommended)
- 4GB RAM minimum
- 250MB storage space
