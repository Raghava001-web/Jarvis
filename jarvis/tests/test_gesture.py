"""
JARVIS Feature Test #2: Gesture Control (GestureController)
Tests: Hand gesture recognition via webcam using MediaPipe
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("  JARVIS Feature Test #2: Gesture Control")
print("=" * 60)
print()

# Try to import gesture controller
try:
    from core.gesture_controller import GestureController, GestureType
    print("[OK] GestureController imported successfully")
except ImportError as e:
    print(f"[FAIL] Import error: {e}")
    print("    MediaPipe may not be installed. Run: pip install mediapipe")
    sys.exit(1)

# Check for perception (optional)
perception = None
try:
    from core.perception import PerceptionLayer
    perception = PerceptionLayer()
    print("[OK] PerceptionLayer available for voice feedback")
except:
    print("[INFO] Perception not available, will use print output only")

# Initialize gesture controller
print("\n[1] Initializing GestureController...")
try:
    gesture = GestureController(perception)
    print("[OK] GestureController initialized")
    
    if gesture.is_available():
        print("[OK] MediaPipe is available for gesture detection")
    else:
        print("[WARN] MediaPipe not available - gesture detection won't work")
        print("       Install with: pip install mediapipe opencv-python")
except Exception as e:
    print(f"[FAIL] Init error: {e}")
    sys.exit(1)

# Print supported gestures
print("\n[2] Supported Gestures:")
for gt in GestureType:
    print(f"    - {gt.value}")

# Test gesture detection
print("\n[3] Testing Gesture Detection...")
print("    Starting webcam for 15 seconds...")
print("    Try these gestures in front of the camera:")
print("      - Open palm (all fingers spread)")
print("      - Thumbs up")
print("      - Pointing finger")
print("      - Make a fist")
print("      - Wave your hand")
print()

# Gesture callback
detected_gestures = []

def on_gesture(gesture_type):
    detected_gestures.append(gesture_type)
    print(f"    >>> DETECTED: {gesture_type.value}")
    if perception:
        perception.speak(f"Gesture detected: {gesture_type.value}")

# Register callback for all gestures
for gt in GestureType:
    if gt != GestureType.NONE:
        gesture.register_callback(gt, lambda g=gt: on_gesture(g))

try:
    # Start gesture detection
    gesture.start()
    print("[OK] Gesture detection started - show gestures to the camera!")
    
    # Run for 15 seconds
    time.sleep(15)
    
    # Stop detection
    gesture.stop()
    print("\n[OK] Gesture detection stopped")

except KeyboardInterrupt:
    gesture.stop()
    print("\n[!] Interrupted by user")
except Exception as e:
    print(f"[FAIL] Gesture detection error: {e}")

# Summary
print("\n" + "=" * 60)
print("  Test Complete - Gesture Control")
print("=" * 60)
print(f"\nGestures detected: {len(detected_gestures)}")
if detected_gestures:
    for g in detected_gestures:
        print(f"  - {g.value}")
else:
    print("  No gestures were detected")
    print("  Make sure webcam is working and hand is visible")

print("\nIf gestures were detected, gesture control is ready for HUD integration!")
