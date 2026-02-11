#!/usr/bin/env python
"""Simple script to start the Flask server"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Check face_recognition availability before starting
    from face_recognition_api import FACE_RECOGNITION_AVAILABLE
    print("Checking face_recognition library...")
    print(f"FACE_RECOGNITION_AVAILABLE: {FACE_RECOGNITION_AVAILABLE}")
    if not FACE_RECOGNITION_AVAILABLE:
        print("WARNING: face_recognition is not available!")
    else:
        print("[OK] face_recognition library is ready")
    print()
    
    from app import app
    print("=" * 50)
    print("Starting Biometric Attendance System Server")
    print("=" * 50)
    print("Server will be available at: http://127.0.0.1:5001")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5001, use_reloader=False)
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
