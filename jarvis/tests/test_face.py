"""
JARVIS Feature Test #3: Face Recognition (FaceRecognition)
Tests: Owner verification and user authentication via webcam
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("  JARVIS Feature Test #3: Face Recognition")
print("=" * 60)
print()

# Try to import face recognition
try:
    from core.face_recognition_auth import FaceRecognition, UserType
    print("[OK] FaceRecognition imported successfully")
except ImportError as e:
    print(f"[FAIL] Import error: {e}")
    print("    face_recognition may not be installed. Run: pip install face_recognition")
    sys.exit(1)

# Check for perception (optional)
perception = None
try:
    from core.perception import PerceptionLayer
    perception = PerceptionLayer()
    print("[OK] PerceptionLayer available for voice feedback")
except:
    print("[INFO] Perception not available, will use print output only")

# Initialize face recognition
print("\n[1] Initializing FaceRecognition...")
try:
    face_auth = FaceRecognition(perception)
    print("[OK] FaceRecognition initialized")
    
    if face_auth.is_available():
        print("[OK] Face recognition library is available")
    else:
        print("[WARN] Face recognition not available")
        print("       Install with: pip install face_recognition dlib")
except Exception as e:
    print(f"[FAIL] Init error: {e}")
    sys.exit(1)

# List registered users
print("\n[2] Registered Users:")
try:
    users = face_auth.list_registered_users()
    if users:
        for user in users:
            print(f"    - {user}")
    else:
        print("    No users registered yet")
except Exception as e:
    print(f"    Error listing users: {e}")

# Test authentication
print("\n[3] Testing Face Authentication...")
print("    Look at your webcam for 10 seconds...")
print("    The system will try to identify you.")
print()

try:
    if perception:
        perception.speak("Sir, please look at the camera for face verification.")
    
    # Try to authenticate
    result = face_auth.authenticate()
    
    if result:
        user_type = face_auth.current_user.user_type if face_auth.current_user else "unknown"
        user_name = face_auth.current_user.name if face_auth.current_user else "Unknown"
        
        print(f"[OK] Face detected!")
        print(f"    User: {user_name}")
        print(f"    Type: {user_type}")
        
        if face_auth.is_owner():
            print("[OK] You are the OWNER - full access granted")
            if perception:
                perception.speak(f"Welcome back, {user_name}. Full access granted.")
        else:
            print("[INFO] Access level restricted for non-owner")
            if perception:
                perception.speak(f"Hello, {user_name}. Limited access mode.")
    else:
        print("[!] No face recognized")
        print("    You may need to register your face first")
        print("    Would you like to register as owner? (The test will skip this)")
        
except Exception as e:
    print(f"[FAIL] Authentication error: {e}")

# Test command access
print("\n[4] Testing Command Access Control...")
test_commands = [
    "what time is it",
    "open whatsapp",
    "send email",
    "delete all files"
]

for cmd in test_commands:
    try:
        allowed, reason = face_auth.check_command_access(cmd)
        status = "[ALLOWED]" if allowed else "[BLOCKED]"
        print(f"    {status} '{cmd}' - {reason}")
    except Exception as e:
        print(f"    [ERROR] '{cmd}' - {e}")

# Summary
print("\n" + "=" * 60)
print("  Test Complete - Face Recognition")
print("=" * 60)
print("""
Results:
- Face detection: Check if your face was detected
- User identification: Check if you were recognized
- Access control: Check if restricted commands are blocked for non-owners

If face recognition worked, it's ready for HUD integration!
""")
