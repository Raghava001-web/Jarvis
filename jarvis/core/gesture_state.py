"""
Gesture State - Smooth stateful gesture tracking
=================================================
Maintains history for velocity-based gesture detection.
No jitter, smooth swipes, proper debouncing.
"""

from collections import deque
from typing import Tuple, Optional
import numpy as np


class GestureState:
    """
    Tracks gesture state over time for smooth detection.
    Uses sliding window for velocity calculation.
    """
    
    def __init__(self, window: int = 7):
        self.positions = deque(maxlen=window)   # palm center history
        self.pinch_values = deque(maxlen=window)  # thumb-index distance
        self.last_gesture: Optional[str] = None
        self.gesture_cooldown: int = 0  # frames to wait before next gesture
        
    def update(self, palm_center: Tuple[float, float], pinch_dist: float):
        """Update tracking state with new frame data"""
        self.positions.append(np.array(palm_center))
        self.pinch_values.append(pinch_dist)
        
        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1
            
    def smoothed_velocity(self) -> tuple:
        """Calculate smooth velocity from position history. Returns (vx, vy) tuple."""
        if len(self.positions) < 3:
            return (0.0, 0.0)
            
        diffs = np.diff(np.array(self.positions), axis=0)
        mean = np.mean(diffs, axis=0)
        return (float(mean[0]), float(mean[1]))
        
    def smoothed_pinch(self) -> float:
        """Get smoothed pinch distance"""
        if not self.pinch_values:
            return 1.0
        return float(np.mean(self.pinch_values))
        
    def can_trigger(self) -> bool:
        """Check if cooldown allows new gesture"""
        return self.gesture_cooldown == 0
        
    def set_cooldown(self, frames: int = 10):
        """Set cooldown after gesture triggers"""
        self.gesture_cooldown = frames
        
    def clear(self):
        """Reset state"""
        self.positions.clear()
        self.pinch_values.clear()
        self.last_gesture = None
        self.gesture_cooldown = 0
