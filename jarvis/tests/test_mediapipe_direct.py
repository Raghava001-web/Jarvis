"""
Direct MediaPipe Test - No threading, no JARVIS modules
Tests if MediaPipe hand detection works at all
"""

import cv2
import time

print("="*50)
print("  MEDIAPIPE DIRECT TEST")
print("="*50)

# Load model
print("\n[1] Loading MediaPipe...")
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    import os
    
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'hand_landmarker.task')
    print(f"Model path: {model_path}")
    print(f"Exists: {os.path.exists(model_path)}")
    
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        min_hand_detection_confidence=0.4
    )
    hand_landmarker = vision.HandLandmarker.create_from_options(options)
    print("[OK] Hand landmarker created")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

# Open camera
print("\n[2] Opening camera...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[FAIL] Cannot open camera")
    exit(1)
print("[OK] Camera opened")

# Warm up
print("[3] Warming up...")
time.sleep(1)

# Test frames
print("\n[4] Testing detection (10 seconds)...")
print("    Show your hand to the camera!\n")

start_time = time.time()
frame_count = 0
detect_count = 0

while time.time() - start_time < 10:
    ret, frame = cap.read()
    if not ret:
        print("Frame read failed!")
        continue
    
    frame_count += 1
    
    # Convert to RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    
    # Detect
    result = hand_landmarker.detect(mp_image)
    
    if result.hand_landmarks and len(result.hand_landmarks) > 0:
        detect_count += 1
        print(f"  HAND DETECTED! Frame {frame_count} (total detections: {detect_count})")
    
    # Show frame
    cv2.imshow("Test", cv2.flip(frame, 1))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hand_landmarker.close()

print("\n" + "="*50)
print(f"  RESULTS: {detect_count} detections in {frame_count} frames")
print("="*50)
