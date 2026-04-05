"""
Perception Layer - Speech Recognition & Text-to-Speech
Enhanced with JARVIS/FRIDAY voice switching, emotion-adaptive speech, and interruptible TTS
Integrated with StateManager for proper state transitions

TTS Priority: Edge TTS (natural voices) > pyttsx3 (instant fallback)
STT Priority: Google STT (real-time) with Whisper available for file transcription
"""
import speech_recognition as sr
import pyttsx3
import threading
import json
import os
from pathlib import Path
from typing import Optional, Callable
from enum import Enum

# Import StateManager for state transitions
try:
    from core.state_manager import StateManager, JARVISState, get_state_manager
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    STATE_MANAGER_AVAILABLE = False

# Import Voice Engine for Edge TTS
try:
    from core.voice_engine import VoiceEngine, get_voice_engine
    VOICE_ENGINE_AVAILABLE = True
except ImportError:
    VOICE_ENGINE_AVAILABLE = False


class VoiceAssistant(Enum):
    """Voice assistant identities"""
    JARVIS = "jarvis"
    FRIDAY = "friday"


class PerceptionLayer:
    """Handles all speech input/output with voice switching and interruption support"""

    def __init__(self, state_manager: 'StateManager' = None):
        print("[PERCEPTION] Initializing Perception Layer...")
        
        # StateManager for state transitions
        self._state_manager = state_manager
        self._authority_token = "perception_layer"
        if self._state_manager is None and STATE_MANAGER_AVAILABLE:
            try:
                self._state_manager = get_state_manager()
            except:
                pass

        # ━━━ Voice Engine (Edge TTS - natural voices) ━━━
        self._voice_engine = None
        if VOICE_ENGINE_AVAILABLE:
            try:
                self._voice_engine = get_voice_engine()
                print(f"[PERCEPTION] Edge TTS: {'Active' if self._voice_engine.has_edge_tts else 'Unavailable'}")
            except Exception as e:
                print(f"[PERCEPTION] Voice Engine init error: {e}")

        # Speech Recognition setup
        self.recognizer = sr.Recognizer()
        
        # Tuned for natural speech (not cutting off mid-sentence)
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 2.5      # Wait 2.5s of silence before ending (was 1.0)
        self.recognizer.phrase_threshold = 0.5      # Need 0.5s of speech to start (was 0.3)
        self.recognizer.non_speaking_duration = 0.8  # Ignore gaps < 0.8s (was 0.5)
        
        # Mic muting — prevents TTS echo feedback loop
        self.mic_muted = False
        self._ambient_calibrated = False
        
        # Track consecutive failures
        self.consecutive_failures = 0
        
        # User title (sir/mam) - default to sir, can be changed
        self.user_title = "sir"
        self.gender_detected = False

        # Voice assistant identity (JARVIS or FRIDAY)
        self.current_assistant = VoiceAssistant.JARVIS
        self.assistant_name = "JARVIS"
        
        # Available voices (pyttsx3 fallback)
        self.male_voice_id = None
        self.female_voice_id = None
        self._discover_voices()
        
        # Speech settings
        self.speech_rate = 200  # Snappy, not laggy (was 175)
        self.speech_volume = 0.9
        
        # Interruptible speech
        self.is_speaking = False
        self.stop_speaking_flag = False
        self.speaking_thread = None
        self.pending_interrupt_command = None
        
        # Preferences file
        self.prefs_path = Path(__file__).parent.parent / "data" / "voice_prefs.json"
        self._load_preferences()

        tts_mode = "Edge TTS" if (self._voice_engine and self._voice_engine.has_edge_tts) else "pyttsx3"
        print(f"[PERCEPTION] {self.assistant_name} Ready | TTS: {tts_mode} | StateManager: {'Connected' if self._state_manager else 'Standalone'}")

    def _discover_voices(self):
        """Discover available male and female voices"""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            for voice in voices:
                name_lower = voice.name.lower()
                # Common patterns for male/female voices
                if any(m in name_lower for m in ['david', 'mark', 'male', 'guy']):
                    if not self.male_voice_id:
                        self.male_voice_id = voice.id
                        print(f"[PERCEPTION] Male voice: {voice.name}")
                elif any(f in name_lower for f in ['zira', 'hazel', 'female', 'woman', 'sabina']):
                    if not self.female_voice_id:
                        self.female_voice_id = voice.id
                        print(f"[PERCEPTION] Female voice: {voice.name}")
            
            # Fallback: use first two voices
            if not self.male_voice_id and len(voices) > 0:
                self.male_voice_id = voices[0].id
            if not self.female_voice_id and len(voices) > 1:
                self.female_voice_id = voices[1].id
            elif not self.female_voice_id:
                self.female_voice_id = self.male_voice_id
            
            engine.stop()
            del engine
        except Exception as e:
            print(f"[PERCEPTION] Voice discovery error: {e}")

    def _load_preferences(self):
        """Load voice preferences from file"""
        try:
            if self.prefs_path.exists():
                with open(self.prefs_path, 'r') as f:
                    prefs = json.load(f)
                    
                    if prefs.get("assistant") == "friday":
                        self.current_assistant = VoiceAssistant.FRIDAY
                        self.assistant_name = "FRIDAY"
                    
                    self.speech_rate = prefs.get("rate", 175)
                    self.speech_volume = prefs.get("volume", 0.9)
        except Exception as e:
            print(f"[PERCEPTION] Could not load preferences: {e}")

    def _save_preferences(self):
        """Save voice preferences to file"""
        try:
            self.prefs_path.parent.mkdir(parents=True, exist_ok=True)
            prefs = {
                "assistant": self.current_assistant.value,
                "rate": self.speech_rate,
                "volume": self.speech_volume
            }
            with open(self.prefs_path, 'w') as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"[PERCEPTION] Could not save preferences: {e}")

    def switch_to_jarvis(self):
        """Switch to JARVIS (male voice)"""
        self.current_assistant = VoiceAssistant.JARVIS
        self.assistant_name = "JARVIS"
        if self._voice_engine:
            self._voice_engine.set_voice("jarvis")
        self._save_preferences()
        self.speak("JARVIS at your service, sir.")
        print("[PERCEPTION] Switched to JARVIS")

    def switch_to_friday(self):
        """Switch to FRIDAY (female voice)"""
        self.current_assistant = VoiceAssistant.FRIDAY
        self.assistant_name = "FRIDAY"
        if self._voice_engine:
            self._voice_engine.set_voice("friday")
        self._save_preferences()
        self.speak("FRIDAY online. How may I assist you?")
        print("[PERCEPTION] Switched to FRIDAY")

    def switch_voice(self, assistant_name: str):
        """Switch between JARVIS and FRIDAY"""
        if assistant_name.lower() == "friday":
            self.switch_to_friday()
        else:
            self.switch_to_jarvis()

    def get_wake_words(self) -> list:
        """Return wake words for current assistant"""
        if self.current_assistant == VoiceAssistant.FRIDAY:
            return ["friday", "hey friday", "ok friday"]
        return ["jarvis", "hey jarvis", "ok jarvis"]

    def set_user_gender(self, gender: str):
        """Set user gender for proper address"""
        if gender.lower() in ["male", "m", "man", "boy"]:
            self.user_title = "sir"
        elif gender.lower() in ["female", "f", "woman", "girl", "mam", "madam"]:
            self.user_title = "mam"
        self.gender_detected = True
        print(f"[PERCEPTION] User title set to: {self.user_title}")

    def _get_current_voice_id(self) -> str:
        """Get voice ID for current assistant"""
        if self.current_assistant == VoiceAssistant.FRIDAY:
            return self.female_voice_id
        return self.male_voice_id

    def speak(self, text: str, rate: int = None, volume: float = None):
        """Speak text using TTS with interruption support"""
        # Use provided or default settings
        speech_rate = rate or self.speech_rate
        speech_volume = volume or self.speech_volume
        
        # If already speaking, stop and queue new speech
        if self.is_speaking:
            self.stop_speaking()
        
        # Run speech in thread for potential interruption
        self.speaking_thread = threading.Thread(
            target=self._speak_threaded,
            args=(text, speech_rate, speech_volume),
            daemon=True
        )
        self.speaking_thread.start()

    def _speak_threaded(self, text: str, rate: int, volume: float):
        """Internal threaded speech function with mic muting to prevent echo.
        
        Uses Edge TTS (natural voice) if available, pyttsx3 as fallback.
        """
        self.is_speaking = True
        self.stop_speaking_flag = False
        
        # ━━━ MUTE MIC WHILE SPEAKING (prevents TTS echo) ━━━
        self.mic_muted = True
        
        # Transition to SPEAKING state
        if self._state_manager and STATE_MANAGER_AVAILABLE:
            self._state_manager.update_context(
                self._authority_token,
                speaking_text=text
            )
        
        try:
            print(f"{self.assistant_name}: {text}")
            
            # ━━━ TRY EDGE TTS FIRST (natural voice) ━━━
            edge_used = False
            if self._voice_engine and self._voice_engine.has_edge_tts:
                try:
                    self._voice_engine.set_rate(rate)
                    self._voice_engine.set_volume(volume)
                    edge_used = self._voice_engine.speak(text)
                except Exception as e:
                    print(f"[PERCEPTION] Edge TTS failed, falling back to pyttsx3: {e}")
                    edge_used = False
            
            # ━━━ PYTTSX3 FALLBACK ━━━
            if not edge_used:
                engine = pyttsx3.init()
                engine.setProperty('rate', rate)
                engine.setProperty('volume', volume)
                
                # Set voice based on current assistant
                voice_id = self._get_current_voice_id()
                if voice_id:
                    engine.setProperty('voice', voice_id)
                
                # Connect to check for stop flag
                def on_word(name, location, length):
                    if self.stop_speaking_flag:
                        engine.stop()
                
                engine.connect('started-word', on_word)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                del engine
        except Exception as e:
            print(f"ERROR - Speech error: {e}")
        finally:
            self.is_speaking = False
            # Wait for echo to fade before unmuting mic
            import time
            time.sleep(0.8)
            self.mic_muted = False

    def stop_speaking(self):
        """Stop current speech immediately"""
        self.stop_speaking_flag = True
        # Stop Edge TTS playback if active
        if self._voice_engine:
            self._voice_engine.stop()
        if self.speaking_thread and self.speaking_thread.is_alive():
            # Give it a moment to stop
            self.speaking_thread.join(timeout=0.5)
        self.is_speaking = False

    def speak_with_interrupt_check(self, text: str, on_interrupt: Callable = None) -> Optional[str]:
        """Speak while checking for interruptions
        
        Returns the interruption command if detected, None otherwise
        """
        # Start speaking in background
        self.speak(text)
        
        # Listen for potential interrupt while speaking
        while self.is_speaking:
            # Quick listen for wake word
            interrupt = self._quick_listen_for_wake_word()
            if interrupt:
                self.stop_speaking()
                if on_interrupt:
                    on_interrupt()
                return interrupt
        
        return None

    def _quick_listen_for_wake_word(self, timeout: float = 0.5) -> Optional[str]:
        """Quick listen for wake word during speech"""
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=3
                )
                text = self.recognizer.recognize_google(audio).lower()
                
                # Check for wake word
                wake_words = self.get_wake_words()
                for wake_word in wake_words:
                    if wake_word in text:
                        # Extract command after wake word
                        parts = text.split(wake_word, 1)
                        if len(parts) > 1 and parts[1].strip():
                            return parts[1].strip()
                        return text
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            pass
        except Exception as e:
            pass
        
        return None

    def speak_adaptive(self, text: str, emotion: str = None):
        """Speak with emotion-adaptive settings
        
        Adjusts rate and volume based on detected user emotion
        """
        # Emotion-based adjustments
        settings = {
            "angry": {"rate": 190, "volume": 0.9},
            "rushed": {"rate": 195, "volume": 0.9},
            "sad": {"rate": 145, "volume": 0.65},
            "tired": {"rate": 140, "volume": 0.6},
            "calm": {"rate": 155, "volume": 0.75},
            "happy": {"rate": 175, "volume": 0.85},
            "confused": {"rate": 155, "volume": 0.8},
            "neutral": {"rate": 175, "volume": 0.9}
        }
        
        config = settings.get(emotion, settings["neutral"])
        self.speak(text, rate=config["rate"], volume=config["volume"])

    def listen(self, timeout: int = 10) -> Optional[str]:
        """Listen and return text (skips if mic is muted during TTS)"""
        # ━━━ SKIP IF MIC MUTED (JARVIS is speaking) ━━━
        if self.mic_muted or self.is_speaking:
            import time
            time.sleep(0.3)
            return None
        
        try:
            with sr.Microphone() as source:
                print("[LISTENING] Listening...")
                
                # Update context
                if self._state_manager and STATE_MANAGER_AVAILABLE:
                    self._state_manager.update_context(
                        self._authority_token,
                        listening_duration=float(timeout)
                    )
                
                # Calibrate ambient noise ONCE, not every call
                if not self._ambient_calibrated:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                    self._ambient_calibrated = True
                    print("[PERCEPTION] Ambient noise calibrated")
                
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
                
                # Double-check mic wasn't muted while we were listening
                if self.mic_muted:
                    return None
                
                print("[PROCESSING] Processing...")
                text = self.recognizer.recognize_google(audio)
                user_input = text.lower().strip()
                
                # ━━━ SPEECH CORRECTION: Fix common Google misrecognitions ━━━
                user_input = self._correct_speech(user_input)
                
                print(f"YOU: {user_input}")
                
                # Update context with command
                if self._state_manager and STATE_MANAGER_AVAILABLE:
                    self._state_manager.update_context(
                        self._authority_token,
                        last_command=user_input
                    )
                
                self.consecutive_failures = 0
                return user_input
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("[INFO] Could not understand audio, waiting for retry...")
            return None
        except sr.RequestError as e:
            self.speak(f"Speech service unavailable, {self.user_title}. Check internet connection.")
            print(f"ERROR: Google Speech API error: {e}")
            return None
        except Exception as e:
            print(f"ERROR: {e}")
            return None

    def ask_gender(self):
        """Ask user for gender preference"""
        self.speak("Should I address you as sir or mam?")
        response = self.listen(timeout=10)
        if response:
            if any(word in response for word in ["sir", "male", "man", "boy"]):
                self.set_user_gender("male")
                self.speak("Understood, sir.")
            elif any(word in response for word in ["mam", "madam", "female", "woman", "girl"]):
                self.set_user_gender("female")
                self.speak("Understood, mam.")
            else:
                self.speak("I'll address you as sir by default.")
                self.user_title = "sir"

    def set_speech_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        self.speech_rate = max(100, min(300, rate))
        self._save_preferences()

    def set_speech_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0)"""
        self.speech_volume = max(0.0, min(1.0, volume))
        self._save_preferences()
    def _correct_speech(self, text: str) -> str:
        """Post-process speech recognition to fix common Google misrecognitions.
        
        Google Speech API often mishears technical terms, app names, and 
        uncommon words. This corrects the most common errors.
        """
        # Common misrecognitions → correct forms
        corrections = {
            # Geopolitics and similar
            'jio politics': 'geopolitics',
            'geo politics': 'geopolitics',
            'jio political': 'geopolitical',
            
            # App names
            'para plexity': 'perplexity',
            'perplexed city': 'perplexity',
            'perplex city': 'perplexity',
            'visual studio code': 'vs code',
            'fire fox': 'firefox',
            'file manager': 'file explorer',
            
            # YouTube misrecognitions
            'you to': 'youtube',
            'you tube': 'youtube',
            'you too': 'youtube',
            
            # Common truncations / merges
            'open you': 'open youtube',
            'play you': 'play youtube',
            
            # System commands
            'bright ness': 'brightness',
            'volume up': 'increase volume',
            'volume down': 'decrease volume',
            
            # JARVIS himself
            'service': 'jarvis',
            'jar with': 'jarvis',
            'jar vis': 'jarvis',
            'jarrett': 'jarvis',
        }
        
        corrected = text
        for wrong, right in corrections.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, right)
        
        if corrected != text:
            print(f"[PERCEPTION] Speech corrected: '{text}' -> '{corrected}'")
        
        return corrected

    def contains_wake_word(self, text: str) -> bool:
        """Check if text contains wake word for current assistant"""
        text_lower = text.lower()
        wake_words = self.get_wake_words()
        return any(w in text_lower for w in wake_words)

    def extract_after_wake_word(self, text: str) -> str:
        """Extract command after wake word"""
        text_lower = text.lower()
        wake_words = self.get_wake_words()
        
        for wake_word in wake_words:
            if wake_word in text_lower:
                parts = text_lower.split(wake_word, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return text
