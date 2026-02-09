try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition library not installed. Face recognition features will be disabled.")
    print("To enable face recognition, install dlib and face-recognition:")
    print("  - Install CMake from https://cmake.org/")
    print("  - pip install dlib face-recognition")

import cv2
import numpy as np
import json
import os
from PIL import Image

def encode_face_from_image(image_path):
    """
    Encode a face from an image file.
    Returns the face encoding as a list.
    """
    # Check import at runtime to ensure we have the latest state
    try:
        import face_recognition
    except ImportError:
        raise ImportError("face_recognition library is not installed. Please install dlib and face-recognition.")
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        
        if len(encodings) > 0:
            return encodings[0].tolist()
        else:
            return None
    except Exception as e:
        print(f"Error encoding face: {e}")
        return None

def encode_face_from_array(image_array):
    """
    Encode a face from a numpy array (from webcam).
    Returns the face encoding as a list.
    """
    # Check import at runtime to ensure we have the latest state
    try:
        import face_recognition
    except ImportError:
        raise ImportError("face_recognition library is not installed. Please install dlib and face-recognition.")
    try:
        # Convert BGR to RGB (OpenCV uses BGR, face_recognition uses RGB)
        rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_image)
        
        if len(encodings) > 0:
            return encodings[0].tolist()
        else:
            return None
    except Exception as e:
        print(f"Error encoding face from array: {e}")
    except Exception as e:
        print(f"Error encoding face from array: {e}")
        return None

def get_all_face_encodings(image_array):
    """
    Encode ALL faces from a numpy array (from webcam).
    Returns a list of encodings.
    """
    try:
        import face_recognition
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        # Get locations first (optimization)
        face_locations = face_recognition.face_locations(rgb_image)
        if not face_locations:
            return []
            
        encodings = face_recognition.face_encodings(rgb_image, face_locations)
        return [enc.tolist() for enc in encodings]
    except Exception as e:
        print(f"Error getting all encodings: {e}")
        return []

def compare_faces(known_encoding, unknown_encoding, tolerance=0.6):
    """
    Compare two face encodings.
    Returns True if faces match, False otherwise.
    """
    # Check import at runtime to ensure we have the latest state
    try:
        import face_recognition
    except ImportError:
        raise ImportError("face_recognition library is not installed. Please install dlib and face-recognition.")
    try:
        if known_encoding is None or unknown_encoding is None:
            return False
        
        # Convert lists back to numpy arrays
        known = np.array(known_encoding)
        unknown = np.array(unknown_encoding)
        
        # Calculate face distance
        face_distance = face_recognition.face_distance([known], unknown)[0]
        
        # Check if distance is below tolerance
        return face_distance <= tolerance
    except Exception as e:
        print(f"Error comparing faces: {e}")
        return False

def find_matching_student(unknown_encoding, students):
    """
    Find a matching student from the database.
    Returns student object if match found, None otherwise.
    """
    # Check import at runtime to ensure we have the latest state
    try:
        import face_recognition
    except ImportError:
        raise ImportError("face_recognition library is not installed. Please install dlib and face-recognition.")
    try:
        if unknown_encoding is None:
            return None
        
        best_match = None
        best_distance = 1.0
        
        for student in students:
            if student.face_encoding:
                try:
                    known_encoding = json.loads(student.face_encoding)
                    distance = face_recognition.face_distance([np.array(known_encoding)], np.array(unknown_encoding))[0]
                    
                    if distance < best_distance and distance <= 0.6:
                        best_distance = distance
                        best_match = student
                except Exception as e:
                    print(f"Error processing student {student.student_id}: {e}")
                    continue
        
        return best_match
    except Exception as e:
        print(f"Error finding matching student: {e}")
        return None

def detect_faces_in_frame(frame):
    """
    Detect faces in a video frame.
    Returns list of face locations.
    """
    # Check import at runtime to ensure we have the latest state
    try:
        import face_recognition
    except ImportError:
        raise ImportError("face_recognition library is not installed. Please install dlib and face-recognition.")
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        return face_locations
    except Exception as e:
        print(f"Error detecting faces: {e}")
        return []
def is_smiling(landmarks):
    """
    Detect if a face is smiling based on landmarks.
    Simple heuristic: Width of mouth vs Height of mouth.
    """
    try:
        top_lip = landmarks['top_lip']
        bottom_lip = landmarks['bottom_lip']
        
        # Find mouth corners (leftmost and rightmost x)
        mouth_left = min(top_lip, key=lambda p: p[0])
        mouth_right = max(top_lip, key=lambda p: p[0])
        mouth_width = getattr(mouth_right, 'x', mouth_right[0]) - getattr(mouth_left, 'x', mouth_left[0])
        
        # Find mouth top and bottom (min y of top_lip, max y of bottom_lip)
        mouth_top = min(top_lip, key=lambda p: p[1])
        mouth_bottom = max(bottom_lip, key=lambda p: p[1])
        mouth_height = getattr(mouth_bottom, 'y', mouth_bottom[1]) - getattr(mouth_top, 'y', mouth_top[1])
        
        # Smile Ratio: Width / Height
        # A neutral mouth is usually short and slightly open or closed.
        # A smile is wide. 
        # But an open mouth (yawning) is tall.
        # Let's verify mouth corners (y-coord) vs lip center (y-coord).
        # Smiles have corners HIGHER (lower Y) than center.
        
        # Get lip center (approx)
        center_idx = len(top_lip) // 2
        lip_center_y = top_lip[center_idx][1]
        
        left_corner_y = mouth_left[1]
        right_corner_y = mouth_right[1]
        avg_corner_y = (left_corner_y + right_corner_y) / 2
        
        # If corners are significantly higher than center (lower y value), it's a smile.
        # Offset threshold: 2 pixels?
        curvature = lip_center_y - avg_corner_y
        
        # Also check ratio to avoid false positives from head tilt
        ratio = mouth_width / (mouth_height + 1)
        
        # Heuristic: High curvature OR very wide ratio
        if curvature > 4: # Corners are 4px higher than center
            return True
        
        if ratio > 2.5: # Very wide mouth
            return True
            
        return False
    except Exception as e:
        print(f"Error checking smile: {e}")
        return False

def analyze_faces(frame):
    """
    Detect faces, getting locations, encodings, and smile status.
    Returns: [{'location': loc, 'encoding': enc, 'is_smiling': bool}]
    """
    try:
        import face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 1. Locations
        locations = face_recognition.face_locations(rgb_frame)
        if not locations:
            return []
            
        # 2. Landmarks (for smile)
        landmarks_list = face_recognition.face_landmarks(rgb_frame, locations)
        
        # 3. Encodings
        encodings = face_recognition.face_encodings(rgb_frame, locations)
        
        results = []
        for i in range(len(locations)):
            smile = False
            if i < len(landmarks_list):
                smile = is_smiling(landmarks_list[i])
                
            results.append({
                'location': locations[i],
                'encoding': encodings[i].tolist(),
                'is_smiling': smile
            })
            
        return results
    except Exception as e:
        print(f"Error analyzing faces: {e}")
        return []
