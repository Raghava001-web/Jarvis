"""
Gesture Controller - Smooth Touchless Trackpad
==============================================
Detects: swipes, pinch/zoom, scroll, open palm.
Uses velocity-based detection for natural feel.

Updated for MediaPipe Tasks API (0.10.x+)
"""

import cv2
import numpy as np
import os
from typing import Tuple, Dict, Optional, Any
from pathlib import Path

# Import gesture state  
try:
    from .gesture_state import GestureState
except ImportError:
    from gesture_state import GestureState

# Try to import mediapipe tasks API
MP_AVAILABLE = False
HandLandmarker = None
HandLandmarkerOptions = None
HandLandmarkerResult = None

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    from mediapipe import Image as MpImage
    from mediapipe import ImageFormat as MpImageFormat
    
    HandLandmarker = mp_vision.HandLandmarker
    HandLandmarkerOptions = mp_vision.HandLandmarkerOptions
    HandLandmarkerResult = mp_vision.HandLandmarkerResult
    
    MP_AVAILABLE = True
    print("[GESTURE] MediaPipe Tasks API available")
except ImportError as e:
    print(f"[GESTURE] MediaPipe Tasks not available: {e}")
except Exception as e:
    print(f"[GESTURE] MediaPipe Tasks error: {e}")


class GestureController:
    """
    Smooth gesture detection using MediaPipe Tasks HandLandmarker.
    Returns gesture type + metadata for app-specific handling.
    
    Features:
    - Discrete gestures: swipe, pinch, open_palm
    - Continuous gestures: rotate, hand_tracking
    - Delta tracking for smooth UI transitions
    """
    
    # Gesture thresholds (tuned for natural feel)
    SWIPE_THRESHOLD = 0.015      # velocity threshold for swipes
    PINCH_CLOSE = 0.05           # pinch closed threshold
    PINCH_OPEN = 0.12            # pinch open (zoom) threshold
    ROTATE_THRESHOLD = 0.02     # angle change for rotation
    COOLDOWN_FRAMES = 15         # frames between discrete gestures
    
    # Model path
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    MODEL_NAME = "hand_landmarker.task"
    
    def __init__(self, perception=None):
        print("[GESTURE] Initializing Gesture Controller...")
        
        self.perception = perception
        self.landmarker = None
        self.state = GestureState()
        self.active = False
        
        # Latest detection result (for sync mode)
        self.latest_result = None
        
        # Continuous tracking state
        self.last_palm = None
        self.last_angle = None
        self.tracking_mode = False  # True = output continuous positions
        
        if MP_AVAILABLE:
            self._initialize_landmarker()
        else:
            print("[GESTURE] Gesture Controller Disabled (MediaPipe Tasks not available)")
    
    def _get_model_path(self) -> str:
        """Get or download the hand landmarker model"""
        model_dir = Path(__file__).parent.parent / "data" / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / self.MODEL_NAME
        
        if not model_path.exists():
            print(f"[GESTURE] Downloading hand landmarker model...")
            try:
                import urllib.request
                urllib.request.urlretrieve(self.MODEL_URL, str(model_path))
                print(f"[GESTURE] Model downloaded to {model_path}")
            except Exception as e:
                print(f"[GESTURE] Failed to download model: {e}")
                return None
        
        return str(model_path)
    
    def _initialize_landmarker(self):
        """Initialize the HandLandmarker with Tasks API"""
        model_path = self._get_model_path()
        
        if not model_path or not os.path.exists(model_path):
            print("[GESTURE] Model not available")
            return
        
        try:
            # Create options
            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            
            options = HandLandmarkerOptions(
                base_options=base_options,
                running_mode=mp_vision.RunningMode.IMAGE,  # Sync mode for simpler processing
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            
            self.landmarker = HandLandmarker.create_from_options(options)
            self.active = True
            print("[GESTURE] Gesture Controller Ready (Tasks API)")
            
        except Exception as e:
            print(f"[GESTURE] Landmarker init error: {e}")
            self.active = False
    
    def enable_tracking(self, enabled: bool = True):
        """Enable/disable continuous position tracking mode"""
        self.tracking_mode = enabled
    
    def disable_tracking(self):
        """Disable continuous position tracking mode"""
        self.tracking_mode = False
        
    def detect(self, frame: np.ndarray) -> Tuple[str, Dict[str, Any]]:
        """
        Detect gesture from camera frame.
        Returns: (gesture_name, metadata_dict)
        """
        if not self.active or self.landmarker is None:
            return "disabled", {}
        
        try:
            h, w, _ = frame.shape
            
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create MediaPipe Image
            mp_image = MpImage(image_format=MpImageFormat.SRGB, data=rgb)
            
            # Detect hands
            result = self.landmarker.detect(mp_image)
            
            if not result.hand_landmarks or len(result.hand_landmarks) == 0:
                self.state.clear()
                self.last_palm = None
                self.last_angle = None
                return "idle", {}
            
            # Get first hand landmarks
            hand_landmarks = result.hand_landmarks[0]
            
            # Extract landmarks as simple objects with x, y, z
            lm = hand_landmarks
            
            # Calculate palm center (wrist + middle MCP average)
            palm = (
                (lm[0].x + lm[9].x) / 2,
                (lm[0].y + lm[9].y) / 2
            )
            
            # Calculate delta (for smooth tracking)
            delta = (0.0, 0.0)
            if self.last_palm:
                delta = (palm[0] - self.last_palm[0], palm[1] - self.last_palm[1])
            
            # Calculate hand angle (wrist to middle finger base)
            angle = np.arctan2(lm[9].y - lm[0].y, lm[9].x - lm[0].x)
            angle_delta = 0.0
            if self.last_angle is not None:
                angle_delta = angle - self.last_angle
                # Normalize to [-pi, pi]
                if angle_delta > np.pi:
                    angle_delta -= 2 * np.pi
                elif angle_delta < -np.pi:
                    angle_delta += 2 * np.pi
            
            # Calculate pinch distance (thumb tip to index tip)
            pinch = self._distance(
                (lm[4].x, lm[4].y),  # thumb tip
                (lm[8].x, lm[8].y)   # index tip
            )
            
            # Update state
            self.state.update(palm, pinch)
            self.last_palm = palm
            self.last_angle = angle
            
            # Get smoothed values
            vel = self.state.smoothed_velocity()
            pinch_smooth = self.state.smoothed_pinch()
            
            # Compute confidence
            confidence = min(1.0, max(0.3, 
                0.7 + abs(vel[0]) * 5 + abs(vel[1]) * 5 - abs(pinch_smooth - 0.08) * 2
            ))
            
            meta = {
                "palm": palm,
                "palm_x": float(palm[0]),
                "palm_y": float(palm[1]),
                "delta": delta,
                "delta_x": float(delta[0]),
                "delta_y": float(delta[1]),
                "angle": float(angle),
                "angle_delta": float(angle_delta),
                "pinch_distance": float(pinch_smooth),
                "confidence": float(confidence),
            }
            
            # Check cooldown for discrete gestures
            if not self.state.can_trigger():
                if self.tracking_mode:
                    return "hand_tracking", meta
                return "tracking", meta
            
            # === DETECT DISCRETE GESTURES ===
            
            # 1. OPEN PALM (all fingers extended) — CHECK FIRST!
            # Must come before pinch/zoom: closing then opening hand
            # would otherwise trigger zoom (large thumb-index distance)
            if self._is_open_palm(lm):
                self.state.set_cooldown(self.COOLDOWN_FRAMES * 2)
                return "open_palm", meta
            
            # 2. PINCH (select/confirm)
            if pinch_smooth < self.PINCH_CLOSE:
                self.state.set_cooldown(self.COOLDOWN_FRAMES)
                meta["strength"] = float(1 - pinch_smooth)
                return "pinch", meta
            
            # 3. ZOOM (spread fingers — but NOT open palm)
            if pinch_smooth > self.PINCH_OPEN:
                meta["strength"] = float(pinch_smooth)
                return "zoom", meta
            
            # 4. ROTATION (for globe control) 
            if abs(angle_delta) > self.ROTATE_THRESHOLD:
                gesture = "rotate_cw" if angle_delta > 0 else "rotate_ccw"
                meta["speed"] = float(abs(angle_delta))
                return gesture, meta
            
            # 5. HORIZONTAL SWIPES
            if abs(vel[0]) > self.SWIPE_THRESHOLD and abs(vel[0]) > abs(vel[1]):
                gesture = "swipe_right" if vel[0] > 0 else "swipe_left"
                self.state.set_cooldown(self.COOLDOWN_FRAMES)
                meta["speed"] = float(abs(vel[0]))
                return gesture, meta
            
            # 6. VERTICAL SWIPES
            if abs(vel[1]) > self.SWIPE_THRESHOLD and abs(vel[1]) > abs(vel[0]):
                gesture = "swipe_down" if vel[1] > 0 else "swipe_up"
                self.state.set_cooldown(self.COOLDOWN_FRAMES)
                meta["speed"] = float(abs(vel[1]))
                return gesture, meta
            
            # If tracking mode, return continuous position
            if self.tracking_mode:
                return "hand_tracking", meta
            
            return "tracking", meta
            
        except Exception as e:
            print(f"[GESTURE] Detection error: {e}")
            return "error", {"error": str(e)}
        
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Euclidean distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
    def _is_open_palm(self, landmarks) -> bool:
        """Check if palm is open (all fingers extended)"""
        # Compare fingertips to MCP joints
        tips = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky
        mcps = [2, 5, 9, 13, 17]
        
        extended = 0
        for tip, mcp in zip(tips, mcps):
            if landmarks[tip].y < landmarks[mcp].y:
                extended += 1
                
        return extended >= 4  # at least 4 fingers extended
        
    def close(self):
        """Cleanup resources"""
        if self.landmarker:
            self.landmarker.close()
            self.landmarker = None
        self.active = False


# Gesture to action mapping (app-aware)
GESTURE_ACTIONS = {
    "youtube": {
        "swipe_right": "next_video",
        "swipe_left": "previous_video",
        "swipe_up": "volume_up",
        "swipe_down": "volume_down",
        "pinch": "play_pause",
        "open_palm": "stop",
        "rotate_cw": "seek_forward",
        "rotate_ccw": "seek_backward",
    },
    "spotify": {
        "swipe_right": "next_track",
        "swipe_left": "previous_track",
        "swipe_up": "volume_up",
        "swipe_down": "volume_down",
        "pinch": "play_pause",
        "rotate_cw": "seek_forward",
        "rotate_ccw": "seek_backward",
    },
    "browser": {
        "swipe_right": "forward",
        "swipe_left": "back",
        "swipe_up": "scroll_up",
        "swipe_down": "scroll_down",
        "pinch": "click",
        "zoom": "zoom_in",
        "rotate_cw": "zoom_in",
        "rotate_ccw": "zoom_out",
    },
    "globe": {
        "swipe_right": "rotate_earth_right",
        "swipe_left": "rotate_earth_left",
        "swipe_up": "tilt_up",
        "swipe_down": "tilt_down",
        "pinch": "select_location",
        "zoom": "zoom_in",
        "open_palm": "reset_view",
        "rotate_cw": "rotate_earth_cw",
        "rotate_ccw": "rotate_earth_ccw",
        "hand_tracking": "continuous_control",
    },
    "music": {
        "swipe_right": "next_track",
        "swipe_left": "previous_track",
        "swipe_up": "volume_up",
        "swipe_down": "volume_down",
        "pinch": "play_pause",
        "open_palm": "stop",
        "rotate_cw": "seek_forward",
        "rotate_ccw": "seek_backward",
    },
    "pdf": {
        "swipe_right": "next_page",
        "swipe_left": "previous_page",
        "swipe_up": "scroll_up",
        "swipe_down": "scroll_down",
        "pinch": "select_text",
        "zoom": "zoom_in",
        "open_palm": "close_pdf",
        "rotate_cw": "zoom_in",
        "rotate_ccw": "zoom_out",
    },
    "default": {
        "swipe_right": "next",
        "swipe_left": "previous",
        "swipe_up": "scroll_up",
        "swipe_down": "scroll_down",
        "pinch": "select",
        "open_palm": "stop_speaking",
        "zoom": "zoom_in",
        "rotate_cw": "rotate_right",
        "rotate_ccw": "rotate_left",
        "hand_tracking": "cursor_control",
    }
}


def get_gesture_action(gesture: str, app: str = "default") -> Optional[str]:
    """Map gesture to action based on active app"""
    actions = GESTURE_ACTIONS.get(app, GESTURE_ACTIONS["default"])
    return actions.get(gesture)


def execute_gesture_action(action: str) -> bool:
    """Execute a gesture action using pyautogui keyboard/mouse simulation.
    
    This is the execution layer that connects gesture detection → system actions.
    Returns True if action was executed.
    """
    if not action:
        return False
    
    try:
        import pyautogui
        import time
        
        # Action → keyboard/mouse mapping
        ACTION_KEYS = {
            # Playback
            "play_pause": lambda: pyautogui.press('space'),
            "stop": lambda: pyautogui.press('space'),
            "next_track": lambda: pyautogui.hotkey('ctrl', 'right'),
            "previous_track": lambda: pyautogui.hotkey('ctrl', 'left'),
            "next_video": lambda: pyautogui.hotkey('shift', 'n'),
            "previous_video": lambda: pyautogui.hotkey('shift', 'p'),
            "seek_forward": lambda: pyautogui.press('right'),
            "seek_backward": lambda: pyautogui.press('left'),
            
            # Volume
            "volume_up": lambda: [pyautogui.press('volumeup') for _ in range(3)],
            "volume_down": lambda: [pyautogui.press('volumedown') for _ in range(3)],
            
            # Scrolling
            "scroll_up": lambda: pyautogui.scroll(5),
            "scroll_down": lambda: pyautogui.scroll(-5),
            
            # Navigation
            "next": lambda: pyautogui.press('right'),
            "previous": lambda: pyautogui.press('left'),
            "forward": lambda: pyautogui.hotkey('alt', 'right'),
            "back": lambda: pyautogui.hotkey('alt', 'left'),
            "next_page": lambda: pyautogui.press('pagedown'),
            "previous_page": lambda: pyautogui.press('pageup'),
            
            # Zoom (DISABLED - misfires too easily)
            "zoom_in": lambda: None,
            "zoom_out": lambda: None,
            
            # Selection
            "select": lambda: pyautogui.click(),
            "click": lambda: pyautogui.click(),
            "select_text": lambda: pyautogui.click(),
            "select_location": lambda: pyautogui.click(),
            
            # Cancel/close
            "cancel": lambda: pyautogui.press('escape'),
            "close_pdf": lambda: pyautogui.hotkey('ctrl', 'w'),
            "reset_view": lambda: pyautogui.hotkey('ctrl', '0'),
            "stop_speaking": lambda: None,  # Handled by WebSocket server, not pyautogui
        }
        
        executor = ACTION_KEYS.get(action)
        if executor:
            executor()
            print(f"[GESTURE] Executed action: {action}")
            return True
        else:
            print(f"[GESTURE] Unknown action: {action}")
            return False
            
    except ImportError:
        print("[GESTURE] pyautogui not available for gesture actions")
        return False
    except Exception as e:
        print(f"[GESTURE] Action execution error: {e}")
        return False


# Singleton
_controller = None

def get_gesture_controller(perception=None) -> GestureController:
    global _controller
    if _controller is None:
        _controller = GestureController(perception)
    return _controller
