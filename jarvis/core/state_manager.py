"""
State Manager - Central Brain State
====================================
Single source of truth for JARVIS state.
All modules read/write through this.
Includes session management for multi-user handling.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime
from enum import Enum
import uuid


@dataclass
class Session:
    """
    Session for multi-user handling.
    
    Tracks who JARVIS should listen to and provides behavior rules:
    - If detected_faces > 1: Pause and ask "Who should I listen to?"
    - If user_confidence < 0.6: Reduce personalization
    - If new user detected: Create new session or switch
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    primary_user: Optional[str] = None       # Who JARVIS is talking to
    user_confidence: float = 1.0             # How sure are we about user identity
    detected_faces: int = 0                  # Number of faces in view
    session_start: datetime = field(default_factory=datetime.now)
    last_interaction: datetime = field(default_factory=datetime.now)
    is_paused: bool = False                  # Paused due to multi-user conflict
    pause_reason: Optional[str] = None
    
    def should_pause(self) -> bool:
        """
        Check if JARVIS should pause due to multi-user conflict.
        
        SMART PAUSE RULE:
        - If faces > 1 AND no primary user → pause
        - If faces > 1 AND confidence < 0.7 → pause (uncertain who's talking)
        - If faces > 1 BUT primary user AND confidence >= 0.7 → DON'T pause
        
        This prevents annoying pauses when face recognition is confident.
        """
        if self.detected_faces <= 1:
            return False  # Single user or no one - don't pause
            
        # Multiple faces detected
        if not self.primary_user:
            return True  # No primary user set - ask who to listen to
            
        if self.user_confidence < 0.7:
            return True  # Uncertain who's talking - pause
            
        return False  # Primary user set and confident - keep going
    
    def should_reduce_personalization(self) -> bool:
        """Check if we should reduce personalization (uncertain user)"""
        return self.user_confidence < 0.6
    
    def update_interaction(self):
        """Mark that an interaction just happened"""
        self.last_interaction = datetime.now()
    
    def is_stale(self, timeout_seconds: int = 300) -> bool:
        """Check if session is stale (no interaction for a while)"""
        delta = datetime.now() - self.last_interaction
        return delta.total_seconds() > timeout_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Export session to dictionary"""
        return {
            "session_id": self.session_id,
            "primary_user": self.primary_user,
            "user_confidence": self.user_confidence,
            "detected_faces": self.detected_faces,
            "is_paused": self.is_paused,
            "pause_reason": self.pause_reason,
        }


class UserMood(Enum):
    """User emotional states"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    CALM = "calm"
    SAD = "sad"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    TIRED = "tired"


@dataclass
class JARVISState:
    """
    Central state object.
    Every module should read/write to this, not keep its own state.
    """
    # Intent state
    current_intent: Optional[str] = None
    intent_confidence: float = 0.0
    entities: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    current_topic: Optional[str] = None
    last_entity: Optional[str] = None
    active_app: Optional[str] = None
    
    # Conversation
    last_user_input: Optional[str] = None
    last_jarvis_response: Optional[str] = None
    last_action: Optional[str] = None
    
    # User state
    user_mood: UserMood = UserMood.NEUTRAL
    user_name: str = "sir"
    recognized_user: Optional[str] = None
    
    # Vision state (updated by background worker)
    last_gesture: Optional[str] = None
    last_gesture_meta: Dict[str, Any] = field(default_factory=dict)
    last_emotion: Optional[str] = None
    
    # Session
    conversation_turns: int = 0
    session_start: datetime = field(default_factory=datetime.now)
    
    # Flags
    awaiting_clarification: bool = False
    awaiting_confirmation: bool = False
    pending_action: Optional[str] = None


class StateManager:
    """
    Manages the central JARVIS state.
    Thread-safe, observable, with session handling.
    """
    
    def __init__(self):
        print("[STATE] Initializing State Manager...")
        self.state = JARVISState()
        self.session = Session()  # Multi-user session management
        self._observers: List[callable] = []
        print("[STATE] State Manager Ready")
        
    def get(self) -> JARVISState:
        """Get current state (read-only view)"""
        return self.state
    
    def get_session(self) -> Session:
        """Get current session"""
        return self.session
    
    # ═══════════════════════════════════════════════════════════
    # SESSION MANAGEMENT (Multi-user handling)
    # ═══════════════════════════════════════════════════════════
    
    def update_detected_faces(self, count: int, faces: List[str] = None):
        """
        Update detected face count from vision.
        If >1 face detected without primary user, pause and ask.
        """
        self.session.detected_faces = count
        
        if self.session.should_pause():
            self.session.is_paused = True
            self.session.pause_reason = "Multiple faces detected. Who should I listen to?"
            self._notify_observers("session_paused")
        else:
            self.session.is_paused = False
            self.session.pause_reason = None
    
    def switch_user(self, user: str, confidence: float = 1.0):
        """
        Switch to a new user session.
        Creates new session if different user.
        """
        if self.session.primary_user != user:
            # Save old session start time if same user with low confidence
            old_session_id = self.session.session_id
            self.session = Session(
                primary_user=user,
                user_confidence=confidence
            )
            self.state.recognized_user = user
            print(f"[SESSION] Switched from {old_session_id} to {self.session.session_id} (user: {user})")
            self._notify_observers("user_switched")
        else:
            # Same user, just update confidence
            self.session.user_confidence = confidence
            self.session.update_interaction()
    
    def set_primary_user(self, user: str):
        """Set/confirm primary user (voice command: 'Listen to me')"""
        self.session.primary_user = user
        self.session.is_paused = False
        self.session.pause_reason = None
        self.state.recognized_user = user
        self._notify_observers("primary_user_set")
    
    def is_session_active(self) -> bool:
        """Check if there's an active non-stale session"""
        return not self.session.is_stale() and not self.session.is_paused
    
    def should_personalize(self) -> bool:
        """Check if we should use personalization"""
        return not self.session.should_reduce_personalization()
        
    def update_intent(self, intent: Optional[str], confidence: float, 
                      entities: Dict[str, Any] = None):
        """Update intent-related state"""
        self.state.current_intent = intent
        self.state.intent_confidence = confidence
        self.state.entities = entities or {}
        
        # Auto-update topic from intent
        if intent:
            self.state.current_topic = intent.replace("_", " ")
            
        self._notify_observers("intent_updated")
        
    def set_mood(self, mood: str):
        """Update user mood"""
        try:
            self.state.user_mood = UserMood(mood.lower())
        except ValueError:
            self.state.user_mood = UserMood.NEUTRAL
            
    def set_active_app(self, app: str):
        """Track active application"""
        self.state.active_app = app
        
    def set_last_action(self, action: str):
        """Record last action taken"""
        self.state.last_action = action
        
    def set_topic(self, topic: str):
        """Set current conversation topic"""
        self.state.current_topic = topic
        
    def set_last_entity(self, entity: str):
        """Track last mentioned entity (for pronoun resolution)"""
        self.state.last_entity = entity
        
    def record_turn(self, user_input: str, jarvis_response: str):
        """Record a conversation turn"""
        self.state.last_user_input = user_input
        self.state.last_jarvis_response = jarvis_response
        self.state.conversation_turns += 1
    
    def update_context(self, topic: str = None, entity: str = None, **kwargs):
        """Update context state (topic, entity, etc.)"""
        if topic:
            self.state.current_topic = topic
        if entity:
            self.state.last_entity = entity
        # Update any additional fields provided
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self._notify_observers("context_updated")
        
    def set_awaiting_clarification(self, pending: bool, action: str = None):
        """Mark that we're waiting for user clarification"""
        self.state.awaiting_clarification = pending
        self.state.pending_action = action if pending else None
        
    def set_awaiting_confirmation(self, pending: bool, action: str = None):
        """Mark that we're waiting for user confirmation"""
        self.state.awaiting_confirmation = pending
        self.state.pending_action = action if pending else None
        
    def reset_intent(self):
        """Clear intent state after handling"""
        self.state.current_intent = None
        self.state.intent_confidence = 0.0
        self.state.entities = {}
        self.state.awaiting_clarification = False
        self.state.awaiting_confirmation = False
        self.state.pending_action = None
        
    def reset_session(self):
        """Reset for new session"""
        self.state = JARVISState()
        
    # Observer pattern for reactive updates
    def add_observer(self, callback: callable):
        """Add observer for state changes"""
        self._observers.append(callback)
        
    def _notify_observers(self, event: str):
        """Notify all observers of state change"""
        for observer in self._observers:
            try:
                observer(event, self.state)
            except:
                pass
                
    # Vision state updates (called by background worker only)
    def update_gesture(self, gesture: str, meta: Dict = None):
        """Update detected gesture (background worker only)"""
        self.state.last_gesture = gesture
        self.state.last_gesture_meta = meta or {}
        self._notify_observers("gesture_updated")
        
    def update_emotion(self, emotion: str):
        """Update detected emotion (background worker only)"""
        self.state.last_emotion = emotion
        self._notify_observers("emotion_updated")
        
    def update_recognized_user(self, user: str):
        """Update recognized user (background worker only)"""
        self.state.recognized_user = user
        self._notify_observers("user_recognized")
        
    def update_mood(self, mood: UserMood):
        """Update user mood from any source"""
        self.state.user_mood = mood
        self._notify_observers("mood_updated")
                
    def to_dict(self) -> Dict:
        """Export state as dictionary (for UI observation)"""
        return {
            "current_intent": self.state.current_intent,
            "intent_confidence": self.state.intent_confidence,
            "entities": self.state.entities,
            "current_topic": self.state.current_topic,
            "last_entity": self.state.last_entity,
            "active_app": self.state.active_app,
            "user_mood": self.state.user_mood.value,
            "conversation_turns": self.state.conversation_turns,
            # Vision state for UI
            "last_gesture": self.state.last_gesture,
            "last_emotion": self.state.last_emotion,
            "recognized_user": self.state.recognized_user,
        }
        
    def __repr__(self):
        return f"StateManager({self.state})"


# Singleton
_manager = None

def get_state_manager() -> StateManager:
    global _manager
    if _manager is None:
        _manager = StateManager()
    return _manager
