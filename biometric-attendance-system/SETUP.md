# Setup Guide

## Quick Start

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   ```bash
   python init_db.py
   ```
   This will create the database with default admin and faculty accounts.

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Application**
   - Open your browser and go to: `http://localhost:5000`
   - Login with default credentials:
     - **Admin**: admin@college.edu / admin123
     - **Faculty**: faculty@college.edu / faculty123

## Adding Students

1. Login as Admin
2. Go to "Add Student" page
3. Fill in student details:
   - Name
   - Enrollment Number
   - Class (FY/SY/TY)
   - Upload a clear front-facing photo
4. Click "Add Student"

The system will automatically encode the face from the uploaded photo.

## Marking Attendance

1. Login as Faculty
2. Go to "Mark Attendance" page
3. Select Class and Lecture Number
4. Click "Start Camera"
5. Allow camera permissions when prompted
6. Students will be automatically recognized and marked present

## Viewing Reports

1. Go to "Reports" page
2. Set date range and class filters (optional)
3. Click "Filter" to view records
4. Click "Export CSV" or "Export Excel" to download reports

## Troubleshooting

### Camera Not Working
- Ensure camera permissions are granted in browser settings
- Try using Chrome or Firefox
- Check if camera is being used by another application

### Face Not Recognized
- Ensure student photo is clear and front-facing
- Good lighting is important
- Student should be looking directly at the camera
- Try re-adding the student with a better photo

### Installation Issues
- Ensure Python 3.8+ is installed
- On Windows, you may need to install Visual C++ Build Tools for face_recognition
- For face_recognition library, you may need dlib which requires CMake

### Database Issues
- Delete `database/attendance.db` and run `init_db.py` again
- Ensure write permissions in the database directory

## System Requirements

- Python 3.8 or higher
- Webcam (HD recommended for better recognition)
- 4GB RAM minimum
- Modern web browser (Chrome, Firefox, Edge)

## Notes

- The system uses SQLite database by default (suitable for development)
- For production, consider using PostgreSQL or MySQL
- Face recognition works best with good lighting and clear photos
- The system prevents duplicate attendance for the same lecture on the same day
