"""
PHASE 1.2: Gesture Classification Test
Tests the classify_gesture function with detected hand landmarks
"""

import cv2
import time
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
MODEL_PATH = SCRIPT_DIR.parent / "models" / "hand_landmarker.task"

print("\n" + "="*50)
print("PHASE 1.2: GESTURE CLASSIFICATION TEST")
print("="*50)

# Check model
if not MODEL_PATH.exists():
    print(f"[FAIL] Model not found: {MODEL_PATH}")
    exit(1)

# Imports
import mediapipe
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
print(f"[OK] MediaPipe v{mediapipe.__version__}")

# =====================================================
# GESTURE CLASSIFIER (copy from test_vision.py)
# =====================================================

def classify_gesture(landmarks, debug=False):
    """Classify hand gesture from landmarks"""
    if len(landmarks) < 21:
        return "Unknown"
    
    # Key landmarks
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    index_mcp = landmarks[5]
    middle_tip = landmarks[12]
    middle_pip = landmarks[10]
    ring_tip = landmarks[16]
    ring_pip = landmarks[14]
    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]
    wrist = landmarks[0]
    
    # SIMPLE FINGER CURL DETECTION
    # Finger is EXTENDED if tip is above (lower y) than PIP joint
    index_extended = index_tip.y < index_pip.y
    middle_extended = middle_tip.y < middle_pip.y
    ring_extended = ring_tip.y < ring_pip.y
    pinky_extended = pinky_tip.y < pinky_pip.y
    
    # Thumb is different - check if extended horizontally away from palm
    thumb_extended = abs(thumb_tip.x - index_mcp.x) > 0.05
    
    # Count extended fingers (excluding thumb for most gestures)
    fingers_up = sum([index_extended, middle_extended, ring_extended, pinky_extended])
    
    if debug:
        print(f"  Fingers: I={index_extended} M={middle_extended} R={ring_extended} P={pinky_extended} T={thumb_extended} | Total={fingers_up}")
    
    # GESTURE CLASSIFICATION (ordered by specificity)
    
    # FIST: all fingers curled
    if fingers_up == 0 and not thumb_extended:
        return "Fist"
    
    # OPEN PALM: all 4 fingers extended
    if fingers_up >= 4:
        return "Open Palm"
    
    # PEACE: only index and middle extended
    if index_extended and middle_extended and not ring_extended and not pinky_extended:
        return "Peace"
    
    # POINTING: only index extended
    if index_extended and not middle_extended and not ring_extended and not pinky_extended:
        return "Pointing"
    
    # THUMBS UP: thumb extended, all fingers curled
    if thumb_extended and fingers_up == 0:
        # Check thumb is pointing UP (thumb tip above thumb IP)
        if thumb_tip.y < thumb_ip.y:
            return "Thumbs Up"
        else:
            return "Thumbs Down"
    
    # ROCK: index and pinky extended (horns)
    if index_extended and pinky_extended and not middle_extended and not ring_extended:
        return "Rock"
    
    # THREE: index, middle, ring extended
    if index_extended and middle_extended and ring_extended and not pinky_extended:
        return "Three"
    
    return "Unknown"


def test_gesture_classification():
    """Test gesture classification"""
    
    # Initialize
    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
    detector = vision.HandLandmarker.create_from_options(options)
    print("[OK] Hand landmarker ready")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[FAIL] Camera failed")
        return False
    
    print("[OK] Camera ready")
    print("\nTest each gesture and verify the label is correct:")
    print("  1. FIST - make a fist")
    print("  2. OPEN PALM - show open hand")
    print("  3. PEACE - peace sign (index + middle)")
    print("  4. POINTING - point with index finger")
    print("  5. THUMBS UP - thumbs up")
    print("\nPress Q to quit\n")
    
    # Track results
    gesture_counts = {}
    last_gesture = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect hand
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=rgb)
        result = detector.detect(mp_image)
        
        gesture = "None"
        
        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            
            # Draw landmarks
            for lm in landmarks:
                x, y = int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
            
            # Classify
            gesture = classify_gesture(landmarks, debug=False)
            
            # Track
            if gesture != "Unknown" and gesture != last_gesture:
                gesture_counts[gesture] = gesture_counts.get(gesture, 0) + 1
                print(f"[GESTURE] {gesture}")
                last_gesture = gesture
        
        # Draw UI
        color = (0, 255, 0) if gesture != "None" and gesture != "Unknown" else (0, 0, 255)
        cv2.putText(frame, f"GESTURE: {gesture}", (10, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        
        # Show detected gestures summary
        y = 80
        for g, count in gesture_counts.items():
            cv2.putText(frame, f"  {g}: {count}x", (10, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y += 25
        
        cv2.imshow("Gesture Test (Q to quit)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    
    # Results
    print("\n" + "="*50)
    print("GESTURE TEST RESULTS")
    print("="*50)
    print("Gestures detected:")
    for g, count in gesture_counts.items():
        print(f"  {g}: {count} times")
    
    # Pass if at least 3 different gestures were detected
    unique = len(gesture_counts)
    print(f"\nUnique gestures detected: {unique}")
    
    if unique >= 3:
        print("\n[PASS] Gesture classification working!")
        return True
    else:
        print("\n[FAIL] Not enough gestures detected. Try different hand positions.")
        return False


if __name__ == "__main__":
    result = test_gesture_classification()
    print(f"\n{'='*50}")
    print(f"FINAL: {'PASS' if result else 'FAIL'}")
    print(f"{'='*50}")
