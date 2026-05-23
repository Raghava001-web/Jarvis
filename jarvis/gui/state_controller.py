"""
JARVIS State Controller
=======================
Extracted from websocket_server.py — centralized state manager for UI.

Single source of truth for: state transitions, gesture vectors,
user/mood/emotion tracking, trust scoring, and duplicate detection.
"""

import time
from typing import Dict, Any

from jarvis.gui.mood_engine import EmotionStateMachine


class UIStateController:
    """Centralized state manager - SINGLE SOURCE OF TRUTH for UI
    
    All state changes flow through here. UI receives complete state updates.
    """
    
    VALID_TRANSITIONS = {
        "idle": {"listening"},
        "listening": {"processing", "idle"},
        "processing": {"speaking", "idle"},
        "speaking": {"idle"},
    }

    def __init__(self):
        # Core state
        self.state = "idle"
        self.context: Dict[str, Any] = {}
        
        # Response tracking (prevents duplicates)
        self.last_response: str = None
        self.last_response_time: float = 0.0
        self.last_command: str = None
        self.last_command_time: float = 0.0
        
        # EMOTION STATE MACHINE - Proper state transitions
        self.emotion_machine = EmotionStateMachine()
        
        # Vision features - ALL AUTO-ENABLED ON STARTUP
        self.gesture_enabled = True   # Auto-enabled from boot
        self.face_enabled = True      # Always on by default
        self.emotion_enabled = True   # Always on by default
        
        # ═══════════════════════════════════════════════════════════════
        # GESTURE VECTOR with EMA Smoothing
        # Instead of discrete labels, use continuous vectors
        # ═══════════════════════════════════════════════════════════════
        self.gesture_vector = {
            "dx": 0.0,      # Horizontal movement (-1 to +1)
            "dy": 0.0,      # Vertical movement (-1 to +1)
            "speed": 0.0,   # Movement speed (0 to 1)
            "confidence": 0.0
        }
        self.gesture_ema_alpha = 0.3  # Smoothing factor (0.2=cinematic, 0.5=reactive)
        self.last_gesture = None
        self.last_gesture_time = 0.0
        
        # ═══════════════════════════════════════════════════════════════
        # USER CONTEXT VECTOR (Face + Mood Fusion)
        # ═══════════════════════════════════════════════════════════════
        self.current_user = None
        self.user_confidence = 0.0
        self.user_last_seen = 0.0  # Timestamp
        
        # Emotion vector: [happy, sad, angry, neutral, tired]
        self.emotion_vector = [0.0, 0.0, 0.0, 1.0, 0.0]
        self.current_mood = None
        self.mood_confidence = 0.0
        self.mood_stability = 1.0  # How stable mood has been (0-1)
        
        # Trust score: Face + Emotion + Recency fusion
        self.trust_score = 0.0
        self.fatigue_score = 0.0
        self.attention_score = 1.0
        
        # Intent tracking
        self.last_intent = None
        self.intent_confidence = 0.0
        
        # Active app (for context-aware gestures)
        self.active_app = None
        self._active_app_time = 0.0

    def transition(self, to_state: str) -> str:
        """Transition to a new state if valid"""
        if to_state in self.VALID_TRANSITIONS.get(self.state, set()):
            self.state = to_state
        return self.state

    def force_state(self, state: str) -> str:
        """Force state (for error recovery)"""
        self.state = state
        return self.state

    def is_duplicate_response(self, text: str, window_seconds: float = 2.0) -> bool:
        """Check if this response was just sent (prevents loops)"""
        now = time.time()
        if text == self.last_response and (now - self.last_response_time) < window_seconds:
            return True
        self.last_response = text
        self.last_response_time = now
        return False

    def is_duplicate_command(self, command: str, window_seconds: float = 2.0) -> bool:
        """Check if this command was just processed (prevents duplicate processing)"""
        now = time.time()
        cmd_lower = command.lower().strip()
        last_lower = (self.last_command or "").lower().strip()
        if cmd_lower == last_lower and (now - self.last_command_time) < window_seconds:
            return True
        self.last_command = command
        self.last_command_time = now
        return False

    def update_context(self, key: str, value: Any):
        """Update context (e.g., from globe events)"""
        self.context[key] = value

    def update_gesture(self, gesture: str):
        """Update last detected gesture (label)"""
        self.last_gesture = gesture
        self.last_gesture_time = time.time()
    
    def update_gesture_vector(self, dx: float, dy: float, speed: float, confidence: float):
        """Update gesture vector with EMA smoothing for smooth UI feedback
        
        G_smooth = α * G_new + (1-α) * G_old
        α=0.2 (cinematic), α=0.5 (reactive)
        """
        α = self.gesture_ema_alpha
        self.gesture_vector = {
            "dx": α * dx + (1-α) * self.gesture_vector["dx"],
            "dy": α * dy + (1-α) * self.gesture_vector["dy"],
            "speed": α * speed + (1-α) * self.gesture_vector["speed"],
            "confidence": α * confidence + (1-α) * self.gesture_vector["confidence"]
        }
        
        # Infer discrete gesture from smoothed vector
        gv = self.gesture_vector
        if gv["confidence"] > 0.7:
            if gv["dx"] > 0.7:
                self.last_gesture = "next_track"
            elif gv["dx"] < -0.7:
                self.last_gesture = "previous_track"
            elif gv["dy"] > 0.7:
                self.last_gesture = "volume_up"
            elif gv["dy"] < -0.7:
                self.last_gesture = "volume_down"
            self.last_gesture_time = time.time()

    def update_user(self, user: str, confidence: float):
        """Update recognized user and recency"""
        self.current_user = user
        self.user_confidence = confidence
        self.user_last_seen = time.time()
        self._compute_trust_score()

    def update_mood(self, mood: str, confidence: float):
        """Update detected mood and emotion vector"""
        self.current_mood = mood
        self.mood_confidence = confidence
        
        # Update emotion vector: [happy, sad, angry, neutral, tired]
        mood_to_idx = {"happy": 0, "sad": 1, "angry": 2, "neutral": 3, "tired": 4}
        if mood.lower() in mood_to_idx:
            idx = mood_to_idx[mood.lower()]
            # Decay all, boost current
            self.emotion_vector = [v * 0.8 for v in self.emotion_vector]
            self.emotion_vector[idx] = min(1.0, self.emotion_vector[idx] + confidence * 0.3)
        
        self._compute_trust_score()
    
    def _compute_trust_score(self):
        """Compute trust score from face + emotion + recency fusion
        
        trust_score = 0.6*face_confidence + 0.2*emotion_stability + 0.2*recency
        
        > 0.8 = "OWNER CONFIRMED"
        0.5-0.8 = "POSSIBLE USER"
        < 0.5 = "UNKNOWN"
        """
        # Recency factor: decays over 60 seconds
        now = time.time()
        recency = max(0.0, 1.0 - (now - self.user_last_seen) / 60.0) if self.user_last_seen > 0 else 0.0
        
        # Mo-05: Emotion stability = confident detection = high stability
        emotion_sum = sum(self.emotion_vector)
        emotion_stability = max(self.emotion_vector) if emotion_sum > 0 else 0.5
        
        self.trust_score = (
            0.6 * self.user_confidence +
            0.2 * emotion_stability +
            0.2 * recency
        )
        
        # Update fatigue from tired component
        self.fatigue_score = self.emotion_vector[4]  # tired index

    def update_intent(self, intent: str, confidence: float):
        """Update last intent"""
        self.last_intent = intent
        self.intent_confidence = confidence
    
    def get_trust_level(self) -> str:
        """Get human-readable trust level"""
        if self.trust_score > 0.8:
            return "OWNER CONFIRMED"
        elif self.trust_score > 0.5:
            return "POSSIBLE USER"
        else:
            return "UNKNOWN"
    
    def should_clarify(self) -> bool:
        """Whether JARVIS should ask for clarification based on mood"""
        # If user is frustrated, raise the clarification threshold
        if self.current_mood and self.current_mood.lower() in ("frustrated", "angry"):
            return self.intent_confidence < 0.8  # Higher threshold
        return self.intent_confidence < 0.6  # Normal threshold

    def snapshot(self) -> Dict[str, Any]:
        """Get current state snapshot (legacy)"""
        return {"state": self.state, "context": dict(self.context)}

    def get_full_state(self) -> Dict[str, Any]:
        """Get COMPLETE state for UI broadcasting - SINGLE SOURCE OF TRUTH"""
        return {
            # Core state
            "state": self.state,
            
            # Vision feature status
            "gesture_enabled": self.gesture_enabled,
            "gesture_available": True,  # Always available
            "face_enabled": self.face_enabled,
            "face_available": True,
            "emotion_enabled": self.emotion_enabled,
            "emotion_available": True,
            
            # Gesture (discrete + vector)
            "last_gesture": self.last_gesture,
            "gesture_vector": self.gesture_vector,  # {dx, dy, speed, confidence}
            
            # Face recognition
            "current_user": self.current_user,
            "user_confidence": self.user_confidence,
            "trust_score": self.trust_score,
            "trust_level": self.get_trust_level(),  # "OWNER CONFIRMED", etc.
            
            # Mood/Emotion
            "current_mood": self.current_mood,
            "mood_confidence": self.mood_confidence,
            "emotion_vector": self.emotion_vector,  # [happy, sad, angry, neutral, tired]
            "fatigue_score": self.fatigue_score,
            "attention_score": self.attention_score,
            
            # Intent
            "last_intent": self.last_intent,
            "intent_confidence": self.intent_confidence,
            
            # Active app
            "active_app": self.active_app,
            
            # Context
            "context": dict(self.context)
        }
