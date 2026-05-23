"""
Emotion Router
==============
Detects user emotion and updates state before routing.
Wrapper around existing emotion detection.
"""

import re
from typing import Optional
from .state_manager import StateManager, UserMood


class EmotionRouter:
    """
    Detects user emotional state and updates StateManager.
    Uses existing emotion detector if available, else text-based inference.
    """
    
    # Text-based emotion cues — Mo-04: no duplicates across categories
    EMOTION_CUES = {
        UserMood.ANGRY: [
            "damn", "hell", "stupid", "hate", "annoying", 
            "angry", "pissed", "ridiculous"
        ],
        UserMood.HAPPY: [
            "awesome", "great", "love", "amazing", "wonderful", "excellent",
            "fantastic", "perfect", "thanks", "thank you", "yay", ":)", "😊"
        ],
        UserMood.SAD: [
            "sad", "depressed", "down", "lonely", "miss", "crying",
            "unhappy", "terrible", "awful", ":(", "😢"
        ],
        UserMood.FRUSTRATED: [
            "why won't", "doesn't work", "not working", "broken", "again",
            "come on", "seriously", "ugh", "can't", "won't", "frustrated"
        ],
        UserMood.TIRED: [
            "tired", "exhausted", "sleepy", "need sleep", "so tired",
            "worn out", "can't focus", "long day"
        ],
        UserMood.EXCITED: [
            "excited", "can't wait", "so cool", "wow", "!!",
            "incredible", "omg", "finally"
        ],
    }
    
    def __init__(self, state_manager: StateManager, emotion_detector=None):
        print("[EMOTION] Initializing Emotion Router...")
        self.state = state_manager
        self.emotion_detector = emotion_detector  # Optional existing detector
        print("[EMOTION] Emotion Router Ready")
        
    def update_mood(self, text: str) -> Optional[UserMood]:
        """
        Detect emotion from text and update state.
        Uses existing detector if available, else text cues.
        Only updates state when a non-neutral emotion is detected.
        """
        mood = None
        
        # Try existing emotion detector first
        if self.emotion_detector:
            try:
                detected = self.emotion_detector.detect(text=text)
                if detected:
                    mood = self._normalize_mood(detected)
            except:
                pass
                
        # Fallback to text-based detection
        if not mood:
            mood = self._detect_from_text(text)
            
        # Only update state if a real (non-neutral) emotion was detected
        # Prevents overwriting genuine detected emotions with NEUTRAL on clean sentences
        if mood and mood != UserMood.NEUTRAL:
            self.state.set_mood(mood.value)
            
        return mood
        
    def _detect_from_text(self, text: str) -> Optional[UserMood]:
        """Simple text-based emotion detection"""
        text_lower = text.lower()
        
        scores = {}
        for mood, cues in self.EMOTION_CUES.items():
            score = sum(1 for cue in cues if cue in text_lower)
            if score > 0:
                scores[mood] = score
                
        if not scores:
            # Return None — not NEUTRAL — so we don't overwrite real detected emotions
            return None
            
        # Return highest scoring mood
        return max(scores, key=scores.get)
        
    def _normalize_mood(self, detected) -> UserMood:
        """Normalize detected mood to UserMood enum.
        
        'detected' can be:
          - A string like 'happy'
          - An EmotionResult object with .emotion attribute
          - An EmotionState enum value
        """
        # Handle EmotionResult object from emotion_detector.detect()
        if hasattr(detected, 'emotion'):
            # It's an EmotionResult — get the emotion enum value
            detected = detected.emotion
        
        # Handle enum (EmotionState) — get its string value
        if hasattr(detected, 'value'):
            detected = detected.value
        
        # Now it should be a string
        if not isinstance(detected, str):
            return UserMood.NEUTRAL
            
        detected_lower = detected.lower()
        
        mood_map = {
            "happy": UserMood.HAPPY,
            "joy": UserMood.HAPPY,
            "excited": UserMood.EXCITED,
            "sad": UserMood.SAD,
            "sadness": UserMood.SAD,
            "angry": UserMood.ANGRY,
            "anger": UserMood.ANGRY,
            "frustrated": UserMood.FRUSTRATED,
            "frustration": UserMood.FRUSTRATED,
            "tired": UserMood.TIRED,
            "fatigue": UserMood.TIRED,
            "neutral": UserMood.NEUTRAL,
            "calm": UserMood.CALM,
            "rushed": UserMood.FRUSTRATED,  # Map rushed to closest available
            "confused": UserMood.NEUTRAL,    # No direct mapping
        }
        
        return mood_map.get(detected_lower, UserMood.NEUTRAL)
        
    def get_current_mood(self) -> UserMood:
        """Get current user mood from state"""
        return self.state.get().user_mood


# Singleton
_router = None

def get_emotion_router(state_manager: StateManager = None, 
                       emotion_detector=None) -> EmotionRouter:
    global _router
    if _router is None:
        from .state_manager import get_state_manager
        state_manager = state_manager or get_state_manager()
        _router = EmotionRouter(state_manager, emotion_detector)
    return _router
