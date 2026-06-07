import time
import os
import cv2
import numpy as np
import pyautogui

def record_screen(output_path="docs/jarvis_demo.mp4", duration=60, fps=10):
    """
    Captures screenshots of the primary display at a set frame rate
    and writes them to an MP4 video file.
    """
    print(f"\n==================================================")
    print(f" J.A.R.V.I.S. Screen Capture Utility")
    print(f"==================================================")
    print(f"Output:   {os.path.abspath(output_path)}")
    print(f"Duration: {duration} seconds")
    print(f"FPS:      {fps}")
    print(f"--------------------------------------------------")
    print(f"Prepare your Web HUD window (http://localhost:8080 or http://localhost:9999).")
    
    # Countdown
    for i in range(5, 0, -1):
        print(f"Starting recording in {i} seconds...")
        time.sleep(1)
        
    # Get screen dimensions
    screen_size = pyautogui.size()
    width, height = screen_size.width, screen_size.height
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    delay = 1.0 / fps
    
    print("\n>>> RECORDING ACTIVE! Press Ctrl+C in this window to stop early. <<<")
    start_time = time.time()
    
    try:
        for frame_num in range(total_frames):
            frame_start = time.time()
            
            # Capture screen frame
            img = pyautogui.screenshot()
            
            # Convert RGB to BGR
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Write frame
            out.write(frame)
            
            # Log progress every second
            if (frame_num + 1) % fps == 0:
                elapsed = int(time.time() - start_time)
                print(f"  [Progress] {elapsed:02d}s / {duration:02d}s captured...")
                
            # Maintain stable target frame rate
            time_spent = time.time() - frame_start
            wait_time = max(0.001, delay - time_spent)
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n[INFO] Recording stopped early by keyboard interrupt.")
    finally:
        out.release()
        print(f"\n==================================================")
        print(f"Recording completed successfully!")
        print(f"Saved to: {os.path.abspath(output_path)}")
        print(f"==================================================")

if __name__ == "__main__":
    # Ensure docs directory exists
    os.makedirs("docs", exist_ok=True)
    record_screen(duration=60, fps=10)
