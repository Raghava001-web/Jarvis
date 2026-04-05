"""
PHASE 1.5: Emotion Detection Test
Tests FER (Facial Expression Recognition) library
"""

import cv2
import time

print("\n" + "="*50)
print("PHASE 1.5: EMOTION DETECTION TEST")
print("="*50)

# Try to import FER
try:
    from fer.fer import FER
    print("[OK] FER library imported")
except ImportError as e:
    print(f"[FAIL] FER not installed: {e}")
    print("Install with: pip install fer")
    exit(1)

def test_emotion_detection():
    """Test emotion detection using FER"""
    
    # Initialize detector
    try:
        detector = FER(mtcnn=False)  # Use OpenCV cascade (faster)
        print("[OK] FER detector created")
    except Exception as e:
        print(f"[FAIL] FER init error: {e}")
        return False
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[FAIL] Cannot open camera")
        return False
    
    print("[OK] Camera opened")
    print("\nInstructions:")
    print("- Look at the camera")
    print("- Try different expressions: happy, sad, angry, surprised, neutral")
    print("- Your detected emotion will show on screen")
    print("- Press Q to quit\n")
    
    total_frames = 0
    emotion_frames = 0
    emotion_counts = {}
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        total_frames += 1
        
        # Only process every 3rd frame for performance
        if total_frames % 3 == 0:
            # Detect emotions
            results = detector.detect_emotions(frame)
            
            if results:
                emotion_frames += 1
                
                for result in results:
                    box = result['box']
                    emotions = result['emotions']
                    
                    # Get dominant emotion
                    dominant = max(emotions, key=emotions.get)
                    confidence = emotions[dominant]
                    
                    # Track
                    emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
                    
                    # Draw box
                    x, y, w, h = box
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Draw emotion
                    cv2.putText(frame, f"{dominant.upper()} ({confidence:.0%})", 
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    if total_frames % 15 == 0:
                        print(f"[EMOTION] {dominant} ({confidence:.0%})")
            else:
                cv2.putText(frame, "No face/emotion", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Stats
        elapsed = time.time() - start_time
        if elapsed > 0:
            fps = total_frames / elapsed
            cv2.putText(frame, f"FPS: {fps:.1f}",
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Show emotion counts
        y = 60
        for emotion, count in sorted(emotion_counts.items(), key=lambda x: -x[1])[:5]:
            cv2.putText(frame, f"{emotion}: {count}", (frame.shape[1] - 150, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y += 20
        
        cv2.imshow("Emotion Detection Test (Q to quit)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Results
    print("\n" + "="*50)
    print("EMOTION DETECTION RESULTS")
    print("="*50)
    print(f"Total frames: {total_frames}")
    print(f"Frames with emotion: {emotion_frames}")
    print("\nEmotions detected:")
    for emotion, count in sorted(emotion_counts.items(), key=lambda x: -x[1]):
        print(f"  {emotion}: {count} times")
    
    unique = len(emotion_counts)
    print(f"\nUnique emotions: {unique}")
    
    if unique >= 2 and emotion_frames > 10:
        print("\n[PASS] Emotion detection working!")
        return True
    else:
        print("\n[FAIL] Not enough emotions detected")
        return False

if __name__ == "__main__":
    result = test_emotion_detection()
    print(f"\n{'='*50}")
    print(f"FINAL: {'PASS' if result else 'FAIL'}")
    print(f"{'='*50}")
