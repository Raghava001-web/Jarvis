"""
Unified Perception Module
=========================
Combines all input modalities:
- Voice (speech recognition)
- Vision (face + gesture + emotion)
- Text (keyboard input)

This is the sensory layer for JARVIS.
"""

import cv2
import threading
import queue
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from pathlib import Path

from .gesture_controller import GestureController, get_gesture_action, get_gesture_controller
from .multimodal_emotion import MultimodalEmotionFusion, get_emotion_fusion
from .face_auth import FaceAuth, get_face_auth


@dataclass
class PerceptionEvent:
    """A perception event from any modality"""
    source: str       # "voice", "gesture", "face", "keyboard"
    event_type: str   # "command", "gesture", "recognition", "emotion"
    data: Any         # Event-specific data
    confidence: float = 1.0


class UnifiedPerception:
    """
    Unified perception layer combining all input modalities.
    Runs in background thread for continuous monitoring.
    """
    
    def __init__(self, callback: Callable[[PerceptionEvent], None] = None):
        print("[PERCEPTION] Initializing Unified Perception...")
        
        # Event callback
        self.on_event = callback
        
        # Modality handlers
        self.gesture = get_gesture_controller()
        self.emotion = get_emotion_fusion()
        self.face_auth = get_face_auth()
        
        # Camera
        self.camera = None
        self.camera_active = False
        
        # Threading
        self.running = False
        self.event_queue: queue.Queue = queue.Queue()
        self.camera_thread: Optional[threading.Thread] = None
        
        # State
        self.current_user: Optional[str] = None
        self.gesture_mode = False  # toggleable gesture control
        self.last_gesture = None
        self.last_emotion = "neutral"
        
        print("[PERCEPTION] Unified Perception Ready")
        
    def start_camera(self, camera_id: int = 0) -> bool:
        """Start camera for visual perception"""
        if self.camera_active:
            return True
            
        try:
            self.camera = cv2.VideoCapture(camera_id)
            if not self.camera.isOpened():
                print("[PERCEPTION] Failed to open camera")
                return False
                
            self.camera_active = True
            self.running = True
            
            # Start background processing
            self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.camera_thread.start()
            
            print("[PERCEPTION] Camera started")
            return True
            
        except Exception as e:
            print(f"[PERCEPTION] Camera error: {e}")
            return False
            
    def stop_camera(self):
        """Stop camera"""
        self.running = False
        self.camera_active = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
            
        print("[PERCEPTION] Camera stopped")
        
    def _camera_loop(self):
        """Background camera processing loop"""
        frame_count = 0
        
        while self.running and self.camera:
            ret, frame = self.camera.read()
            if not ret:
                continue
                
            frame_count += 1
            
            # Process gestures every frame if enabled
            if self.gesture_mode:
                gesture, meta = self.gesture.detect(frame)
                if gesture not in ["idle", "tracking", "disabled"]:
                    self._emit_event(PerceptionEvent(
                        source="gesture",
                        event_type="gesture",
                        data={"gesture": gesture, "meta": meta},
                        confidence=0.8
                    ))
                    
            # Face recognition every 30 frames
            if frame_count % 30 == 0:
                name, confidence = self.face_auth.recognize(frame)
                if name and name != "unknown" and confidence > 0.5:
                    if name != self.current_user:
                        self.current_user = name
                        self._emit_event(PerceptionEvent(
                            source="face",
                            event_type="recognition",
                            data={"user": name},
                            confidence=confidence
                        ))
                        
            # Emotion detection every 60 frames
            if frame_count % 60 == 0:
                try:
                    emotion = self.emotion.detect_from_frame(frame)
                    if emotion != self.last_emotion:
                        self.last_emotion = emotion
                        self._emit_event(PerceptionEvent(
                            source="face",
                            event_type="emotion",
                            data={"emotion": emotion},
                            confidence=0.7
                        ))
                except:
                    pass
                    
    def _emit_event(self, event: PerceptionEvent):
        """Emit event to callback or queue"""
        self.event_queue.put(event)
        
        if self.on_event:
            self.on_event(event)
            
    def get_next_event(self, timeout: float = 0.1) -> Optional[PerceptionEvent]:
        """Get next event from queue (non-blocking)"""
        try:
            return self.event_queue.get(timeout=timeout)
        except queue.Empty:
            return None
            
    def enable_gestures(self):
        """Enable gesture control mode"""
        self.gesture_mode = True
        print("[PERCEPTION] Gesture control enabled")
        
    def disable_gestures(self):
        """Disable gesture control mode"""
        self.gesture_mode = False
        print("[PERCEPTION] Gesture control disabled")
        
    def register_face(self, name: str) -> tuple:
        """Register current camera face to name"""
        if not self.camera_active or not self.camera:
            return False, "Camera not active"
            
        ret, frame = self.camera.read()
        if not ret:
            return False, "Failed to capture frame"
            
        return self.face_auth.register(frame, name)
        
    def detect_text_emotion(self, text: str) -> str:
        """Detect emotion from text"""
        return self.emotion.detect_from_text(text)
        
    def get_current_user(self) -> Optional[str]:
        """Get currently recognized user"""
        return self.current_user
        
    def get_current_emotion(self) -> str:
        """Get current detected emotion"""
        return self.last_emotion
        
    def close(self):
        """Cleanup all resources"""
        self.stop_camera()
        self.gesture.close()


# Singleton
_perception = None

def get_unified_perception(callback=None) -> UnifiedPerception:
    global _perception
    if _perception is None:
        _perception = UnifiedPerception(callback)
    return _perception
