"""
PHASE 1.1: Hand Detection ONLY Test
Uses MediaPipe Tasks API (v0.10+) with hand_landmarker.task model
"""

import cv2
import time
import os
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).parent
MODEL_PATH = SCRIPT_DIR.parent / "models" / "hand_landmarker.task"

print("\n" + "="*50)
print("PHASE 1.1: HAND DETECTION TEST")
print("="*50)

# Check model file
if not MODEL_PATH.exists():
    print(f"[FAIL] Model not found: {MODEL_PATH}")
    print("Download from: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
    exit(1)
print(f"[OK] Model found: {MODEL_PATH}")

# Import MediaPipe
try:
    import mediapipe
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    print(f"[OK] MediaPipe v{mediapipe.__version__} imported")
except ImportError as e:
    print(f"[FAIL] MediaPipe import error: {e}")
    exit(1)

def test_hand_detection():
    """Minimal hand detection test using Tasks API"""
    
    # Initialize hand landmarker
    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2
    )
    detector = vision.HandLandmarker.create_from_options(options)
    print("[OK] Hand landmarker created")
    
    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[FAIL] Cannot open camera!")
        return False
    
    print("[OK] Camera opened")
    print("\nInstructions:")
    print("- Show your hand to camera")
    print("- Green 'HAND DETECTED!' when found")
    print("- Press Q to quit\n")
    
    # Stats
    total_frames = 0
    hand_frames = 0
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[FAIL] Frame read failed")
            break
        
        total_frames += 1
        
        # Convert to MediaPipe Image
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=rgb)
        
        # Detect hands
        result = detector.detect(mp_image)
        
        # Check for hands
        if result.hand_landmarks:
            hand_frames += 1
            num_hands = len(result.hand_landmarks)
            
            # Draw landmarks
            for hand_landmarks in result.hand_landmarks:
                for landmark in hand_landmarks:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
            
            cv2.putText(frame, f"HAND DETECTED! ({num_hands})", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Print less frequently to avoid spam
            if total_frames % 10 == 0:
                print(f"[DETECTED] {num_hands} hand(s) - frame {total_frames}")
        else:
            cv2.putText(frame, "No hand", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Stats overlay
        elapsed = time.time() - start_time
        if elapsed > 0:
            fps = total_frames / elapsed
            rate = (hand_frames / total_frames * 100) if total_frames > 0 else 0
            cv2.putText(frame, f"FPS: {fps:.1f} | Detection: {rate:.0f}%", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow("Hand Detection Test (Q to quit)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    
    # Final results
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    print(f"Total frames: {total_frames}")
    print(f"Frames with hand: {hand_frames}")
    rate = (hand_frames / total_frames * 100) if total_frames > 0 else 0
    print(f"Detection rate: {rate:.1f}%")
    
    if rate > 30:
        print("\n[PASS] Hand detection WORKING")
        return True
    else:
        print("\n[FAIL] Hand detection rate too low")
        return False

if __name__ == "__main__":
    result = test_hand_detection()
    print(f"\n{'='*50}")
    print(f"FINAL: {'PASS' if result else 'FAIL'}")
    print(f"{'='*50}")
