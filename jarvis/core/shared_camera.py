"""
Shared Camera Manager — Singleton camera for gesture + emotion + face auth
Prevents multiple modules from fighting over cv2.VideoCapture(0)
"""

import cv2
import threading
import time
import numpy as np
from typing import Optional


class SharedCamera:
    """Thread-safe singleton camera manager.
    
    Multiple consumers (gesture, emotion, face auth) share one camera.
    Each consumer gets the latest frame without opening their own.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._cap = None
        self._frame = None
        self._frame_lock = threading.Lock()
        self._running = False
        self._thread = None
        self._consumers = set()  # Track who's using the camera
        self._last_frame_time = 0
        self._fps = 10  # Reduced from 20: 10 FPS is sufficient for face/emotion/gesture
        self._initialized = True
        print("[CAMERA] Shared Camera Manager initialized")
    
    def register(self, consumer_name: str):
        """Register a consumer (gesture, emotion, face_auth)"""
        self._consumers.add(consumer_name)
        print(f"[CAMERA] Registered consumer: {consumer_name} (total: {len(self._consumers)})")
        
        # Auto-start if first consumer
        if not self._running:
            self.start()
    
    def unregister(self, consumer_name: str):
        """Unregister a consumer"""
        self._consumers.discard(consumer_name)
        print(f"[CAMERA] Unregistered consumer: {consumer_name} (remaining: {len(self._consumers)})")
        
        # Auto-stop if no consumers left
        if not self._consumers and self._running:
            self.stop()
    
    def start(self):
        """Start the camera capture thread"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="SharedCameraThread"
        )
        self._thread.start()
    
    def stop(self):
        """Stop the camera capture thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap and self._cap.isOpened():
            self._cap.release()
            self._cap = None
        print("[CAMERA] Camera stopped")
    
    def _capture_loop(self):
        """Background capture loop"""
        frame_interval = 1.0 / self._fps
        
        while self._running:
            try:
                # Open camera if needed
                if self._cap is None or not self._cap.isOpened():
                    self._cap = cv2.VideoCapture(0)
                    if not self._cap.isOpened():
                        print("[CAMERA] Cannot open camera")
                        time.sleep(5)
                        continue
                    # Optimized: 480x360 is enough for face/gesture detection, saves ~40% CPU
                    self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
                    self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
                    print("[CAMERA] Camera opened (480x360 @ 10fps)")
                
                ret, frame = self._cap.read()
                if ret:
                    with self._frame_lock:
                        self._frame = frame
                        self._last_frame_time = time.time()
                
                # Sleep to maintain target FPS
                time.sleep(frame_interval)
                
            except Exception as e:
                print(f"[CAMERA] Capture error: {e}")
                time.sleep(1)
        
        # Cleanup
        if self._cap and self._cap.isOpened():
            self._cap.release()
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest camera frame (thread-safe).
        
        Returns None if no frame available or frame is stale (>2s old).
        """
        with self._frame_lock:
            if self._frame is None:
                return None
            # Check staleness
            if time.time() - self._last_frame_time > 2.0:
                return None
            return self._frame.copy()
    
    @property
    def is_active(self) -> bool:
        return self._running and self._cap is not None and self._cap.isOpened()


# Module-level singleton accessor
_shared_camera = None

def get_shared_camera() -> SharedCamera:
    """Get the shared camera singleton"""
    global _shared_camera
    if _shared_camera is None:
        _shared_camera = SharedCamera()
    return _shared_camera

def release_shared_camera():
    """Force-release the camera on exit (called by atexit)"""
    global _shared_camera
    if _shared_camera is not None:
        try:
            _shared_camera.stop()
            print("[CAMERA] Camera released on exit")
        except Exception:
            pass

# Register atexit cleanup so camera ALWAYS releases when process exits
import atexit
atexit.register(release_shared_camera)
