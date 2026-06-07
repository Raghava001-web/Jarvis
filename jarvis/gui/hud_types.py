import time
import queue
import threading
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Action:
    """Single response type for all WebSocket responses - prevents loops"""
    type: str                  # SPEAK, UPDATE_UI, UPDATE_CONTEXT, SILENT
    payload: Dict[str, Any]
    
    @staticmethod
    def speak(text: str, speak_aloud: bool = True, mood: str = "neutral") -> 'Action':
        """Create a SPEAK action - the primary response type"""
        return Action("SPEAK", {"text": text, "speak": speak_aloud, "mood": mood})
    
    @staticmethod
    def silent() -> 'Action':
        """Create a SILENT action - no response needed"""
        return Action("SILENT", {})
    
    @staticmethod
    def update_ui(ui_type: str, data: Dict[str, Any]) -> 'Action':
        """Create an UPDATE_UI action for HUD updates"""
        return Action("UPDATE_UI", {"ui_type": ui_type, **data})


class HUDPerception:
    """Custom perception layer that captures speech for HUD display"""
    
    def __init__(self, original_perception=None):
        self.original = original_perception
        self.speech_queue = queue.Queue()
        self.assistant_name = "JARVIS"
        self.user_title = "sir"
        self.is_friday = False
        # Deduplication tracking
        self.last_speech = ""
        self.last_speech_time = 0
        
        if original_perception:
            self.assistant_name = getattr(original_perception, 'assistant_name', 'JARVIS')
            self.user_title = getattr(original_perception, 'user_title', 'sir')
            self.is_friday = self.assistant_name.upper() == 'FRIDAY'
    
    def speak(self, text):
        """Capture speech and add to queue - with deduplication"""
        # Prevent duplicate messages within 2 seconds (must run BEFORE any early return)
        now = time.time()
        if text == self.last_speech and (now - self.last_speech_time) < 2.0:
            # C-07: Safe-encode for non-ASCII console output
            safe = text.encode('ascii', errors='replace').decode()
            print(f"[{self.assistant_name}] (duplicate skipped) {safe[:60]}")
            return
        
        self.last_speech = text
        self.last_speech_time = now
        
        # When Gemini Live Engine is active, it handles ALL audio output.
        # Only log to the speech queue for the Web HUD chat panel, do NOT trigger Edge TTS.
        if getattr(self, '_gemini_live_active', False):
            safe = text.encode('ascii', errors='replace').decode()
            print(f"[{self.assistant_name}] (live mode - TTS skipped) {safe}")
            self.speech_queue.put(text)
            return
        
        safe = text.encode('ascii', errors='replace').decode()
        print(f"[{self.assistant_name}] {safe}")
        self.speech_queue.put(text)
        
        # ━━━ SPEAK OUT LOUD via VoiceEngine (Edge TTS / pyttsx3 fallback) ━━━
        # M-09: Use module-level cached reference instead of importing every call
        try:
            if not hasattr(HUDPerception, '_voice_engine_ref'):
                from core.voice_engine import get_voice_engine
                HUDPerception._voice_engine_ref = get_voice_engine()
            engine = HUDPerception._voice_engine_ref
            
            # Use current assistant name (jarvis/friday) for the voice profile
            voice_key = "friday" if self.is_friday else "jarvis"
            engine.set_voice(voice_key)
            
            # Speak asynchronously so we don't block the WebSocket loop
            threading.Thread(target=engine.speak, args=(text,), daemon=True).start()
        except (ImportError, Exception) as e:
            # Fallback to older perception layer if voice_engine fails
            if self.original and hasattr(self.original, 'speak'):
                try:
                    self.original.speak(text)
                except Exception as e:
                    print(f"[{self.assistant_name}] TTS error: {e}")
    
    def switch_to_friday(self):
        """Switch to FRIDAY voice"""
        self.assistant_name = "FRIDAY"
        self.is_friday = True
        if self.original and hasattr(self.original, 'switch_to_friday'):
            self.original.switch_to_friday()
        self.speak("FRIDAY online. Hello, boss.")
    
    def switch_to_jarvis(self):
        """Switch to JARVIS voice"""
        self.assistant_name = "JARVIS"
        self.is_friday = False
        if self.original and hasattr(self.original, 'switch_to_jarvis'):
            self.original.switch_to_jarvis()
        self.speak("JARVIS back online, sir.")
    
    def get_pending_speech(self):
        """Get all pending speech from queue"""
        messages = []
        while not self.speech_queue.empty():
            try:
                messages.append(self.speech_queue.get_nowait())
            except:
                break
        return messages
