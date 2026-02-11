"""
Reset Today's Attendance Script
This script resets all attendance records for today.
Make sure the server is running before executing this script.
"""

import requests
import json
from getpass import getpass

# Server URL - update if needed
SERVER_URL = "http://localhost:5000"  # or https://localhost:5000 if using SSL

def reset_today_attendance():
    """Reset today's attendance by calling the API endpoint"""
    
    print("=" * 50)
    print("Reset Today's Attendance")
    print("=" * 50)
    
    # Get credentials
    email = input("Enter your email/enrollment: ")
    password = getpass("Enter your password: ")
    user_type = input("Enter user type (admin/faculty): ").lower()
    
    # Create a session
    session = requests.Session()
    
    try:
        # Step 1: Login
        print("\n[1/3] Logging in...")
        login_response = session.post(
            f"{SERVER_URL}/login",
            data={
                'email': email,
                'password': password,
                'user_type': user_type
            },
            allow_redirects=False
        )
        
        if login_response.status_code not in [200, 302]:
            print("❌ Login failed! Check your credentials.")
            return
        
        print("✓ Login successful")
        
        # Step 2: Get CSRF token
        print("\n[2/3] Getting CSRF token...")
        dashboard_response = session.get(f"{SERVER_URL}/dashboard")
        
        # Extract CSRF token from cookies or session
        csrf_token = None
        for cookie in session.cookies:
            if 'csrf' in cookie.name.lower():
                csrf_token = cookie.value
                break
        
        # If not in cookies, try to get from dashboard HTML
        if not csrf_token and 'csrf_token' in dashboard_response.text:
            import re
            match = re.search(r'csrf_token.*?value="([^"]+)"', dashboard_response.text)
            if match:
                csrf_token = match.group(1)
        
        if not csrf_token:
            # Try getting it from meta tag
            import re
            match = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', dashboard_response.text)
            if match:
                csrf_token = match.group(1)
        
        print(f"✓ CSRF token obtained")
        
        # Step 3: Reset attendance
        print("\n[3/3] Resetting today's attendance...")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if csrf_token:
            headers['X-CSRFToken'] = csrf_token
        
        reset_response = session.post(
            f"{SERVER_URL}/api/reset_today_attendance",
            headers=headers,
            json={}
        )
        
        result = reset_response.json()
        
        if result.get('success'):
            print(f"\n✅ {result.get('message')}")
        else:
            print(f"\n❌ Error: {result.get('message')}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to server at {SERVER_URL}")
        print("Make sure the server is running!")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    reset_today_attendance()
