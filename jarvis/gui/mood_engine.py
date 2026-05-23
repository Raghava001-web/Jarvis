"""
JARVIS Mood Engine
==================
Extracted from websocket_server.py — emotion state machine, mood detection,
response adaptation, and text-processing utilities.

All functions are pure (no WebSocket state dependency).
"""

import re
import time
from typing import Dict, Any, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# EMOTION STATE MACHINE - Proper state transitions for JARVIS mood
# ═══════════════════════════════════════════════════════════════════════════════

class EmotionState:
    """JARVIS emotion states - affects response style and HUD orb color"""
    NEUTRAL = "NEUTRAL"       # Cyan orb
    HAPPY = "HAPPY"           # Green orb
    FOCUSED = "FOCUSED"       # Bright blue orb
    CONCERNED = "CONCERNED"   # Orange orb
    FRUSTRATED = "FRUSTRATED" # Red orb
    TIRED = "TIRED"           # Dim blue orb
    ALERT = "ALERT"           # Flashing orange orb


class EmotionStateMachine:
    """Manages JARVIS emotion state transitions
    
    Inputs weighted: Face=40%, Voice=30%, Text=20%, Context=10%
    """
    
    # Transition triggers: (current_state, trigger) -> new_state
    TRANSITIONS = {
        # From NEUTRAL
        (EmotionState.NEUTRAL, "polite"): EmotionState.HAPPY,
        (EmotionState.NEUTRAL, "complex_task"): EmotionState.FOCUSED,
        (EmotionState.NEUTRAL, "repeat_command"): EmotionState.CONCERNED,
        (EmotionState.NEUTRAL, "angry_tone"): EmotionState.FRUSTRATED,
        (EmotionState.NEUTRAL, "late_night"): EmotionState.TIRED,
        (EmotionState.NEUTRAL, "urgent"): EmotionState.ALERT,
        # From HAPPY
        (EmotionState.HAPPY, "task_complete"): EmotionState.NEUTRAL,
        (EmotionState.HAPPY, "error"): EmotionState.CONCERNED,
        (EmotionState.HAPPY, "angry_tone"): EmotionState.CONCERNED,
        # From FOCUSED
        (EmotionState.FOCUSED, "task_complete"): EmotionState.NEUTRAL,
        (EmotionState.FOCUSED, "task_success"): EmotionState.HAPPY,
        (EmotionState.FOCUSED, "error"): EmotionState.CONCERNED,
        # From CONCERNED
        (EmotionState.CONCERNED, "resolved"): EmotionState.NEUTRAL,
        (EmotionState.CONCERNED, "angry_tone"): EmotionState.FRUSTRATED,
        (EmotionState.CONCERNED, "task_success"): EmotionState.HAPPY,
        # From FRUSTRATED
        (EmotionState.FRUSTRATED, "calm_down"): EmotionState.NEUTRAL,
        (EmotionState.FRUSTRATED, "repeat_angry"): EmotionState.ALERT,
        (EmotionState.FRUSTRATED, "resolved"): EmotionState.CONCERNED,
        # From TIRED
        (EmotionState.TIRED, "morning"): EmotionState.NEUTRAL,
        (EmotionState.TIRED, "urgent"): EmotionState.ALERT,
        # From ALERT
        (EmotionState.ALERT, "resolved"): EmotionState.NEUTRAL,
        (EmotionState.ALERT, "calm_down"): EmotionState.CONCERNED,
    }
    
    # Orb colors for HUD
    ORB_COLORS = {
        EmotionState.NEUTRAL: "cyan",
        EmotionState.HAPPY: "green",
        EmotionState.FOCUSED: "bright-blue",
        EmotionState.CONCERNED: "orange",
        EmotionState.FRUSTRATED: "red",
        EmotionState.TIRED: "dim-blue",
        EmotionState.ALERT: "flashing-orange",
    }
    
    def __init__(self):
        self.state = EmotionState.NEUTRAL
        self.state_history = []
        self.last_transition_time = time.time()
        
    def transition(self, trigger: str) -> str:
        """Attempt state transition based on trigger"""
        key = (self.state, trigger)
        if key in self.TRANSITIONS:
            old_state = self.state
            self.state = self.TRANSITIONS[key]
            self.state_history.append((old_state, trigger, self.state))
            self.last_transition_time = time.time()
        return self.state
    
    def compute_from_inputs(self, face_emotion: str = None, text_sentiment: str = None,
                            context: str = None) -> str:
        """Compute emotion state from multimodal inputs"""
        trigger = None
        
        # Face emotion (40% weight)
        if face_emotion:
            f = face_emotion.lower()
            if f in ("angry", "frustrated"): trigger = "angry_tone"
            elif f == "happy": trigger = "polite"
        
        # Text sentiment (20% weight)
        if text_sentiment:
            s = text_sentiment.lower()
            if "angry" in s or "frustrated" in s: trigger = "angry_tone"
            elif "thanks" in s or "great" in s: trigger = "polite"
            elif "urgent" in s: trigger = "urgent"
        
        # Context - time of day (10% weight)
        if context == "check_time":
            import datetime
            hour = datetime.datetime.now().hour
            if 23 <= hour or hour < 5: trigger = trigger or "late_night"
            elif 5 <= hour < 8: trigger = trigger or "morning"
        
        if trigger:
            self.transition(trigger)
        return self.state
    
    def get_orb_color(self) -> str:
        return self.ORB_COLORS.get(self.state, "cyan")
    
    def get_response_style(self) -> Dict[str, Any]:
        """JARVIS response style based on emotion"""
        return {
            EmotionState.NEUTRAL: {"tone": "professional", "sarcasm": 0.3, "speed": 1.0},
            EmotionState.HAPPY: {"tone": "witty", "sarcasm": 0.5, "speed": 1.1},
            EmotionState.FOCUSED: {"tone": "precise", "sarcasm": 0.0, "speed": 1.0},
            EmotionState.CONCERNED: {"tone": "gentle", "sarcasm": 0.0, "speed": 0.9},
            EmotionState.FRUSTRATED: {"tone": "calm", "sarcasm": 0.0, "speed": 0.8},
            EmotionState.TIRED: {"tone": "brief", "sarcasm": 0.1, "speed": 0.85},
            EmotionState.ALERT: {"tone": "urgent", "sarcasm": 0.0, "speed": 1.2},
        }.get(self.state, {"tone": "professional", "sarcasm": 0.3, "speed": 1.0})
    
    def trigger(self, trigger_name: str) -> str:
        """Alias for transition() - trigger a state change"""
        return self.transition(trigger_name)
    
    def reset(self):
        """Reset to neutral state"""
        self.state = EmotionState.NEUTRAL
        self.state_history = []
        self.last_transition_time = time.time()


# ═══════════════════════════════════════════════════════════════════════════════
# MOOD DETECTION — keyword + face + emotion detector fusion
# ═══════════════════════════════════════════════════════════════════════════════

def detect_mood_from_text(text: str, emotion_enabled: bool = False,
                          emotion_detector=None) -> str:
    """Detect user's mood from voice text + camera face analysis (combined).
    
    Args:
        text: User input text
        emotion_enabled: Whether face-based emotion detection is active
        emotion_detector: Emotion detector instance (optional)
    
    Returns:
        Mood string: 'neutral', 'angry', 'rushed', 'tired', 'happy', 'sad', 'confused'
    """
    text_lower = text.lower()
    
    # ═══════════════════════════════════════════════════════════════
    # VOICE-BASED MOOD DETECTION (Keywords)
    # ═══════════════════════════════════════════════════════════════
    
    # Frustration/Anger keywords
    frustration_words = [
        'again', 'why', 'annoying', 'frustrated', 'irritating', 'damn', 
        'ugh', 'stupid', 'hate', 'ridiculous', 'seriously', "can't believe",
        'what the', 'wtf', 'come on', 'not working', 'broken', 'failed',
        'fuck', 'shit', 'dumb', 'idiot', 'crap', 'bullshit', 'pissed',
        'sucks', 'terrible', 'horrible', 'useless', 'trash', 'worst',
        'stfu', 'tf', 'dumb fuck', 'crashing out', 'ass'
    ]
    
    # Rushed/Hurry keywords — m-04: removed 'now' (too common, triggers false positives)
    rushed_words = [
        'hurry', 'quick', 'fast', 'asap', 'urgent', 'immediately',
        'right now', 'quickly', 'rush', "don't have time", 'late'
    ]
    
    # Tired keywords
    tired_words = [
        'tired', 'exhausted', 'sleepy', 'worn out', 'drained', 'need rest',
        'so tired', 'long day', 'yawn'
    ]
    
    # Happy/Excited keywords
    happy_words = [
        'great', 'awesome', 'amazing', 'love', 'fantastic', 'wonderful',
        'excellent', 'perfect', 'happy', 'excited', 'yes', 'nice', 'cool'
    ]
    
    # Sad keywords
    sad_words = [
        'sad', 'upset', 'depressed', 'down', 'unhappy', 'miserable',
        'crying', 'hurt', 'lonely', 'miss'
    ]
    
    # Confused keywords — ONLY genuine confusion, not normal questions
    confused_words = [
        'confused', "don't understand", "don't get it", 'makes no sense',
        'unclear', "i'm lost", 'what do you mean', 'huh',
    ]
    
    # Count voice keyword matches
    voice_scores = {
        'angry': sum(1 for w in frustration_words if w in text_lower),
        'rushed': sum(1 for w in rushed_words if w in text_lower),
        'tired': sum(1 for w in tired_words if w in text_lower),
        'happy': sum(1 for w in happy_words if w in text_lower),
        'sad': sum(1 for w in sad_words if w in text_lower),
        'confused': sum(1 for w in confused_words if w in text_lower)
    }
    
    # ═══════════════════════════════════════════════════════════════
    # FACE-BASED MOOD DETECTION (Camera)
    # ═══════════════════════════════════════════════════════════════
    
    face_emotion = None
    camera_frame = None
    
    # Capture camera frame for face emotion (if emotion_enabled)
    if emotion_enabled and emotion_detector:
        try:
            try:
                from jarvis.core.shared_camera import get_shared_camera
            except ImportError:
                from core.shared_camera import get_shared_camera
            
            shared_cam = get_shared_camera()
            shared_cam.register("emotion")  # Register if not already
            camera_frame = shared_cam.get_frame()
            if camera_frame is not None:
                print("[MoodEngine] Camera frame from shared camera for mood detection")
        except Exception as e:
            print(f"[MoodEngine] Camera capture error: {e}")
    
    # Use combined emotion detector (voice + face)
    if emotion_detector:
        try:
            result = emotion_detector.detect(text=text, camera_frame=camera_frame)
            if result:
                detected = result.emotion.value
                confidence = result.confidence
                
                # Log detection sources
                sources = []
                if result.voice_emotion and result.voice_emotion.value != 'neutral':
                    sources.append(f"voice:{result.voice_emotion.value}")
                if result.face_emotion and result.face_emotion.value != 'neutral':
                    sources.append(f"face:{result.face_emotion.value}")
                
                if sources:
                    print(f"[MoodEngine] Mood detected: {detected} (confidence: {confidence:.0%}) from {', '.join(sources)}")
                
                if detected != 'neutral':
                    # Face emotion has 60% weight, voice 40%
                    return detected
        except Exception as e:
            print(f"[MoodEngine] Emotion detection error: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # FALLBACK: Use keyword scores only
    # ═══════════════════════════════════════════════════════════════
    
    max_score = max(voice_scores.values())
    if max_score > 0:
        for mood, score in voice_scores.items():
            if score == max_score:
                return mood
    
    return 'neutral'


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE ADAPTATION — tone/rate adjustments based on detected mood
# ═══════════════════════════════════════════════════════════════════════════════

def adapt_response_to_mood(response: str, mood: str, title: str = "sir",
                           perception=None, hud_perception=None,
                           jarvis=None) -> str:
    """Adapt response tone based on user's detected mood.
    
    IMPORTANT: No scripted prefixes/suffixes. The LLM personality prompt
    handles tone naturally. We only adjust speech rate and volume here.
    
    Args:
        response: The response text to adapt
        mood: Detected mood string
        title: User title ('sir', 'mam', etc.)
        perception: Perception layer instance (optional, for speech params)
        hud_perception: HUD perception instance (optional, for speech params)
        jarvis: JARVISUltimate instance (optional, for speech params)
    """
    if mood == 'neutral':
        return response
    
    # Only speech style parameters — NO text prefixes/suffixes
    # Those sounded scripted and annoying ("I'm here for you", "Does that help?")
    mood_speech_styles = {
        'angry': {
            'speech_rate': 190,    # Direct, no BS
            'speech_volume': 0.85,
        },
        'rushed': {
            'speech_rate': 210,    # Fast
            'speech_volume': 0.9,
        },
        'tired': {
            'speech_rate': 155,    # Soothing
            'speech_volume': 0.7,
        },
        'sad': {
            'speech_rate': 155,    # Gentle
            'speech_volume': 0.75,
        },
        'happy': {
            'speech_rate': 185,    # Energetic
            'speech_volume': 0.95,
        },
        'confused': {
            'speech_rate': 160,    # Clear
            'speech_volume': 0.9,
        }
    }
    
    style = mood_speech_styles.get(mood, {})
    
    # Apply TTS style changes based on emotion
    speech_rate = style.get('speech_rate', 175)
    speech_volume = style.get('speech_volume', 0.9)
    
    # Update perception layer speech parameters
    if perception and hasattr(perception, 'speech_rate'):
        perception.speech_rate = speech_rate
        perception.speech_volume = speech_volume
    if hud_perception and hasattr(hud_perception, 'speech_rate'):
        hud_perception.speech_rate = speech_rate
        hud_perception.speech_volume = speech_volume
    if jarvis and hasattr(jarvis, 'perception'):
        jarvis.perception.speech_rate = speech_rate
        jarvis.perception.speech_volume = speech_volume
    
    # For rushed users, shorten the response
    if mood == 'rushed':
        # Take only first sentence or first 50 chars
        if '.' in response[:80]:
            response = response.split('.')[0] + '.'
        elif len(response) > 60:
            response = response[:60].rsplit(' ', 1)[0] + '...'
    
    # NO prefix/suffix injection — return response as-is
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT UTILITIES — sir reduction, action inference
# ═══════════════════════════════════════════════════════════════════════════════

# Counter for sir usage — shared across all responses
_sir_counter = 0


def reduce_sir_usage(response: str, title: str = "sir") -> str:
    """Remove excess 'sir'/'mam' from responses.
    
    JARVIS says sir/mam in almost every response — irritating.
    This keeps it to roughly every 3rd response for natural feel.
    """
    global _sir_counter
    
    # Count occurrences of title in this response
    pattern = re.compile(rf'\b{title}\b', re.IGNORECASE)
    matches = list(pattern.finditer(response))
    
    if not matches:
        return response
    
    # Increment global counter
    _sir_counter += 1
    
    # Keep title only every 3rd response
    if _sir_counter % 3 != 0:
        # Strip all occurrences of ", sir" / ", mam" / " sir." etc
        result = response
        # Remove patterns like ", sir." / ", sir," / ", sir!" / " sir."
        result = re.sub(rf',?\s*{title}\.', '.', result, flags=re.IGNORECASE)
        result = re.sub(rf',?\s*{title},', ',', result, flags=re.IGNORECASE)
        result = re.sub(rf',?\s*{title}!', '!', result, flags=re.IGNORECASE)
        result = re.sub(rf',?\s*{title}\s*$', '', result, flags=re.IGNORECASE)
        # Leading "Sir, " at start
        result = re.sub(rf'^{title},?\s+', '', result, flags=re.IGNORECASE)
        # Clean up double spaces/punctuation
        result = re.sub(r'\s{2,}', ' ', result).strip()
        result = re.sub(r'\.\s*\.', '.', result)
        if result:
            return result
    
    # On the 3rd response, keep exactly one sir (the last one)
    if len(matches) > 1:
        # Keep only the last match
        result = response
        for m in reversed(matches[:-1]):
            # Remove this occurrence
            before = result[:m.start()]
            after = result[m.end():]
            # Clean up surrounding punctuation
            before = before.rstrip(', ')
            after = after.lstrip(', ')
            result = before + ' ' + after
        result = re.sub(r'\s{2,}', ' ', result).strip()
        return result
    
    return response


def infer_action_from_text(text: str) -> str:
    """Infer action/intent from user input text - maps to result.action
    
    This provides a quick intent classification for the result type.
    More sophisticated intent recognition should be in JARVISUltimate.
    """
    t = text.lower()
    
    # Music actions
    if any(w in t for w in ['play music', 'play song', 'play my', 'next track', 'previous track']):
        return 'play_music'
    if any(w in t for w in ['shutdown', 'shut down', 'shut yourself', 'power off', 'go offline', 'exit jarvis', 'quit jarvis']):
        return 'shutdown'
    if any(w in t for w in ['story', 'bedtime', 'tell me a tale', 'once upon']):
        return 'general_ai'
    if any(w in t for w in ['next', 'skip']):
        return 'next_track'
    if any(w in t for w in ['previous', 'back', 'last']):
        return 'previous_track'
    if any(w in t for w in ['pause', 'stop music', 'stop playing']):
        return 'pause_music'
    if any(w in t for w in ['volume up', 'louder', 'increase volume']):
        return 'volume_up'
    if any(w in t for w in ['volume down', 'quieter', 'decrease volume']):
        return 'volume_down'
    
    # System actions
    if any(w in t for w in ['open', 'launch', 'start']):
        return 'open_app'
    if 'screenshot' in t or 'capture' in t:
        return 'screenshot'
    if 'time' in t and 'what' in t:
        return 'get_time'
    if 'weather' in t:
        return 'get_weather'
    if 'news' in t or 'headlines' in t:
        return 'get_news'
    
    # Communication
    if 'message' in t or 'whatsapp' in t or 'text' in t:
        return 'send_message'
    if 'email' in t or 'mail' in t:
        return 'check_email'
    if 'calendar' in t or 'schedule' in t or 'meeting' in t:
        return 'calendar'
    
    # Tasks/Reminders
    if any(w in t for w in ['remind', 'reminder', 'alarm']):
        return 'set_reminder'
    if any(w in t for w in ['task', 'todo', 'to do']):
        return 'manage_task'
    
    # General
    if any(w in t for w in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'good night']):
        return 'greeting'
    if any(w in t for w in ['thank', 'thanks']):
        return 'gratitude'
    
    return 'general_query'
