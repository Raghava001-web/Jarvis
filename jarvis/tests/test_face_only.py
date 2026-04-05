"""
PHASE 1.3: Face Detection Test (OpenCV version)
Uses OpenCV's Haar cascade - no external dependencies needed
"""

import cv2
import time
import os

print("\n" + "="*50)
print("PHASE 1.3: FACE DETECTION TEST (OpenCV)")
print("="*50)

def test_face_detection():
    """Test face detection using OpenCV Haar cascade"""
    
    # Load Haar cascade from OpenCV data
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    if not os.path.exists(cascade_path):
        print(f"[FAIL] Haar cascade not found: {cascade_path}")
        return False
    
    face_cascade = cv2.CascadeClassifier(cascade_path)
    print("[OK] Face cascade loaded")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[FAIL] Cannot open camera")
        return False
    
    print("[OK] Camera opened")
    print("\nInstructions:")
    print("- Look at the camera")
    print("- Green box should appear around your face")
    print("- Press Q to quit\n")
    
    total_frames = 0
    face_frames = 0
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        total_frames += 1
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )
        
        if len(faces) > 0:
            face_frames += 1
            
            for (x, y, w, h) in faces:
                # Draw box
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "FACE DETECTED", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if total_frames % 15 == 0:
                print(f"[DETECTED] {len(faces)} face(s) - frame {total_frames}")
        else:
            cv2.putText(frame, "No face", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Stats
        elapsed = time.time() - start_time
        if elapsed > 0:
            fps = total_frames / elapsed
            rate = (face_frames / total_frames * 100) if total_frames > 0 else 0
            cv2.putText(frame, f"FPS: {fps:.1f} | Detection: {rate:.0f}%",
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow("Face Detection Test (Q to quit)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Results
    print("\n" + "="*50)
    print("FACE DETECTION RESULTS")
    print("="*50)
    print(f"Total frames: {total_frames}")
    print(f"Frames with face: {face_frames}")
    rate = (face_frames / total_frames * 100) if total_frames > 0 else 0
    print(f"Detection rate: {rate:.1f}%")
    
    if rate > 30:
        print("\n[PASS] Face detection working!")
        return True
    else:
        print("\n[FAIL] Face detection rate too low")
        return False

if __name__ == "__main__":
    result = test_face_detection()
    print(f"\n{'='*50}")
    print(f"FINAL: {'PASS' if result else 'FAIL'}")
    print(f"{'='*50}")
