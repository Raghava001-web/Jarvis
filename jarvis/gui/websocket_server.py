"""
JARVIS WebSocket Server - FULL INTEGRATION
Connects Web HUD to JARVISUltimate with ALL features:
- Voice-to-voice conversation
- Dynamic news by category and location
- Gesture recognition
- Face recognition
- Mood/emotion analysis
- Screenshot & OCR
- Dictionary & Email
- Entertainment (stories, jokes, poems)
- Smart Notes & Alarms
- All JARVIS commands
"""

import asyncio
import websockets
import json
import threading
import psutil
import time
from pathlib import Path
from datetime import datetime
import sys
import os
import re

# ═══════════════════════════════════════════════════════════════════
# PATH SETUP: Ensure 'from jarvis.core.X' imports work regardless of CWD
# Adds the project root (parent of jarvis/) to sys.path if needed
# ═══════════════════════════════════════════════════════════════════
_this_dir = os.path.dirname(os.path.abspath(__file__))          # jarvis/gui/
_jarvis_dir = os.path.dirname(_this_dir)                        # jarvis/
_project_root = os.path.dirname(_jarvis_dir)                    # AI_Voice_Assistant/
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _jarvis_dir not in sys.path:
    sys.path.insert(0, _jarvis_dir)
import queue
import base64
from dataclasses import dataclass
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Structured pipeline logger
try:
    from core.logger import get_logger
    jlog = get_logger()
except ImportError:
    jlog = None


# ═══════════════════════════════════════════════════════════════════════════════
# CLEAN GATEWAY ARCHITECTURE - Action Model & State Manager
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# EMOTION STATE MACHINE - Extracted to mood_engine.py
# ═══════════════════════════════════════════════════════════════════════════════

from jarvis.gui.mood_engine import (
    EmotionState,
    EmotionStateMachine,
    detect_mood_from_text as _detect_mood_from_text,
    adapt_response_to_mood as _adapt_response_to_mood,
    reduce_sir_usage as _reduce_sir_usage,
    infer_action_from_text as _infer_action_from_text,
)


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MANAGER - Extracted to state_controller.py
# ═══════════════════════════════════════════════════════════════════════════════

from jarvis.gui.state_controller import UIStateController as StateManager  # C-03: renamed to avoid collision

# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND PROCESSOR - Extracted to command_processor.py
# ═══════════════════════════════════════════════════════════════════════════════

from jarvis.gui.command_processor import split_compound_command as _split_compound_command

# ═══════════════════════════════════════════════════════════════════════════════
# DATA PROVIDERS - Extracted to data_providers.py
# ═══════════════════════════════════════════════════════════════════════════════

from jarvis.gui.data_providers import (
    get_system_stats as _get_system_stats,
    get_weather_data as _get_weather_data,
    get_news_data as _get_news_data,
    maybe_title,
    always_title,
)

# Add parent directories to path for imports (works from any directory)
_project_root = Path(__file__).parent.parent.parent.resolve()
_jarvis_root = Path(__file__).parent.parent.resolve()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_jarvis_root) not in sys.path:
    sys.path.insert(0, str(_jarvis_root))
print(f"[WebSocket] Project root: {_project_root}")

# Load .env file for API keys
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    print(f"[WebSocket] Loaded .env from {env_path}")
except ImportError:
    print("[WebSocket] python-dotenv not installed, using system env vars")


# Feature availability flags
JARVIS_AVAILABLE = False
PERCEPTION_AVAILABLE = False
GESTURE_AVAILABLE = False
FACE_AVAILABLE = False
EMOTION_AVAILABLE = False
NEWS_AVAILABLE = False
WEATHER_AVAILABLE = False
SCREENSHOT_AVAILABLE = False
OCR_AVAILABLE = False
DICTIONARY_AVAILABLE = False
EMAIL_AVAILABLE = False
ENTERTAINMENT_AVAILABLE = False
NOTES_AVAILABLE = False
ALARM_AVAILABLE = False
SYSTEM_CONTROL_AVAILABLE = False
CONTEXT_MEMORY_AVAILABLE = False
SCREEN_CONTROL_AVAILABLE = False

# Try to import JARVISUltimate (the full system)
try:
    from jarvis.core.jarvis_ultimate import JARVISUltimate
    JARVIS_AVAILABLE = True
    print("[WebSocket] JARVISUltimate available - FULL INTEGRATION")
except ImportError as e:
    print(f"[WebSocket] JARVISUltimate not available: {e}")
    JARVIS_AVAILABLE = False

# Import individual components as fallbacks
try:
    from jarvis.core.perception import PerceptionLayer
    PERCEPTION_AVAILABLE = True
except ImportError:
    pass

try:
    from jarvis.core.gesture_controller import GestureController, GestureType
    GESTURE_AVAILABLE = True
    print("[WebSocket] Gesture controller available")
except ImportError:
    pass

try:
    from jarvis.core.face_recognition_auth import FaceRecognition, UserType
    FACE_AVAILABLE = True
    print("[WebSocket] Face recognition available")
except ImportError:
    pass

try:
    from jarvis.core.emotion_detector import EmotionDetector, EmotionState
    EMOTION_AVAILABLE = True
    print("[WebSocket] Emotion detector available")
except ImportError:
    pass

try:
    from jarvis.core.news_handler import NewsHandler
    NEWS_AVAILABLE = True
except ImportError:
    pass

try:
    from jarvis.core.weather_handler import WeatherHandler
    WEATHER_AVAILABLE = True
except ImportError:
    pass

try:
    from jarvis.core.system_status import SystemStatus
    SYSTEM_STATUS_AVAILABLE = True
except ImportError:
    SYSTEM_STATUS_AVAILABLE = False

# NEW IMPORTS - All Missing Features
try:
    from jarvis.core.screenshot_handler import ScreenshotHandler
    SCREENSHOT_AVAILABLE = True
    print("[WebSocket] Screenshot handler available")
except ImportError:
    pass

try:
    from jarvis.core.ocr_handler import OCRHandler
    OCR_AVAILABLE = True
    print("[WebSocket] OCR handler available")
except ImportError:
    pass

try:
    from jarvis.core.dictionary_handler import DictionaryHandler
    DICTIONARY_AVAILABLE = True
    print("[WebSocket] Dictionary handler available")
except ImportError:
    pass

try:
    from jarvis.core.email_handler import EmailHandler
    EMAIL_AVAILABLE = True
    print("[WebSocket] Email handler available")
except ImportError:
    pass

try:
    from jarvis.core.entertainment import JARVISEntertainment
    ENTERTAINMENT_AVAILABLE = True
    print("[WebSocket] Entertainment module available")
except ImportError:
    pass

try:
    from jarvis.core.smart_notes import SmartNotes
    NOTES_AVAILABLE = True
    print("[WebSocket] Smart notes available")
except ImportError:
    pass

try:
    from jarvis.core.alarm_system import AlarmSystem
    ALARM_AVAILABLE = True
    print("[WebSocket] Alarm system available")
except ImportError:
    pass

# Reminder Manager
REMINDER_AVAILABLE = False
try:
    from jarvis.core.reminder_manager import ReminderManager
    REMINDER_AVAILABLE = True
    print("[WebSocket] Reminder manager available")
except ImportError:
    pass

try:
    from jarvis.core.system_control import SystemControl
    SYSTEM_CONTROL_AVAILABLE = True
    print("[WebSocket] System control available")
except ImportError:
    pass

# Knowledge layer for Gemini AI
KNOWLEDGE_AVAILABLE = False
try:
    from jarvis.core.knowledge import KnowledgeLayer
    KNOWLEDGE_AVAILABLE = True
    print("[WebSocket] Knowledge layer (Gemini AI) available")
except ImportError:
    pass

# IntentRouter and handlers for clean command routing
ROUTER_AVAILABLE = False
try:
    from jarvis.core.intent_router import IntentRouter, Intent, HandlerResult
    from jarvis.core.intent_classifier import classify_intent
    from jarvis.core.intent_handlers import HANDLER_MAP
    ROUTER_AVAILABLE = True
    print("[WebSocket] IntentRouter and handlers available")
except ImportError as e:
    print(f"[WebSocket] IntentRouter not available: {e}")

# Context Memory for improved conversational abilities
try:
    from jarvis.core.context_memory import ContextMemory, WorkingMemory
    CONTEXT_MEMORY_AVAILABLE = True
    print("[WebSocket] ContextMemory available - enhanced conversations")
except ImportError:
    pass

# Screen Control for mouse/keyboard automation
try:
    from jarvis.core.screen_control import ScreenControlHandler
    SCREEN_CONTROL_AVAILABLE = True
    print("[WebSocket] Screen control available")
except ImportError:
    pass

# Gemini Live Engine (Mark-XXX Parity)
GEMINI_LIVE_AVAILABLE = False
try:
    from jarvis.core.gemini_live_engine import GeminiLiveEngine
    import os
    if os.getenv("JARVIS_USE_GEMINI_LIVE", "0") == "1" and os.getenv("GEMINI_API_KEY"):
        GEMINI_LIVE_AVAILABLE = True
        print("[WebSocket] Gemini Live Engine available and enabled by .env")
except ImportError as e:
    print(f"[WebSocket] Gemini Live Engine not available: {e}")

# PDF Handler
PDF_AVAILABLE = False
try:
    from jarvis.core.pdf_handler import PDFHandler
    PDF_AVAILABLE = True
    print("[WebSocket] PDF handler available")
except ImportError:
    pass

# Brain Adapter — advanced ML pipeline (intent_model, entity_extractor, decision_engine, etc.)
BRAIN_AVAILABLE = False
try:
    from jarvis.core.brain_adapter import BrainAdapter, get_brain_adapter
    BRAIN_AVAILABLE = True
    print("[WebSocket] Brain Adapter available")
except ImportError as e:
    print(f"[WebSocket] Brain Adapter not available: {e}")

# WhatsApp Handler
WHATSAPP_AVAILABLE = False
try:
    from jarvis.core.whatsapp_handler import WhatsAppHandler
    WHATSAPP_AVAILABLE = True
    print("[WebSocket] WhatsApp handler available")
except ImportError:
    pass

# Calendar Integration
CALENDAR_AVAILABLE = False
try:
    from jarvis.core.calendar_integration import CalendarIntegration
    CALENDAR_AVAILABLE = True
    print("[WebSocket] Calendar integration available")
except ImportError:
    pass

# Sound Effects for stories/notifications
SOUND_EFFECTS_AVAILABLE = False
try:
    from jarvis.core.sound_effects import SoundEffects
    SOUND_EFFECTS_AVAILABLE = True
    print("[WebSocket] Sound effects available")
except ImportError:
    pass

# Proactive Assistant
PROACTIVE_AVAILABLE = False
try:
    from jarvis.core.proactive_assistant import ProactiveAssistant
    PROACTIVE_AVAILABLE = True
    print("[WebSocket] Proactive assistant available")
except ImportError:
    pass

# Email Handler (Gmail)
EMAIL_HANDLER_AVAILABLE = False
try:
    from jarvis.core.email_handler import EmailHandler
    EMAIL_HANDLER_AVAILABLE = True
    print("[WebSocket] Email handler available")
except ImportError:
    pass

# YouTube Downloader
YOUTUBE_AVAILABLE = False
try:
    from jarvis.core.youtube_downloader import YouTubeDownloader
    YOUTUBE_AVAILABLE = True
    print("[WebSocket] YouTube downloader available")
except ImportError:
    pass

# Hotkey System
HOTKEY_AVAILABLE = False
try:
    from jarvis.core.hotkey_system import HotkeySystem
    HOTKEY_AVAILABLE = True
    print("[WebSocket] Hotkey system available")
except ImportError:
    pass

# Chat History (SQLite FTS5)
CHAT_HISTORY_AVAILABLE = False
try:
    from jarvis.core.chat_history import ChatHistory
    CHAT_HISTORY_AVAILABLE = True
    print("[WebSocket] Chat history available")
except ImportError:
    pass

# Habit Tracker
HABIT_TRACKER_AVAILABLE = False
try:
    from jarvis.core.habit_tracker import HabitTracker
    HABIT_TRACKER_AVAILABLE = True
    print("[WebSocket] Habit tracker available")
except ImportError:
    pass

# Task Manager
TASK_MANAGER_AVAILABLE = False
try:
    from jarvis.core.task_manager import TaskManager
    TASK_MANAGER_AVAILABLE = True
    print("[WebSocket] Task manager available")
except ImportError:
    pass

# Wellness Monitor
WELLNESS_AVAILABLE = False
try:
    from jarvis.core.wellness_monitor import WellnessMonitor
    WELLNESS_AVAILABLE = True
    print("[WebSocket] Wellness monitor available")
except ImportError:
    pass

# Clipboard Intelligence
CLIPBOARD_AVAILABLE = False
try:
    from jarvis.core.clipboard_intelligence import ClipboardIntelligence
    CLIPBOARD_AVAILABLE = True
    print("[WebSocket] Clipboard Intelligence available")
except ImportError:
    pass




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


class JARVISWebSocketServer:
    """WebSocket server with FULL JARVISUltimate integration"""
    
    def __init__(self, host="localhost", port=8765):
        # DEBUG LOGGING
        self.log_file = os.path.join(os.path.dirname(__file__), "server_debug.log")
        with open(self.log_file, "w") as f:
            f.write(f"[{datetime.now()}] Server initializing...\n")
            
        def log(msg):
            with open(self.log_file, "a") as f:
                f.write(f"[{datetime.now()}] {msg}\n")
        self.log = log
        
        self.log("Starting __init__")
        self.host = host
        self.port = port
        self.clients = set()
        self._client_channels = {}   # {websocket: set('command','stats','live','sensors')}
        self._client_queues = {}     # {websocket: asyncio.Queue} — per-client backpressure
        self._recent_result_text = ''  # For cross-pipeline dedup
        self._recent_result_time = 0
        self._last_stats_hash = ''  # Delta compression for periodic updates
        self.running = False
        self._voice_thread = None
        self._voice_loop = None  # asyncio event loop ref for cross-thread injection
        self._gesture_thread = None
        
        # Core JARVIS instance
        self.jarvis = None
        
        # HUD perception wrapper
        self.hud_perception = HUDPerception()
        
        # Feature handlers
        self.perception = None
        self.weather_handler = None
        self.news_handler = None
        self.system_status = None
        self._gesture_controller = None
        self._face_recognition = None
        self._emotion_detector = None
        
        # NEW: Additional feature handlers
        self.screenshot_handler = None
        self._ocr_handler = None
        self.dictionary_handler = None
        self.email_handler = None
        self.entertainment = None
        self.smart_notes = None
        self.alarm_system = None
        self.system_control = None
        self._knowledge = None  # For Groq Llama 3.3 AI
        self.reminder_manager = None  # For reminders
        self.screen_control = None  # Screen mouse/keyboard control
        self._pdf_handler = None  # PDF reader/extraction
        
        # NEW: Additional feature handlers
        self.whatsapp_handler = None  # WhatsApp messaging
        self.calendar = None  # Google Calendar
        self.sound_effects = None  # Sound effects for stories/notifications
        self.proactive_assistant = None  # Proactive suggestions
        self.email_handler_obj = None  # Email/Gmail handler
        self._youtube_downloader = None  # YouTube download
        self.hotkey_system = None  # Global hotkeys
        self._chat_history = None  # SQLite FTS5 chat history
        self._context_memory = None  # Context memory for conversations
        self.habit_tracker = None  # Daily habits
        self.task_manager_obj = None  # Tasks and reminders
        self.wellness_monitor = None  # Health reminders
        self._clipboard_intelligence = None  # Clipboard monitoring
        
        # IntentRouter for clean command routing
        self.router = None
        self.is_speaking = False  # Gesture controller needs this
        
        # State tracking
        self.current_user = None
        self.current_emotion = None
        self.last_gesture = None
        
        # ALL FEATURES AUTO-ENABLED ON STARTUP (fully operational JARVIS)
        self.gesture_enabled = True   # Auto-enabled: gestures active from boot
        self.face_enabled = True      # Always-on: face recognition
        self.emotion_enabled = True   # Always-on: emotion detection
        
        # Mute control - palm gesture can mute JARVIS
        self.muted_by_gesture = False  # Palm closed = JARVIS silent
        
        # CLEAN ARCHITECTURE: Centralized state manager (replaces manual deduplication)
        self.state_manager = StateManager()
        
        # Thread pool for async-safe heavy execution
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize everything
        self.log("Calling _init_jarvis")
        self._init_jarvis()
        self.log("__init__ complete")

    
    @property
    def emotion_detector(self):
        if getattr(self, 'jarvis', None):
            try: return self.jarvis.emotion_detector
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.emotion_detector: {e}")
        if getattr(self, '_emotion_detector', None) is None and EMOTION_AVAILABLE:
            try: self._emotion_detector = EmotionDetector()
            except Exception as e:
                print(f"[LAZY LOAD ERROR] emotion_detector: {e}")
                return None
        return getattr(self, '_emotion_detector', None)

    @property
    def face_recognition(self):
        if getattr(self, 'jarvis', None) and hasattr(self.jarvis, 'face_auth'):
            try: return self.jarvis.face_auth
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.face_auth: {e}")
        if getattr(self, '_face_recognition', None) is None and FACE_AVAILABLE:
            try: self._face_recognition = FaceRecognition(self.hud_perception)
            except Exception as e:
                print(f"[LAZY LOAD ERROR] face_recognition: {e}")
                return None
        return getattr(self, '_face_recognition', None)

    @property
    def gesture_controller(self):
        if getattr(self, 'jarvis', None) and hasattr(self.jarvis, 'gesture'):
            try: return self.jarvis.gesture
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.gesture: {e}")
        if getattr(self, '_gesture_controller', None) is None and GESTURE_AVAILABLE:
            try: self._gesture_controller = GestureController(self.hud_perception)
            except Exception as e:
                print(f"[LAZY LOAD ERROR] gesture_controller: {e}")
                return None
        return getattr(self, '_gesture_controller', None)

    @property
    def chat_history(self):
        if getattr(self, 'jarvis', None):
            try: return self.jarvis.chat_history
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.chat_history: {e}")
        if getattr(self, '_chat_history', None) is None and CHAT_HISTORY_AVAILABLE:
            try: self._chat_history = ChatHistory(self.hud_perception)
            except Exception as e:
                print(f"[LAZY LOAD ERROR] chat_history: {e}")
                return None
        return getattr(self, '_chat_history', None)

    @property
    def context_memory(self):
        if getattr(self, 'jarvis', None):
            try: return self.jarvis.context_memory
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.context_memory: {e}")
        if getattr(self, '_context_memory', None) is None and CONTEXT_MEMORY_AVAILABLE:
            try: self._context_memory = ContextMemory()
            except Exception as e:
                print(f"[LAZY LOAD ERROR] context_memory: {e}")
                return None
        return getattr(self, '_context_memory', None)

    @property
    def knowledge(self):
        if getattr(self, 'jarvis', None):
            try: return self.jarvis.knowledge
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.knowledge: {e}")
        if getattr(self, '_knowledge', None) is None and KNOWLEDGE_AVAILABLE:
            try: self._knowledge = KnowledgeLayer(self.hud_perception)
            except Exception as e:
                print(f"[LAZY LOAD ERROR] knowledge: {e}")
                return None
        return getattr(self, '_knowledge', None)

    @property
    def ocr_handler(self):
        if getattr(self, 'jarvis', None):
            try: return self.jarvis.ocr
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.ocr: {e}")
        if getattr(self, '_ocr_handler', None) is None and OCR_AVAILABLE:
            try: self._ocr_handler = OCRHandler(self.hud_perception)
            except Exception as e:
                print(f"[LAZY LOAD ERROR] ocr_handler: {e}")
                return None
        return getattr(self, '_ocr_handler', None)

    @property
    def pdf_handler(self):
        if getattr(self, 'jarvis', None):
            try: return self.jarvis.pdf
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.pdf: {e}")
        if getattr(self, '_pdf_handler', None) is None and PDF_AVAILABLE:
            try: self._pdf_handler = PDFHandler(self.hud_perception, self.knowledge)
            except Exception as e:
                print(f"[LAZY LOAD ERROR] pdf_handler: {e}")
                return None
        return getattr(self, '_pdf_handler', None)

    @property
    def youtube_downloader(self):
        if getattr(self, 'jarvis', None):
            try: return self.jarvis.youtube
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.youtube: {e}")
        if getattr(self, '_youtube_downloader', None) is None and YOUTUBE_AVAILABLE:
            try: self._youtube_downloader = YouTubeDownloader(self.hud_perception)
            except Exception as e:
                print(f"[LAZY LOAD ERROR] youtube_downloader: {e}")
                return None
        return getattr(self, '_youtube_downloader', None)

    @property
    def clipboard_intelligence(self):
        if getattr(self, 'jarvis', None):
            try: return self.jarvis.clipboard
            except Exception as e: print(f"[LAZY LOAD ERROR] jarvis.clipboard: {e}")
        if getattr(self, '_clipboard_intelligence', None) is None and CLIPBOARD_AVAILABLE:
            try: self._init_clipboard()
            except Exception as e:
                print(f"[LAZY LOAD ERROR] clipboard_intelligence: {e}")
                return None
        return getattr(self, '_clipboard_intelligence', None)
        
    def _init_jarvis(self):
        """Initialize JARVISUltimate and all handlers"""
        print("\n" + "="*60)
        print("     JARVIS WebSocket Server - Full Integration")
        print("="*60 + "\n")
        
        # Try to initialize full JARVIS
        if JARVIS_AVAILABLE:
            # We defer JARVISUltimate instantiation to Phase 2 to not block < 2s boot
            self.jarvis = None
            self._init_fallback()
        else:
            self._init_fallback()
        
        # Initialize standalone modules if not from JARVIS
        self._init_standalone_modules()
        
        # Initialize startup orchestrator for boot briefing
        self.startup_orchestrator = None
        try:
            from jarvis.core.startup_orchestrator import StartupOrchestrator
            boot_context = {
                "chat_history": getattr(self, '_chat_history', None),
                "weather_handler": getattr(self, 'weather_handler', None),
                "calendar": getattr(self, 'calendar', None),
                "reminder_manager": getattr(self, 'reminder_manager', None),
            }
            # Boot orchestrator - pass None for jarvis, it will handle it
            self.startup_orchestrator = StartupOrchestrator(None, boot_context)
            print("[BOOT] Startup Orchestrator ready")
        except Exception as e:
            print(f"[BOOT] Startup Orchestrator error: {e}")

        print("\n" + "="*60)
        print("     Server Ready - All Features Initialized")
        print("="*60 + "\n")
    
    # ═══════════════════════════════════════════════════════════════
    # VOICE LISTENING THREAD
    # Runs perception.listen() in background, injects into async pipeline
    # ═══════════════════════════════════════════════════════════════
    
    def _start_voice_thread(self):
        """Start background voice listening thread"""
        # When Gemini Live Engine is active, it owns the microphone exclusively.
        # Do NOT start the old STT pipeline — it would fight for the mic.
        if getattr(self, 'live_engine', None):
            print("[VOICE] Gemini Live Engine active -- old voice listener SKIPPED")
            return

        if not self.perception:
            print("[VOICE] No perception layer - voice input disabled")
            return
        
        self._voice_thread = threading.Thread(
            target=self._voice_listen_loop,
            daemon=True,
            name="JARVISVoiceThread"
        )
        self._voice_thread.start()
        print("[VOICE] Background voice listening thread started")
    
    def _voice_listen_loop(self):
        """Background voice listening loop.
        
        Runs perception.listen() continuously and injects recognized text
        into the async WebSocket pipeline via asyncio.run_coroutine_threadsafe.
        
        CRITICAL: Two-layer echo prevention:
        1. Flag-based: Skip listening while JARVIS is speaking (mic_muted)
        2. Content-based: Filter out text that matches recent JARVIS responses
        """
        print("[VOICE] Voice listening active - speak into microphone")
        
        # Store recent JARVIS responses for echo comparison
        if not hasattr(self, '_recent_responses'):
            self._recent_responses = []
        
        while self.running:
            try:
                # ━━━ LAYER 1: Flag-based echo guard + quiet mode ━━━
                if self.perception.is_speaking or self.perception.mic_muted:
                    time.sleep(0.3)
                    continue
                
                # Quiet mode: mic is OFF, only listen for wake word
                if getattr(self, 'quiet_mode', False):
                    # Keep mic muted in perception so normal pipeline stops
                    if self.perception:
                        self.perception.mic_muted = True
                    
                    # Direct silent listen for wake word (bypasses perception noise)
                    import speech_recognition as sr
                    r = sr.Recognizer()
                    try:
                        with sr.Microphone() as source:
                            r.adjust_for_ambient_noise(source, duration=0.2)
                            audio = r.listen(source, timeout=1, phrase_time_limit=3)
                        text = r.recognize_google(audio).lower()
                        if any(w in text for w in ['jarvis', 'friday', 'hey jarvis', 'wake up']):
                            self.quiet_mode = False
                            if self.perception:
                                self.perception.mic_muted = False
                                self.perception.is_speaking = False
                            print("[VOICE] Quiet mode OFF - wake word detected")
                            # Process the command after the wake word
                            if self._voice_loop and self.clients:
                                asyncio.run_coroutine_threadsafe(
                                    self._handle_voice_input(text),
                                    self._voice_loop
                                )
                    except:
                        pass # Silently drop everything else in quiet mode
                    
                    time.sleep(0.5)
                    continue
                
                # Listen for speech (blocks until speech detected or timeout)
                text = self.perception.listen(timeout=10)
                
                if text and text.strip() and len(text.strip()) > 2:
                    text = text.strip()
                    
                    # ━━━ LAYER 2: Content-based echo filter ━━━
                    # If voice input matches a recent JARVIS response, it's echo
                    text_words = set(text.lower().split())
                    is_echo = False
                    for recent_resp in self._recent_responses:
                        resp_words = set(recent_resp.lower().split())
                        if not text_words or not resp_words:
                            continue
                        # Check word overlap — if >50% of input words appear in response
                        overlap = len(text_words & resp_words)
                        if len(text_words) > 0 and overlap / len(text_words) > 0.5:
                            print(f"[VOICE] Echo filtered: \"{text[:50]}...\" (matched recent response)")
                            is_echo = True
                            break
                    
                    if is_echo:
                        continue
                    
                    print(f"[VOICE] Recognized: \"{text}\"")
                    
                    # ━━━ INTERRUPT: Stop JARVIS if speaking when user talks ━━━
                    if self.perception.is_speaking:
                        print("[VOICE] User spoke while JARVIS speaking - interrupting")
                        self._stop_speaking()
                        time.sleep(0.3)
                    
                    # Inject into async event loop
                    if self._voice_loop and self.clients:
                        asyncio.run_coroutine_threadsafe(
                            self._handle_voice_input(text),
                            self._voice_loop
                        )
                    elif not self.clients:
                        print("[VOICE] No clients connected, skipping")
                        
            except Exception as e:
                err_str = str(e)
                # Don't spam on timeouts
                if 'listening timed out' not in err_str.lower() and 'WaitTimeoutError' not in err_str:
                    print(f"[VOICE] Listen error: {e}")
                time.sleep(0.5)
    
    async def _handle_voice_input(self, text: str):
        """Process voice input text through the command pipeline (called from voice thread)"""
        # Process through unified pipeline via first client only
        # NOTE: We do NOT send a separate 'voice_recognized' message.
        # The 'result' from process_message already contains the response.
        for ws in list(self.clients):
            try:
                data = {'type': 'voice_input', 'text': text}
                await self.process_message(ws, data)
                break  # Only process once via first client
            except Exception as e:
                print(f"[VOICE] Pipeline error: {e}")
    
    def _init_fallback(self):
        """Initialize with individual components"""
        print("[WebSocket] Using fallback initialization...")
        
        if PERCEPTION_AVAILABLE:
            try:
                self.perception = PerceptionLayer()
                self.hud_perception = HUDPerception(self.perception)
                print("[WebSocket] Perception layer initialized")
            except Exception as e:
                print(f"[WebSocket] Perception error: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # GESTURE PROCESSING THREAD
    # Captures camera → detects gestures → executes actions
    # ═══════════════════════════════════════════════════════════════
    
    def _start_gesture_thread(self):
        """Start background gesture processing thread"""
        if not self.gesture_controller:
            print("[GESTURE] No gesture controller - gesture thread disabled")
            return
        
        self._gesture_thread = threading.Thread(
            target=self._gesture_process_loop,
            daemon=True,
            name="JARVISGestureThread"
        )
        self._gesture_thread.start()
        print("[GESTURE] Background gesture processing thread started")
    
    def _gesture_process_loop(self):
        """Background gesture detection loop.
        
        Uses shared camera for frames, detects gestures, executes actions.
        """
        try:
            from jarvis.core.gesture_controller import get_gesture_action, execute_gesture_action
        except ImportError:
            from core.gesture_controller import get_gesture_action, execute_gesture_action
        
        # Use shared camera instead of opening our own
        try:
            from jarvis.core.shared_camera import get_shared_camera
        except ImportError:
            from core.shared_camera import get_shared_camera
        
        shared_cam = get_shared_camera()
        shared_cam.register("gesture")
        print("[GESTURE] Gesture processing active (shared camera)")
        
        while self.running:
            try:
                # Only process if gestures are enabled
                if not self.gesture_enabled:
                    time.sleep(0.5)
                    continue
                
                # Get frame from shared camera
                frame = shared_cam.get_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Detect gesture
                gesture, meta = self.gesture_controller.detect(frame)
                
                # Skip idle/tracking/disabled states
                if gesture in ('idle', 'tracking', 'hand_tracking', 'disabled', 'error'):
                    time.sleep(0.05)  # ~20fps
                    continue
                
                # ━━━ CONFIDENCE GATE — skip weak detections ━━━
                confidence = meta.get('confidence', 0.0)
                if confidence < 0.6:
                    time.sleep(0.05)
                    continue
                
                # ━━━ PER-GESTURE DEBOUNCE — prevent spam ━━━
                now = time.time()
                if not hasattr(self, '_gesture_last_fire'):
                    self._gesture_last_fire = {}
                
                # Cooldowns per gesture type (seconds)
                GESTURE_COOLDOWNS = {
                    'pinch': 1.5,       # Click — needs long cooldown 
                    'open_palm': 2.0,   # Stop speaking — long cooldown
                    'swipe_left': 0.8,  # Navigation — moderate
                    'swipe_right': 0.8,
                    'swipe_up': 0.8,
                    'swipe_down': 0.8,
                    'rotate_cw': 1.0,
                    'rotate_ccw': 1.0,
                    'thumb_up': 2.0,
                    'thumb_down': 2.0,
                    'peace': 2.0,
                    'fist': 1.5,
                }
                cooldown = GESTURE_COOLDOWNS.get(gesture, 1.0)
                last_fire = self._gesture_last_fire.get(gesture, 0)
                
                if now - last_fire < cooldown:
                    time.sleep(0.05)
                    continue  # Still in cooldown
                
                self._gesture_last_fire[gesture] = now
                
                # ━━━ OPEN PALM = STOP SPEAKING (instant) ━━━
                if gesture == 'open_palm':
                    if getattr(self, 'is_speaking', False) or getattr(self.hud_perception, 'is_speaking', False):  # Only fire if actually speaking
                        self._stop_speaking()
                        self.state_manager.force_state("idle")
                        # Send visual feedback to HUD
                        if self._voice_loop and self.clients:
                            stop_msg = json.dumps({
                                'type': 'gesture_action',
                                'gesture': 'open_palm',
                                'action': 'stop_speaking',
                                'app': 'default',
                                'confidence': confidence
                            })
                            for ws in list(self.clients):
                                try:
                                    asyncio.run_coroutine_threadsafe(
                                        ws.send(stop_msg), self._voice_loop
                                    )
                                except Exception:
                                    pass
                    continue
                
                # Map gesture to action based on active app
                active_app = "default"
                if self.state_manager and hasattr(self.state_manager, 'active_app') and self.state_manager.active_app:
                    active_app = self.state_manager.active_app
                
                action = get_gesture_action(gesture, active_app)
                
                if action:
                    print(f"[GESTURE] {gesture} -> {action} (app: {active_app}, conf: {confidence:.2f})")
                    
                    # Special: stop_speaking is handled by server, not pyautogui
                    if action == 'stop_speaking':
                        self._stop_speaking()
                    else:
                        execute_gesture_action(action)
                    
                    # Send gesture event to connected clients
                    if self._voice_loop and self.clients:
                        gesture_msg = json.dumps({
                            'type': 'gesture_action',
                            'gesture': gesture,
                            'action': action,
                            'app': active_app,
                            'confidence': confidence,
                            'channel': 'sensors'
                        })
                        for ws in list(self.clients):
                            channels = self._client_channels.get(ws, {'command', 'stats', 'live', 'sensors'})
                            if 'sensors' not in channels:
                                continue
                            try:
                                asyncio.run_coroutine_threadsafe(
                                    ws.send(gesture_msg),
                                    self._voice_loop
                                )
                            except Exception:
                                pass
                
                time.sleep(0.05)  # ~20fps
                
            except Exception as e:
                err_str = str(e)
                if 'camera' not in err_str.lower():
                    print(f"[GESTURE] Processing error: {e}")
                time.sleep(1)
        
        # Cleanup
        shared_cam.unregister("gesture")
    
    def _init_standalone_modules(self):
        """Initialize modules: CRITICAL ones immediately, DEFERRED ones in background.
        
        This cuts perceived startup from ~30s to ~10s by loading only essential
        modules first and deferring rarely-used ones to a background thread.
        """
        import time as _time
        start = _time.time()
        
        # ══════════════════════════════════════════════════════════════
        # PHASE 1: CRITICAL MODULES (sync — must be ready before server accepts clients)
        # ══════════════════════════════════════════════════════════════
        print("[BOOT] Phase 1: Loading critical modules...")
        
        # Fast / Lightweight handlers
        if not getattr(self, 'news_handler', None) and NEWS_AVAILABLE:
            try:
                self.news_handler = NewsHandler(self.hud_perception)
            except Exception as e:
                pass
        
        if not getattr(self, 'weather_handler', None) and WEATHER_AVAILABLE:
            try:
                self.weather_handler = WeatherHandler(self.hud_perception)
            except Exception as e:
                pass
        
        # Setup lazy property backings to None
        self._emotion_detector = None
        self._face_recognition = None
        self._gesture_controller = None
        self._chat_history = None
        self._context_memory = None
        self._knowledge = None
        self._ocr_handler = None
        self._pdf_handler = None
        self._youtube_downloader = None
        self._clipboard_intelligence = None

        
        if CONTEXT_MEMORY_AVAILABLE:
            try:
                self.context_memory = ContextMemory()
            except Exception as e:
                print(f"[WebSocket] Context memory init error: {e}")
        
        # Hotkeys (must register immediately)
        if HOTKEY_AVAILABLE:
            try:
                # C-05: Pass a proper callback so hotkeys actually work
                self.hotkey_system = HotkeySystem(
                    self.hud_perception,
                    jarvis_callback=self._on_hotkey_action
                )
            except: pass
        
        # Reminders & Tasks 
        if REMINDER_AVAILABLE:
            try:
                self.reminder_manager = ReminderManager(self.hud_perception)
                self.reminder_manager.start()
            except: pass
        
        if TASK_MANAGER_AVAILABLE:
            try:
                self.task_manager_obj = TaskManager(self.hud_perception)
            except: pass
        
        # System control (needed for voice commands)
        if SYSTEM_CONTROL_AVAILABLE:
            try:
                self.system_control = SystemControl(self.hud_perception)
            except Exception as e:
                print(f"[WebSocket] System control init error: {e}")
        
        # Screenshot (needed for read_screen tool)
        if SCREENSHOT_AVAILABLE:
            try:
                self.screenshot_handler = ScreenshotHandler(self.hud_perception)
            except Exception as e:
                print(f"[WebSocket] Screenshot init error: {e}")
        
        # Gemini Live Engine (core AI voice — must start immediately)
        self.live_engine = None
        if GEMINI_LIVE_AVAILABLE:
            try:
                api_key = os.getenv("GEMINI_API_KEY")
                self.live_engine = GeminiLiveEngine(
                    api_key=api_key,
                    server=self
                )
                self.live_engine.start()
                if self.hud_perception:
                    self.hud_perception._gemini_live_active = True
                print("[WebSocket] Gemini Live Engine Initialized & Started")
            except Exception as e:
                print(f"[WebSocket] Gemini Live Engine error: {e}")

        if ROUTER_AVAILABLE:
            print(f"[WebSocket] Intent routing ready (classify_intent + HANDLER_MAP with {len(HANDLER_MAP)} handlers)")
        
        critical_time = _time.time() - start
        print(f"[BOOT] Phase 1 complete in {critical_time:.1f}s — server accepting connections")
        
        # ══════════════════════════════════════════════════════════════
        # PHASE 2: DEFERRED MODULES (background ThreadPoolExecutor)
        # ══════════════════════════════════════════════════════════════
        def _prewarm_jarvis():
            if JARVIS_AVAILABLE:
                try:
                    self.jarvis = JARVISUltimate()
                    self.perception = self.jarvis.perception
                    self.hud_perception = HUDPerception(self.perception)
                    # Re-apply Gemini Live flag (lost when hud_perception was recreated)
                    if getattr(self, 'live_engine', None):
                        self.hud_perception._gemini_live_active = True
                    self.news_handler = self.jarvis.news_handler
                    self.weather_handler = self.jarvis.weather
                    if getattr(self, 'startup_orchestrator', None):
                        self.startup_orchestrator.jarvis = self.jarvis
                    
                    # C-06: Force identity from voice_prefs.json after Phase 2
                    # Prevents FRIDAY from persisting when prefs say 'jarvis'
                    try:
                        _prefs_path = Path(__file__).parent.parent / "data" / "voice_prefs.json"
                        if _prefs_path.exists():
                            import json as _jl
                            with open(_prefs_path) as _f:
                                _name = _jl.load(_f).get("assistant", "jarvis")
                            self.hud_perception.assistant_name = _name.upper()
                            self.hud_perception.is_friday = (_name.lower() == "friday")
                            print(f"[BG LOAD] Forced identity: {_name.upper()}")
                    except Exception as _e:
                        print(f"[BG LOAD] Identity force failed (non-critical): {_e}")
                    
                    print("[BG LOAD] JARVIS core prewarmed")
                except Exception as e:
                    print(f"[BG LOAD ERROR] JARVIS core prewarming failed: {e}")

        def _load_deferred():
            defer_start = _time.time()
            print("[BOOT] Phase 2: Loading deferred modules in background...")
            
            import concurrent.futures
            
            # Start JARVIS init directly in the background sequentially first
            _prewarm_jarvis()

            # ── Initialize Brain Adapter (wires advanced ML modules) ──
            if BRAIN_AVAILABLE:
                try:
                    self._brain = get_brain_adapter()
                    print("[BG LOAD] Brain Adapter initialized")
                    if hasattr(self, 'perception') and self.perception:
                        self._brain.start_perception_consumer(self.perception)
                        print("[BG LOAD] Brain Perception Consumer started")
                except Exception as e:
                    print(f"[BG LOAD ERROR] Brain Adapter: {e}")
                    self._brain = None
            else:
                self._brain = None

            deferred_modules = [
                (EMOTION_AVAILABLE, '_emotion_detector', lambda: EmotionDetector(), "EmotionDetector"),
                (FACE_AVAILABLE, '_face_recognition', lambda: FaceRecognition(self.hud_perception), "FaceRecognition"),
                (GESTURE_AVAILABLE, '_gesture_controller', lambda: GestureController(self.hud_perception), "GestureController"),
                (CHAT_HISTORY_AVAILABLE, '_chat_history', lambda: ChatHistory(self.hud_perception), "ChatHistory"),
                (CONTEXT_MEMORY_AVAILABLE, '_context_memory', lambda: ContextMemory(), "ContextMemory"),
                (KNOWLEDGE_AVAILABLE, '_knowledge', lambda: KnowledgeLayer(self.hud_perception), "KnowledgeLayer"),
                (OCR_AVAILABLE, '_ocr_handler', lambda: OCRHandler(self.hud_perception), "OCR"),
                (DICTIONARY_AVAILABLE, 'dictionary_handler', lambda: DictionaryHandler(self.hud_perception), "Dictionary"),
                (ENTERTAINMENT_AVAILABLE, 'entertainment', lambda: JARVISEntertainment(self.hud_perception, self.knowledge), "Entertainment"),
                (NOTES_AVAILABLE, 'smart_notes', lambda: SmartNotes(self.hud_perception), "Smart Notes"),
                (ALARM_AVAILABLE, 'alarm_system', lambda: AlarmSystem(self.hud_perception), "Alarm"),
                (SCREEN_CONTROL_AVAILABLE, 'screen_control', lambda: ScreenControlHandler(), "Screen Control"),
                (WHATSAPP_AVAILABLE, 'whatsapp_handler', lambda: WhatsAppHandler(self.hud_perception), "WhatsApp"),
                (CALENDAR_AVAILABLE, 'calendar', lambda: CalendarIntegration(self.hud_perception), "Calendar"),
                (SOUND_EFFECTS_AVAILABLE, 'sound_effects', lambda: SoundEffects(), "Sound Effects"),
                (PROACTIVE_AVAILABLE, 'proactive_assistant', lambda: ProactiveAssistant(self.hud_perception), "Proactive"),
                (EMAIL_HANDLER_AVAILABLE, 'email_handler_obj', lambda: EmailHandler(self.hud_perception, getattr(self, '_knowledge', None)), "Email"),
                (YOUTUBE_AVAILABLE, '_youtube_downloader', lambda: YouTubeDownloader(self.hud_perception), "YouTube"),
                (HABIT_TRACKER_AVAILABLE, 'habit_tracker', lambda: HabitTracker(self.hud_perception), "Habits"),
                (WELLNESS_AVAILABLE, 'wellness_monitor', lambda: WellnessMonitor(self.hud_perception), "Wellness"),
                (PDF_AVAILABLE, '_pdf_handler', lambda: PDFHandler(self.hud_perception), "PDF"),
                (CLIPBOARD_AVAILABLE, '_clipboard_intelligence', lambda: getattr(self, '_init_clipboard', lambda: None)(), "Clipboard"),
            ]
            
            def _load_module_safe(mod_def):
                available, attr_name, factory, label = mod_def
                if available and getattr(self, attr_name, None) is None:
                    try:
                        setattr(self, attr_name, factory())
                        print(f"[BG LOAD] {label} loaded")
                        return True
                    except Exception as e:
                        print(f"[BG LOAD ERROR] {label}: {e}")
                return False

            loaded = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(_load_module_safe, deferred_modules))
                loaded = sum(1 for r in results if r)
            
            defer_time = _time.time() - defer_start
            print(f"[BOOT] Phase 2 complete: deferred batch finished. {loaded} modules loaded in {defer_time:.1f}s")
        
        # Launch deferred loading in background thread
        self._deferred_thread = threading.Thread(
            target=_load_deferred,
            daemon=True,
            name="JARVISDeferredInit"
        )
        self._deferred_thread.start()
    
    def _init_clipboard(self):
        """Create ClipboardIntelligence with HUD suggestion callback."""
        def _push_clipboard_suggestion(suggestion):
            import json
            msg = json.dumps({
                'type': 'clipboard_suggestion',
                'suggestion': suggestion.get('suggestion', ''),
                'action': suggestion.get('action', ''),
                'content_type': suggestion.get('type', ''),
            })
            for client in getattr(self, 'clients', set()):
                try:
                    import asyncio
                    asyncio.run_coroutine_threadsafe(
                        client.send(msg),
                        getattr(self, '_voice_loop', None) or asyncio.get_event_loop()
                    )
                except Exception:
                    pass
        
        clip = ClipboardIntelligence(
            perception=self.hud_perception,
            on_suggestion=_push_clipboard_suggestion
        )
        clip.start()
        return clip
    
    def recall_conversation(self, query: str) -> str:
        """Search chat history for past conversations matching query."""
        if not self.chat_history:
            return "Chat history not ready yet, sir."
        try:
            results = self.chat_history.search(query, limit=5)
            if not results:
                return f"No conversations found matching '{query}'."
            
            lines = [f"Found {len(results)} relevant conversation(s):"]
            for msg in results:
                role = "You" if msg.role == 'user' else "JARVIS"
                ts = msg.timestamp.strftime('%b %d, %I:%M %p') if hasattr(msg, 'timestamp') and msg.timestamp else ''
                text = msg.text[:150] if hasattr(msg, 'text') else str(msg)[:150]
                lines.append(f"  [{ts}] {role}: {text}")
            return "\n".join(lines)
        except Exception as e:
            return f"Search error: {e}"
    
    def get_system_stats(self):
        """Get current system statistics — delegates to data_providers."""
        return _get_system_stats()
    
    def get_weather_data(self, city=None):
        """Get weather data — delegates to data_providers."""
        return _get_weather_data(weather_handler=self.weather_handler, city=city)
    
    def get_news_data(self, category='general', count=5, location=None):
        """Get news headlines — delegates to data_providers."""
        return _get_news_data(news_handler=self.news_handler, category=category,
                              count=count, location=location)
    
    def get_feature_status(self):
        """Get status of all advanced features"""
        sm = self.state_manager
        return {
            'type': 'feature_status',
            'jarvis_full': self.jarvis is not None,
            'gesture_available': self.gesture_controller is not None,
            'gesture_enabled': self.gesture_enabled,
            'face_available': self.face_recognition is not None,
            'face_enabled': self.face_enabled,
            'emotion_available': self.emotion_detector is not None,
            'emotion_enabled': self.emotion_enabled,
            'current_user': self.current_user,
            'current_emotion': self.current_emotion,
            'last_gesture': self.last_gesture,
            'whatsapp_available': self.whatsapp_handler is not None,
            'active_app': getattr(sm, 'active_app', None),
            'current_mood': getattr(sm, 'current_mood', None),
            'mood_confidence': getattr(sm, 'mood_confidence', None),
            'emotion_vector': getattr(sm, 'emotion_vector', None),
            'fatigue_score': getattr(sm, 'fatigue_score', None),
            'attention_score': getattr(sm, 'attention_score', None),
        }
    
    async def handle_client(self, websocket, path=None):
        """Handle a client connection"""
        self.clients.add(websocket)
        # Subscribe to all channels by default
        self._client_channels[websocket] = {'command', 'stats', 'live', 'sensors'}
        # Per-client queue for backpressure (maxsize=50)
        self._client_queues[websocket] = asyncio.Queue(maxsize=50)
        client_id = id(websocket)
        print(f"[WebSocket] Client connected: {client_id}")
        
        # Start per-client sender loop (drains queue → ws.send)
        sender_task = asyncio.create_task(self._client_sender(websocket))
        
        try:
            # ══════ BOOT SEQUENCE: Batched single payload ══════
            name = self.hud_perception.assistant_name

            # Generate boot briefing from orchestrator
            boot_briefing = None
            if self.startup_orchestrator:
                try:
                    boot_briefing = self.startup_orchestrator.generate_boot_briefing()
                    print(f"[BOOT] Briefing generated: {boot_briefing.get('greeting', '')[:60]}")
                except Exception as e:
                    print(f"[BOOT] Briefing error: {e}")

            # Build greeting for HUD chat panel (always shown — Gemini Live handles audio separately)
            greeting_text = None
            if boot_briefing:
                greeting_text = boot_briefing.get('spoken_briefing', f'{name} online, sir.')
            else:
                hour = datetime.now().hour
                greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
                greeting_text = f'{greeting}, sir. {name} online. How can I help you?'

            # ━━━ SINGLE BATCHED INIT PAYLOAD (1 send instead of 6) ━━━
            init_payload = {
                'type': 'init_payload',
                'assistant_info': {'name': name, 'is_friday': self.hud_perception.is_friday},
                'system_stats': self.get_system_stats(),
                'weather': self.get_weather_data(),
                'news': self.get_news_data(),
                'features': self.get_feature_status(),
            }
            if greeting_text:
                _greet_speak = not bool(getattr(self, 'live_engine', None))
                init_payload['greeting'] = {'text': greeting_text, 'speak': _greet_speak}
            if boot_briefing:
                init_payload['briefing'] = boot_briefing
            
            await self._send_to(websocket, init_payload)
            
            # Start periodic updates
            stats_task = asyncio.create_task(self.send_periodic_updates(websocket))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    # Handle channel subscription messages
                    if data.get('type') == 'subscribe':
                        channels = data.get('channels', [])
                        if channels:
                            self._client_channels[websocket] = set(channels)
                        continue
                    await self.process_message(websocket, data)
                except json.JSONDecodeError:
                    print(f"[WebSocket] Invalid JSON")
                except Exception as e:
                    print(f"[WebSocket] Error: {e}")
            
            stats_task.cancel()
            
        except websockets.exceptions.ConnectionClosed:
            print(f"[WebSocket] Client disconnected: {client_id}")
        finally:
            sender_task.cancel()
            self.clients.discard(websocket)
            self._client_channels.pop(websocket, None)
            self._client_queues.pop(websocket, None)
            # Save session state on disconnect for next boot
            if self.startup_orchestrator:
                try:
                    self.startup_orchestrator.save_session()
                    print("[BOOT] Session state saved on disconnect")
                except Exception as e:
                    print(f"[BOOT] Session save error: {e}")
    
    async def send_periodic_updates(self, websocket):
        """Send updates periodically with delta compression"""
        counter = 0
        while True:
            try:
                await asyncio.sleep(10)  # 10s instead of 3s
                
                # Only send stats if values changed (delta compression)
                stats = self.get_system_stats()
                stats_hash = str(stats.get('cpu', 0)) + str(stats.get('ram', 0)) + str(stats.get('battery', 0))
                if stats_hash != self._last_stats_hash:
                    self._last_stats_hash = stats_hash
                    stats['channel'] = 'stats'
                    await self._send_to(websocket, json.dumps(stats))
                
                counter += 1
                if counter >= 18:  # Every 3 minutes (18 * 10s)
                    counter = 0
                    weather = self.get_weather_data()
                    weather['channel'] = 'stats'
                    await self._send_to(websocket, json.dumps(weather))
                    news = self.get_news_data()
                    news['channel'] = 'stats'
                    await self._send_to(websocket, json.dumps(news))
            except:
                break
    
    async def apply_action(self, websocket, action: Action):
        """Single point for all WebSocket responses - PREVENTS LOOPS"""
        if action.type == "SPEAK":
            text = action.payload.get("text", "")
            if not text:
                return
            
            # CRITICAL: Duplicate response check
            if self.state_manager.is_duplicate_response(text):
                print(f"[WebSocket] Skipping duplicate response")
                return
            
            _should_speak = action.payload.get("speak", True) and not bool(getattr(self, 'live_engine', None))
                
            await self._send_to(websocket, json.dumps({
                "type": "response",
                "text": text,
                "speak": _should_speak,
                "mood": action.payload.get("mood", "neutral")
            }))
        elif action.type == "UPDATE_UI":
            await self._send_to(websocket, json.dumps({
                "type": action.payload.get("ui_type", "update"),
                **{k: v for k, v in action.payload.items() if k != "ui_type"}
            }))
        # SILENT actions do nothing
    
    # ── C-05: Hotkey callback handler ──
    def _on_hotkey_action(self, action):
        """Handle hotkey actions from HotkeySystem"""
        if action == "shutdown":
            import os, signal
            print("[HOTKEY] Shutdown requested via hotkey")
            self.running = False
            os.kill(os.getpid(), signal.SIGTERM)
        elif action == "activate":
            # If Gemini Live is running, inject a greeting
            if getattr(self, 'live_engine', None) and self.live_engine._running:
                try:
                    self._push_live_text("Hey JARVIS, I need you.")
                except Exception:
                    pass
            else:
                self.hud_perception.speak("Yes sir, I'm here.")
    
    # ── C-01: Push text into Gemini Live session ──
    def _push_live_text(self, text):
        """Inject user text directly into the active Gemini Live session.
        This prevents dual-response clashing by using a single audio path.
        """
        le = getattr(self, 'live_engine', None)
        if not le or not le._running or not le.session:
            raise RuntimeError("Gemini Live session not available")
        
        from google import genai
        
        # Push into the live session's event loop
        async def _inject():
            await le.session.send_client_content(
                turns=[{"role": "user", "parts": [{"text": text}]}],
                turn_complete=True
            )
        
        import asyncio
        asyncio.run_coroutine_threadsafe(_inject(), le._loop)
    
    async def process_message(self, websocket, data):
        """Process incoming message using clean gateway architecture
        
        PROTOCOL:
        - Input: text_input, voice_input, command → all go to handle_input
        - Output: result (with action/response/confidence/state) + state updates
        """
        msg_type = data.get('type', '')
        
        # HARD PIPELINE GATE
        if getattr(self, "live_engine", None) and data.get("type") in ["text_input", "voice_input"]:
            print("[PIPELINE] Live active → skipping local pipeline")
            return
        
        # ═══════════════════════════════════════════════════════════════
        # SPEECH INTERRUPTION: Stop JARVIS mid-speech
        # Gesture (palm) or explicit 'stop' command stops TTS immediately
        # ═══════════════════════════════════════════════════════════════
        if msg_type == 'stop_speaking':
            self._stop_speaking()
            self.state_manager.force_state("idle")
            await self._send_to(websocket, json.dumps({
                'type': 'state',
                'state': self.state_manager.get_full_state()
            }))
            return
        
        # ═══════════════════════════════════════════════════════════════
        # UNIFIED INPUT HANDLER: text_input / voice_input / command
        # All user input flows through the same brain path
        # ═══════════════════════════════════════════════════════════════
        if msg_type in ('text_input', 'voice_input', 'command', 'chat'):
            text = data.get('text', '') or data.get('payload', {}).get('text', '')

            # ── VOICE CLASH GUARD ─────────────────────────────────────
            # When Gemini Live is running, it owns the microphone and
            # produces its own audio responses.  The HUD still transcribes
            # speech and sends voice_input, which would create a SECOND
            # response path (text→TTS) clashing with the native audio.
            # Block that path here; text_input / command / chat still work.
            # ──────────────────────────────────────────────────────────
            _live_active = (
                getattr(self, 'live_engine', None) is not None
                and getattr(self.live_engine, '_running', False)
            )
            if msg_type == 'voice_input' and _live_active:
                if jlog:
                    jlog.warn(f'voice_input suppressed (Gemini Live active): "{text[:60]}"')
                else:
                    print(f"[WebSocket] voice_input suppressed (Gemini Live owns mic): {text[:60]}")
                return
            
            # C-01: When Gemini Live is active, route text/command/chat INTO the live session
            # instead of running the legacy command pipeline. This prevents dual responses.
            if _live_active and msg_type in ('text_input', 'command', 'chat') and text.strip():
                try:
                    # Push user text into the Gemini Live session as a text turn
                    self._push_live_text(text)
                    if jlog:
                        jlog.info(f'Routed to Gemini Live: "{text[:60]}"')
                    else:
                        print(f"[WebSocket] Routed text to Gemini Live: {text[:60]}")
                    return
                except Exception as _live_err:
                    print(f"[WebSocket] Live text injection failed, falling through: {_live_err}")
                    # Fall through to legacy pipeline as safety net
            if not text:
                return
            
            if jlog: jlog.input(msg_type, text)
            else: print(f"[WebSocket] Input ({msg_type}): {text}")
            
            # Deduplication
            if self.state_manager.is_duplicate_command(text):
                if jlog: jlog.warn(f'Skipping duplicate: "{text}"')
                return
            
            # Update state: processing (skip intermediate 'listening' broadcast)
            self.state_manager.force_state("processing")
            self.state_manager.update_intent(msg_type, 0.0)
            
            # Detect mood from text
            mood = _detect_mood_from_text(text, emotion_enabled=self.emotion_enabled,
                                          emotion_detector=self.emotion_detector)
            if mood != 'neutral':
                self.current_emotion = mood
                self.state_manager.update_mood(mood, 0.7)
            
            # NOTE: Removed intermediate state(listening) broadcast
            # The result message at the end already contains state

            
            # State: processing
            self.state_manager.force_state("processing")
            
            # ═══════════════════════════════════════════════════════════════
            # FAST PATH: Instant execution for common commands
            # Skips heavy routing chain — sub-100ms response
            # ═══════════════════════════════════════════════════════════════
            fast_response = self._try_fast_path(text)
            
            # ═══════════════════════════════════════════════════════════════
            # COMPOUND COMMAND SPLITTING
            # "set alarm for 5 min and remind me to drink water" → 2 commands
            # ═══════════════════════════════════════════════════════════════
            if not fast_response:
                sub_commands = self._split_compound_command(text)
            
            # ═══════════════════════════════════════════════════════════════
            # CORE: Process through JARVIS brain (or fallback)
            # Error recovery: if handler crashes, reset to idle + notify UI
            # ═══════════════════════════════════════════════════════════════
            try:
                if fast_response:
                    response = fast_response
                elif len(sub_commands) > 1:
                    # Process each sub-command and combine responses
                    responses = []
                    for i, sub_cmd in enumerate(sub_commands):
                        print(f"[WebSocket] Processing sub-command {i+1}/{len(sub_commands)}: {sub_cmd}")
                        sub_response = await self.process_command(sub_cmd.strip(), websocket)
                        if sub_response:
                            responses.append(sub_response)
                    response = " Also, ".join(responses) if responses else "Done."
                else:
                    response = await self.process_command(text, websocket)
            except Exception as e:
                if jlog: jlog.error('Command processing failed', e)
                else: print(f"[WebSocket] CRITICAL: process_command failed: {e}")
                self.state_manager.force_state("idle")
                response = f"I encountered an error processing that command. Please try again."
                await self._send_to(websocket, json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
            
            # Infer action/intent from response (basic pattern matching)
            action = _infer_action_from_text(text)
            confidence = 0.85 if response and len(response) > 10 else 0.5
            if jlog: jlog.state(action=action, confidence=confidence, mood=mood)
            
            # Update state with intent
            self.state_manager.update_intent(action, confidence)
            
            # Adapt response based on mood
            response = _adapt_response_to_mood(
                response, mood,
                title=self.hud_perception.user_title,
                perception=self.perception,
                hud_perception=self.hud_perception,
                jarvis=self.jarvis
            )
            
            # ━━━ REDUCE "sir" OVERUSE (natural, not robotic) ━━━
            title = getattr(self.hud_perception, 'user_title', 'sir') if self.hud_perception else 'sir'
            response = _reduce_sir_usage(response, title=title)
            
            # ━━━ STORE RESPONSE FOR ECHO FILTERING ━━━
            # Voice loop compares mic input against these to filter echoes
            if not hasattr(self, '_recent_responses'):
                self._recent_responses = []
            self._recent_responses.append(response or '')
            if len(self._recent_responses) > 3:
                self._recent_responses.pop(0)
            
            # State: speaking
            self.state_manager.force_state("speaking")
            
            # ━━━ MUTE MIC BEFORE SENDING TO HUD (prevents TTS echo) ━━━
            # The HUD plays audio via browser TTS — mic must be off during playback
            if self.perception:
                self.perception.mic_muted = True
                self.perception.is_speaking = True
            
            # ═══════════════════════════════════════════════════════════════
            # SEND RESULT: action + response + confidence + state
            # This is the SINGLE unified response for all input
            # ═══════════════════════════════════════════════════════════════
            result = {
                'type': 'result',
                'action': action,
                'response': response if not getattr(self, "live_engine", None) else "",
                'confidence': confidence,
                'mood': mood,
                'silent': getattr(self, '_silent_response', False),
                'speak': not getattr(self, '_silent_response', False) and not bool(getattr(self, 'live_engine', None)),
                'state': {'current': self.state_manager.state if self.state_manager else 'idle'},
                'channel': 'command'
            }
            # Reset silent flag
            self._silent_response = False
            if jlog: jlog.response(response or '', spoken=True)
            await self._send_to(websocket, json.dumps(result))
            
            # Record for cross-pipeline dedup
            import time as _rtime
            self._recent_result_text = response or ''
            self._recent_result_time = _rtime.time()
            
            # ━━━ SCHEDULE MIC UNMUTE after estimated speech duration ━━━
            # ~150 words/min = ~2.5 words/sec. Add 1s buffer for echo fade.
            word_count = len((response or '').split())
            speech_secs = max(2.0, word_count / 2.5 + 1.0)
            
            async def _unmute_after(delay):
                await asyncio.sleep(delay)
                if self.perception:
                    self.perception.is_speaking = False
                    self.perception.mic_muted = False
                self.state_manager.force_state("idle")
            
            asyncio.ensure_future(_unmute_after(speech_secs))
            
            # NOTE: Removed duplicate apply_action send - result message above
            # already contains the response. Sending twice caused double messages.
            
            # Save to chat history for memory
            if self.chat_history:
                try:
                    self.chat_history.add_message('user', text)
                    self.chat_history.add_message('assistant', response)
                except Exception as e:
                    if jlog: jlog.error('Chat history save failed', e)
                    else: print(f"[WebSocket] Chat history error: {e}")
            
            # Record action for proactive pattern learning
            if self.proactive_assistant:
                try:
                    self.proactive_assistant.record_action(action, {'command': text})
                except Exception:
                    pass
            
            # Return to idle after speaking
            words = len(response.split()) if response else 1
            await asyncio.sleep(0.3)  # Brief pause before idle
            self.state_manager.force_state("idle")
            
            # Final state broadcast
            await self._send_to(websocket, json.dumps({
                'type': 'state',
                'state': self.state_manager.get_full_state()
            }))
        
        elif msg_type == 'switch_voice':
            voice = data.get('voice', 'jarvis')
            if voice.lower() == 'friday':
                self.hud_perception.switch_to_friday()
            else:
                self.hud_perception.switch_to_jarvis()
            
            await self._send_to(websocket, json.dumps({
                'type': 'assistant_info',
                'name': self.hud_perception.assistant_name,
                'is_friday': self.hud_perception.is_friday
            }))
            
            # Get pending speech
            speeches = self.hud_perception.get_pending_speech()
            for speech in speeches:
                await self._send_to(websocket, json.dumps({
                    'type': 'response',
                    'text': speech,
                    'speak': not bool(getattr(self, 'live_engine', None))
                }))
        
        elif msg_type == 'get_status':
            await self._send_to(websocket, json.dumps(self.get_system_stats()))
        
        elif msg_type == 'get_state':
            # NEW: Broadcast complete JARVIS state - UI mirrors this
            full_state = self.state_manager.get_full_state()
            # Also include system stats for convenience
            full_state['cpu'] = psutil.cpu_percent(interval=0.1)
            full_state['memory'] = psutil.virtual_memory().percent
            full_state['battery'] = getattr(psutil.sensors_battery() or type('', (), {'percent': 100})(), 'percent')
            await self._send_to(websocket, json.dumps({
                'type': 'state',
                'state': full_state
            }))
            print(f"[WebSocket] Sent full state: gesture={full_state.get('gesture_enabled')}, face={full_state.get('face_enabled')}, mood={full_state.get('emotion_enabled')}")
        
        elif msg_type == 'get_weather':
            city = data.get('city')
            await self._send_to(websocket, json.dumps(self.get_weather_data(city)))
        
        elif msg_type == 'get_news':
            category = data.get('category', 'general')
            location = data.get('location')
            await self._send_to(websocket, json.dumps(self.get_news_data(category, location=location)))
        
        elif msg_type == 'globe_hover':
            # Handle globe location hover
            location = data.get('location', '')
            if location:
                news = self.get_news_data(location=location)
                await self._send_to(websocket, json.dumps(news))
        
        elif msg_type == 'toggle_feature':
            # Toggle gesture/face/emotion features
            feature = data.get('feature', '')
            enabled = data.get('enabled', False)
            
            if feature == 'gesture':
                self.gesture_enabled = enabled
                if enabled and self.gesture_controller:
                    self.gesture_controller.enable_tracking()
                elif self.gesture_controller:
                    self.gesture_controller.disable_tracking()
            elif feature == 'face':
                self.face_enabled = enabled
                if enabled and self.face_recognition:
                    self.face_recognition.start_monitoring()
                elif self.face_recognition:
                    self.face_recognition.stop_monitoring()
            elif feature == 'emotion':
                self.emotion_enabled = enabled
            
            await self._send_to(websocket, json.dumps(self.get_feature_status()))
        
        elif msg_type == 'get_features':
            await self._send_to(websocket, json.dumps(self.get_feature_status()))
    
    def _try_fast_path(self, text: str):
        """Instant execution for common commands — no routing chain."""
        cmd = text.lower().strip()
        import re as _re
        title = getattr(self, 'hud_perception', None)
        title = title.user_title if title else 'sir'
        
        # ── CLOSE APP (instant via taskkill) ──
        close_match = _re.match(r'^close\s+(.+)', cmd)
        if close_match:
            app = close_match.group(1).strip()
            try:
                import subprocess
                # Map common names to process names
                APP_PROCESS = {
                    'whatsapp': 'WhatsApp', 'chrome': 'chrome',
                    'brave': 'brave', 'firefox': 'firefox',
                    'spotify': 'Spotify', 'discord': 'Discord',
                    'notepad': 'notepad', 'calculator': 'Calculator',
                    'edge': 'msedge', 'vscode': 'Code', 'vs code': 'Code',
                    'telegram': 'Telegram', 'explorer': 'explorer',
                }
                proc = APP_PROCESS.get(app, app)
                subprocess.run(f'taskkill /IM {proc}.exe /F', shell=True,
                             capture_output=True, timeout=3)
                print(f"[FAST] Closed {app}")
                return f"Closed {app}, {title}."
            except Exception:
                return None  # Fall through to normal pipeline
        
        # ── RESUME/PAUSE VIDEO (space key, not media keys) ──
        if any(w in cmd for w in ['resume video', 'resume the video', 'play video',
                                   'pause video', 'pause the video', 'resume youtube',
                                   'play youtube', 'pause youtube']):
            try:
                import pyautogui
                pyautogui.press('space')  # Space = play/pause in YouTube
                action = 'Resumed' if 'resume' in cmd or 'play' in cmd else 'Paused'
                print(f"[FAST] {action} video (space key)")
                return f"{action} the video, {title}."
            except Exception:
                return None
        
        # ── SCREENSHOT (instant) ──
        if 'screenshot' in cmd or 'screen capture' in cmd:
            try:
                import pyautogui
                from pathlib import Path
                import datetime
                ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                path = Path.home() / 'Pictures' / f'jarvis_screenshot_{ts}.png'
                pyautogui.screenshot(str(path))
                print(f"[FAST] Screenshot saved: {path}")
                return f"Screenshot saved, {title}."
            except Exception:
                return None
        
        # ── VOLUME (instant) ──
        if 'volume' in cmd:
            if self.system_control:
                if 'up' in cmd or 'increase' in cmd:
                    self.system_control.volume_up()
                    return f"Volume up, {title}."
                elif 'down' in cmd or 'decrease' in cmd:
                    self.system_control.volume_down()
                    return f"Volume down, {title}."
                elif 'mute' in cmd:
                    self.system_control.mute_volume()
                    return f"Muted, {title}."
                num = _re.search(r'(\d+)', cmd)
                if num:
                    self.system_control.set_volume(int(num.group(1)))
                    return f"Volume set to {num.group(1)}%, {title}."
        
        # ── BRIGHTNESS (instant) ──
        if 'brightness' in cmd:
            if self.system_control:
                if 'up' in cmd or 'increase' in cmd:
                    self.system_control.brightness_up()
                    return f"Brightness up, {title}."
                elif 'down' in cmd or 'decrease' in cmd:
                    self.system_control.brightness_down()
                    return f"Brightness down, {title}."
                num = _re.search(r'(\d+)', cmd)
                if num:
                    self.system_control.set_brightness(int(num.group(1)))
                    return f"Brightness set to {num.group(1)}%, {title}."
        
        # ── PLAY IN YOUTUBE (instant — prevents Spotify conflict) ──
        yt_match = _re.search(r'play\s+(.+?)\s+(?:in|on)\s+youtube', cmd)
        if yt_match:
            query = yt_match.group(1).strip()
            try:
                import urllib.parse, webbrowser, threading
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                webbrowser.open(url)
                # Auto-click first video after page loads
                def _auto_play():
                    import time, pyautogui
                    time.sleep(3.5)
                    pyautogui.press('tab', presses=8, interval=0.05)
                    time.sleep(0.2)
                    pyautogui.press('enter')
                threading.Thread(target=_auto_play, daemon=True).start()
                print(f"[FAST] YouTube search: {query}")
                return f"Playing {query} on YouTube, {title}."
            except Exception:
                return None
        
        # ── OPEN APP (instant) ──
        open_match = _re.match(r'^(?:open|launch|start)\s+(.+)', cmd)
        if open_match:
            app = open_match.group(1).strip()
            try:
                # Try AppSwitcher first, then fallback to os.startfile
                switcher = getattr(self, 'app_switcher', None)
                if switcher and hasattr(switcher, 'open_app'):
                    switcher.open_app(app)
                else:
                    import subprocess
                    subprocess.Popen(f'start {app}', shell=True)
                print(f"[FAST] Opened {app}")
                return f"Opening {app}, {title}."
            except Exception:
                return None
        
        # ── TIME (instant) ──
        if cmd in ['time', 'what time is it', 'what is the time', 'tell me the time', "what's the time"]:
            from datetime import datetime
            now = datetime.now().strftime('%I:%M %p')
            return f"It's {now}, {title}."
        
        # ── DATE (instant) ──
        if cmd in ['date', 'what date is it', "what's the date", 'what is the date', "what's today's date"]:
            from datetime import datetime
            now = datetime.now().strftime('%A, %B %d, %Y')
            return f"It's {now}, {title}."
        
        # ── STOP / PAUSE / RESUME VIDEO (instant) ──
        if any(p in cmd for p in ['stop video', 'pause video', 'stop the video', 'pause the video',
                                   'resume video', 'resume the video', 'unpause',
                                   'stop playing', 'stop music', 'pause music',
                                   'play pause', 'play/pause']):
            try:
                import pyautogui
                pyautogui.press('space')
                print(f"[FAST] Toggled playback")
                if 'resume' in cmd or 'unpause' in cmd:
                    return f"Resuming playback, {title}."
                return f"Paused, {title}."
            except Exception:
                return None
        
        return None  # No fast path — use normal pipeline

    def _split_compound_command(self, text: str) -> list:
        """Split compound commands — delegates to command_processor module."""
        return _split_compound_command(text)

    async def process_command(self, command: str, websocket) -> str:
        """Process command through HUD handlers or full JARVIS"""
        cmd = command.lower().strip()
        name = self.hud_perception.assistant_name
        title = self.hud_perception.user_title
        
        # ══════════════════════════════════════════════════════════════════
        # STRIP WAKE WORD: "jarvis open perplexity" → "open perplexity"
        # Voice input includes the wake word — strip it before routing
        # ══════════════════════════════════════════════════════════════════
        # M-07: Using module-level re import instead of inline
        cmd = re.sub(r'^(?:hey\s+)?(?:jarvis|friday)[,!.\s]*', '', cmd, flags=re.I).strip()
        if not cmd:
            hour = datetime.now().hour
            greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening" if hour < 21 else "Hey there"
            return f"{greeting}, {title}. How may I help?"
        
        # ══════════════════════════════════════════════════════════════════
        # SPEECH INTERRUPTION: "stop", "shut up", "keep quiet", "silence"
        # Must be first — user wants to interrupt JARVIS immediately
        # ══════════════════════════════════════════════════════════════════
        stop_words = ['stop', 'shut up', 'be quiet', 'silence', 'enough', 'okay stop',
                      'stop talking', 'stop speaking', 'quiet', 'hush',
                      'keep quiet', 'stay silent', 'keep silent', 'stfu',
                      'stop the fuck up', 'shut the fuck up']
        if cmd in stop_words or cmd.startswith('stop ') or 'keep quiet' in cmd or 'stay silent' in cmd:
            self._stop_speaking()
            self.quiet_mode = True  # Pause voice listening until wake word
            self._silent_response = True  # Don't speak the response
            print("[VOICE] Quiet mode ON - mic paused until wake word")
            return f"Understood{maybe_title(title)}. Say my name when you need me."
        
        # ══════════════════════════════════════════════════════════════════
        # RESUME FROM QUIET: "back online", "come back", "I need you"
        # ══════════════════════════════════════════════════════════════════
        resume_words = ['back online', 'come back', 'i need you', 'unmute', 'talk to me']
        if any(r in cmd for r in resume_words):
            self.quiet_mode = False
            print("[VOICE] Quiet mode OFF - JARVIS back online")
            return f"I'm back online{maybe_title(title)}. What do you need?"
        
        # ══════════════════════════════════════════════════════════════════
        # SHUTDOWN: Actually exit the JARVIS process
        # Uses word boundaries to avoid false matches (e.g. 'perplexity' has 'exit')
        # ══════════════════════════════════════════════════════════════════
        # M-07: Using module-level re import instead of inline
        shutdown_patterns = [r'\bshutdown\b', r'\bshut\s+down\b', r'\bpower\s+off\b', 
                            r'\bgo\s+offline\b', r'\bexit\s+jarvis\b', r'\bquit\s+jarvis\b',
                            r'\bjarvis\s+shutdown\b']
        if any(re.search(p, cmd) for p in shutdown_patterns):
            import os, signal
            farewell = f"Shutting down all systems. Until next time{maybe_title(title)}."
            self._silent_response = True  # Don't speak the farewell
            # Schedule actual exit after response is sent
            async def _shutdown():
                await asyncio.sleep(3)
                self.running = False
                os.kill(os.getpid(), signal.SIGTERM)
            asyncio.ensure_future(_shutdown())
            return farewell
        
        # ══════════════════════════════════════════════════════════════════
        # BLUETOOTH TOGGLE: on/off
        # ══════════════════════════════════════════════════════════════════
        if 'bluetooth' in cmd and any(w in cmd for w in ['off', 'disable', 'switch off', 'turn off']):
            try:
                subprocess.run(['powershell', '-Command',
                    'Add-Type -AssemblyName System.Runtime.WindowsRuntime; '
                    '[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null; '
                    '$radios = [Windows.Devices.Radios.Radio]::GetRadiosAsync().AsTask().Result; '
                    '$bt = $radios | Where-Object { $_.Kind -eq "Bluetooth" }; '
                    '$bt.SetStateAsync("Off").AsTask().Result'],
                    capture_output=True, timeout=10)
                return f"Bluetooth is now off{maybe_title(title)}."
            except Exception:
                # Fallback: open bluetooth settings
                subprocess.Popen(['start', 'ms-settings:bluetooth'], shell=True)
                return f"Opening Bluetooth settings{maybe_title(title)}. Please toggle it manually."
        
        if 'bluetooth' in cmd and any(w in cmd for w in ['on', 'enable', 'switch on', 'turn on']):
            try:
                subprocess.run(['powershell', '-Command',
                    'Add-Type -AssemblyName System.Runtime.WindowsRuntime; '
                    '[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null; '
                    '$radios = [Windows.Devices.Radios.Radio]::GetRadiosAsync().AsTask().Result; '
                    '$bt = $radios | Where-Object { $_.Kind -eq "Bluetooth" }; '
                    '$bt.SetStateAsync("On").AsTask().Result'],
                    capture_output=True, timeout=10)
                return f"Bluetooth is now on{maybe_title(title)}."
            except Exception:
                subprocess.Popen(['start', 'ms-settings:bluetooth'], shell=True)
                return f"Opening Bluetooth settings{maybe_title(title)}. Please toggle it manually."
        
        # ══════════════════════════════════════════════════════════════════
        # LAPTOP SHUTDOWN / RESTART
        # ══════════════════════════════════════════════════════════════════
        if any(p in cmd for p in ['switch off laptop', 'shutdown laptop', 'shut down laptop',
                                   'turn off laptop', 'switch off computer', 'shutdown computer',
                                   'turn off computer', 'power off laptop', 'power off computer',
                                   'switch off the laptop', 'turn off the laptop', 'shut down the laptop',
                                   'switch off the computer', 'turn off the computer']):
            subprocess.Popen(['shutdown', '/s', '/t', '5'], shell=True)
            return f"Shutting down the laptop in 5 seconds{maybe_title(title)}. Save your work."
        
        if any(p in cmd for p in ['restart laptop', 'restart computer', 'reboot',
                                   'restart the laptop', 'restart the computer']):
            subprocess.Popen(['shutdown', '/r', '/t', '5'], shell=True)
            return f"Restarting the laptop in 5 seconds{maybe_title(title)}."
        
        # ══════════════════════════════════════════════════════════════════
        # PRE-ROUTER OVERRIDES: Commands the ML classifier gets wrong
        # These explicit keyword matches run BEFORE the intent router
        # ══════════════════════════════════════════════════════════════════
        
        # Bedtime story — classifier thinks this is 'get_time' because 'time' is in 'bedtime'
        if any(w in cmd for w in ['bedtime story', 'bed time story', 'tell me a story', 
                                   'tell a story', 'once upon', 'tell me a tale']):
            # Route to AI knowledge layer for story generation
            if self.jarvis and hasattr(self.jarvis, 'knowledge') and self.jarvis.knowledge:
                story = self.jarvis.knowledge.answer_question(cmd)
                if story:
                    return story
            if self.knowledge:
                story = self.knowledge.answer_question(cmd)
                if story:
                    return story
            return f"Once upon a time, in a kingdom far, far away... I'd tell you more, but my storytelling module needs a moment{maybe_title(title)}."
        
        # Chat History — classifier thinks this is 'story'
        if ('chat history' in cmd or 'show history' in cmd or 'conversation history' in cmd) and self.chat_history:
            if 'search' in cmd:
                import re
                match = re.search(r'search\s+(?:for\s+)?(.+)', cmd, re.I)
                if match:
                    query = match.group(1).strip()
                    results = self.chat_history.search(query)
                    if results:
                        return f"Found {len(results)} conversations matching '{query}', {title}."
                    return f"No conversations found matching '{query}', {title}."
            elif 'clear' in cmd or 'delete' in cmd:
                self.chat_history.clear_history()
                return f"Chat history cleared, {title}."
            else:
                messages = self.chat_history.get_recent(5)
                if messages:
                    summary = "; ".join([f"{m.role}: {m.content[:40]}" for m in messages[-3:]])
                    return f"Recent chat history, {title}: {summary}"
                return f"No chat history yet, {title}."
        
        # App Switching — classifier thinks 'go back' is 'previous_track'
        if cmd in ('go back', 'alt tab', 'switch window', 'next window', 'previous window'):
            try:
                import pyautogui
                pyautogui.hotkey('alt', 'tab')
                return f"Switched to the previous window, {title}."
            except Exception as e:
                return f"Couldn't switch windows, {title}."
        
        # App focus — 'switch to [app]' / 'switch with [app]' / 'switch tab to [app]' / 'go to [app]'
        switch_prefixes = ('switch to ', 'switch with ', 'switch tab to ', 'go to ', 'switch tab ')
        if any(cmd.startswith(p) for p in switch_prefixes) and cmd.split()[-1] not in ('friday', 'jarvis'):
            target = cmd
            for p in switch_prefixes:
                target = target.replace(p, '', 1)
            target = target.strip()
            try:
                import pyautogui, subprocess
                result = subprocess.run(
                    ['powershell', '-command',
                     f'(Get-Process | Where-Object {{$_.MainWindowTitle -match "{target}"}} | Select-Object -First 1).MainWindowTitle'],
                    capture_output=True, text=True, timeout=3
                )
                window_title = result.stdout.strip()
                if window_title:
                    subprocess.run(
                        ['powershell', '-command', f'''
                        $window = Get-Process | Where-Object {{$_.MainWindowTitle -match "{target}"}} | Select-Object -First 1
                        if ($window) {{
                            $hwnd = $window.MainWindowHandle
                            Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class Win32 {{ [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow); }}'
                            [Win32]::ShowWindow($hwnd, 9)
                            [Win32]::SetForegroundWindow($hwnd)
                        }}
                        '''],
                        capture_output=True, timeout=3
                    )
                    self.state_manager.active_app = target.lower()
                    self.state_manager._active_app_time = time.time()
                    return f"Switching to {target}, {title}."
                else:
                    return f"I can't find {target} running. Would you like me to open it?"
            except Exception as e:
                return f"Couldn't switch to {target}, {title}."
        
        # ══════════════════════════════════════════════════════════════════
        # REMINDERS — Route directly, don't let it fall to face-auth gate
        # ══════════════════════════════════════════════════════════════════
        if ('remind' in cmd or 'reminder' in cmd) and 'email' not in cmd:
            if self.reminder_manager:
                # "list reminders" / "show reminders" / "my reminders"
                if 'list' in cmd or 'show' in cmd or 'my' in cmd:
                    result = self.reminder_manager.read_reminders()
                    return result if result else f"No upcoming reminders, {title}."
                
                # "set reminder to drink water in 30 minutes"
                # "remind me to call mom at 5pm"
                success = self.reminder_manager.set_reminder_from_command(cmd)
                if success:
                    return f"Reminder set, {title}."
                return f"I couldn't parse that reminder. Try: 'remind me to X in 30 minutes', {title}."
        
        # ══════════════════════════════════════════════════════════════════
        # OPEN APP — Execute IMMEDIATELY, skip ML classifier entirely
        # This is the #1 user complaint: "open X" says it opened but didn't
        # ══════════════════════════════════════════════════════════════════
        import re as _re
        open_match = _re.match(r'^(?:open|launch|start|run)\s+(.+)', cmd, _re.I)
        if open_match:
            app_name = open_match.group(1).strip()
            import os, subprocess
            
            # Direct app map — no ML, no API, no lag
            DIRECT_APPS = {
                'calculator': 'calc', 'calc': 'calc',
                'notepad': 'notepad', 'paint': 'mspaint',
                'cmd': 'cmd', 'terminal': 'wt',
                'powershell': 'powershell',
                'file explorer': 'explorer', 'explorer': 'explorer',
                'file manager': 'explorer', 'files': 'explorer',
                'this pc': 'explorer', 'my computer': 'explorer',
                'settings': 'ms-settings:', 'task manager': 'taskmgr',
                'control panel': 'control',
                'device manager': 'devmgmt.msc',
                'snipping tool': 'SnippingTool',
                'wifi': 'ms-settings:network-wifi',
                'wifi settings': 'ms-settings:network-wifi',
                'bluetooth': 'ms-settings:bluetooth',
                'bluetooth settings': 'ms-settings:bluetooth',
                'display settings': 'ms-settings:display',
                'sound settings': 'ms-settings:sound',
                'apps': 'ms-settings:appsfeatures',
                'installed apps': 'ms-settings:appsfeatures',
                'photos': 'ms-photos:',
                'camera': 'microsoft.windows.camera:',
                'store': 'ms-windows-store:',
                'microsoft store': 'ms-windows-store:',
                'chrome': 'chrome', 'firefox': 'firefox',
                'edge': 'msedge', 'microsoft edge': 'msedge', 'brave': 'brave',
                'vscode': 'code', 'vs code': 'code',
                'spotify': 'spotify:', 'discord': 'discord:',
                'telegram': 'telegram:', 'whatsapp': 'whatsapp:',
                'whatsapp beta': 'whatsapp:', 
            }
            
            WEB_APPS = {
                'chatgpt': 'https://chat.openai.com',
                'perplexity': 'https://perplexity.ai',
                'youtube': 'https://youtube.com',
                'gmail': 'https://mail.google.com',
                'google': 'https://google.com',
                'claude': 'https://claude.ai',
                'github': 'https://github.com',
            }
            
            app_lower = app_name.lower()
            
            # Try direct map first
            if app_lower in DIRECT_APPS:
                target = DIRECT_APPS[app_lower]
                try:
                    if target.startswith('http') or target.startswith('ms-') or target.endswith(':'):
                        os.startfile(target)
                    else:
                        subprocess.Popen(target, shell=True)
                    return f"Opening {app_name}, {title}."
                except Exception as e:
                    return f"Error opening {app_name}: {e}"
            
            # Try web apps
            if app_lower in WEB_APPS:
                import webbrowser
                webbrowser.open(WEB_APPS[app_lower])
                return f"Opening {app_name} in browser, {title}."
            
            # Try AppFinder for everything else
            if self.jarvis and hasattr(self.jarvis, 'app_finder'):
                try:
                    success = self.jarvis.app_finder.open_app(app_lower)
                    if success:
                        return f"Opening {app_name}, {title}."
                except Exception:
                    pass
            
            # Try os.startfile as last resort
            try:
                os.startfile(app_lower)
                return f"Opening {app_name}, {title}."
            except Exception:
                # Search Start Menu
                try:
                    from jarvis.core.app_finder import AppFinder
                    finder = AppFinder()
                    success = finder.open_app(app_lower)
                    if success:
                        return f"Opening {app_name}, {title}."
                except Exception:
                    pass
            
            return f"Couldn't find {app_name}, {title}. Try the exact name."
        
        # Habits — classifier thinks this is 'conversation'
        if 'habit' in cmd and self.habit_tracker:
            if 'create' in cmd or 'add' in cmd or 'new' in cmd:
                import re
                match = re.search(r'(?:create|add|new)\s+habit\s+(.+?)(?:\s+every\s+|\s+daily|\s+hourly|$)', cmd, re.I)
                if match:
                    desc = match.group(1).strip()
                    self.habit_tracker.create_habit(desc, cmd)
                    return f"Habit '{desc}' created, {title}."
                return f"Please specify a habit, {title}. Say 'add habit drink water'."
            elif 'list' in cmd or 'show' in cmd or 'my habits' in cmd:
                self.habit_tracker.list_habits()
                return f"Listing your habits, {title}."
            elif 'check' in cmd:
                reminders = self.habit_tracker.check_reminders()
                if reminders:
                    return f"You have {len(reminders)} habit reminders, {title}."
                return f"No habit reminders due, {title}."
        
        # Tasks — classifier thinks this is 'conversation'
        if ('task' in cmd or 'todo' in cmd or 'to do' in cmd) and self.task_manager_obj:
            if 'add' in cmd or 'create' in cmd or 'new' in cmd:
                import re
                match = re.search(r'(?:add|create|new)\s+(?:a\s+)?task\s+(.+)', cmd, re.I)
                if match:
                    desc = match.group(1).strip()
                    if hasattr(self.task_manager_obj, 'add_task'):
                        self.task_manager_obj.add_task(desc)
                    elif hasattr(self.task_manager_obj, 'create_task'):
                        self.task_manager_obj.create_task(desc)
                    return f"Task added: '{desc}', {title}."
            elif 'list' in cmd or 'show' in cmd or 'my task' in cmd:
                if hasattr(self.task_manager_obj, 'list_tasks'):
                    result = self.task_manager_obj.list_tasks()
                elif hasattr(self.task_manager_obj, 'get_tasks'):
                    result = self.task_manager_obj.get_tasks()
                else:
                    result = None
                return result if isinstance(result, str) else f"Listing your tasks, {title}."
        
        # Wellness — classifier thinks this is 'conversation'
        if 'wellness' in cmd and self.wellness_monitor:
            if 'summary' in cmd or 'status' in cmd:
                summary = self.wellness_monitor.get_wellness_summary()
                return summary if isinstance(summary, str) else f"Your wellness looks good, {title}."
            elif 'check' in cmd:
                reminder = self.wellness_monitor.check_wellness()
                return reminder if reminder else f"You're doing well, {title}."
            elif 'reset' in cmd or 'took a break' in cmd:
                self.wellness_monitor.reset_session()
                return f"Session reset. Good on you for taking a break, {title}."
        
        # ══════════════════════════════════════════════════════════════════
        # EMAIL — send/check/read emails directly, skip ML classifier
        # ══════════════════════════════════════════════════════════════════
        if ('email' in cmd or 'mail' in cmd or 'gmail' in cmd) and self.email_handler_obj:
            import re as _re
            
            # Send email: "send email to user@example.com saying hello"
            send_match = _re.search(r'send\s+(?:a\s+)?(?:email|mail)\s+to\s+(\S+@\S+)\s+(?:saying|about|subject|with)?\s*(.*)', cmd, _re.I)
            if send_match:
                to_email = send_match.group(1).strip()
                body = send_match.group(2).strip() or "Hello from JARVIS"
                subject = body[:50] + "..." if len(body) > 50 else body
                result = self.email_handler_obj.send_email(to_email, subject, body)
                return result
            
            # Send reminder email to self
            if 'remind' in cmd and 'email' in cmd:
                reminder_text = _re.sub(r'.*(?:remind|email).*?(?:to|about|that)\s+', '', cmd, flags=_re.I).strip()
                if reminder_text:
                    result = self.email_handler_obj.send_reminder_email(reminder_text)
                    return result or f"Reminder email sent, {title}."
            
            # Summarize emails
            if 'summarize' in cmd or 'summary' in cmd:
                result = self.email_handler_obj.summarize_emails()
                return f"Here's your email summary, {title}. {result}" if isinstance(result, str) else f"Summarizing your emails, {title}."
            
            # Check/read unread emails
            if any(w in cmd for w in ['check', 'read', 'unread', 'inbox', 'show']):
                result = self.email_handler_obj.get_unread_emails()
                return f"Checking your inbox, {title}. {result}" if isinstance(result, str) else f"Checking your emails, {title}."
            
            # Default: check inbox
            result = self.email_handler_obj.get_unread_emails()
            return f"Checking your inbox, {title}. {result}" if isinstance(result, str) else f"Checking your emails, {title}."
        
        # PDF — no handler existed before
        if ('read pdf' in cmd or 'open pdf' in cmd or 'pdf' in cmd) and self.pdf_handler:
            if hasattr(self.pdf_handler, 'extract_text'):
                return f"PDF handler ready, {title}. Please specify a file path."
            return f"PDF handler available, {title}."
        
        # ══════════════════════════════════════════════════════════════════
        # TRY INTENTROUTER FIRST - Clean, simple responses
        # This prevents verbose Gemini AI responses for known commands
        # ══════════════════════════════════════════════════════════════════
        router_response = self._route_through_router(command)
        # Check if router gave a REAL answer (not a fallback error)
        _error_phrases = ['trouble connecting', 'knowledge base', 'currently offline', 
                          'encountered an issue', 'Set GROQ_API_KEY']
        if router_response and not any(ep in (router_response or '') for ep in _error_phrases):
            return router_response
        
        # Special handling for news categories
        news_categories = ['economics', 'economy', 'business', 'politics', 'technology', 
                          'tech', 'sports', 'entertainment', 'world', 'global']
        
        for category in news_categories:
            if category in cmd and ('news' in cmd or 'headlines' in cmd):
                # Update news panel with category-specific news
                news_data = self.get_news_data(category=category)
                await self._send_to(websocket, json.dumps(news_data))
                
                items = news_data['items'][:3]
                items_text = ". ".join(items)
                return f"Here are the top {category} headlines, {title}: {items_text}"
        
        # ══════════════════════════════════════════════════════════════════
        # TRY HUD-SPECIFIC COMMANDS FIRST (before full JARVIS)
        # These are features we want to handle in the HUD directly
        # ══════════════════════════════════════════════════════════════════
        
        hud_commands = [
            'screenshot', 'capture screen',
            'read screen', 'read text', 'extract text', 'ocr',
            'read clipboard',
            'define ', 'meaning of ', 'definition of ',
            'synonym',
            'register my face', 'register face', 'register owner',
            'verify me', 'authenticate', 'who am i',
            'enable gesture', 'start gesture', 'gesture on',
            'disable gesture', 'stop gesture', 'gesture off',
            'enable emotion', 'mood detection', 'disable emotion',
            'tell me a story', 'tell a story',
            'recite a poem', 'poem',
            'riddle',
            'create note', 'new note', 'add note',
            'list notes', 'show notes', 'my notes',
            'set alarm',
            'list alarm', 'show alarm', 'my alarm',
            'switch to friday', 'activate friday',
            'switch to jarvis', 'activate jarvis'
        ]
        
        # Check if this is a HUD-specific command
        is_hud_command = any(cmd_pattern in cmd for cmd_pattern in hud_commands)
        
        if is_hud_command:
            # Process through our HUD handlers directly
            return await self._fallback_process(command, websocket)
        
        # For general queries, use fast Gemini API (skip heavy JARVIS pipeline)
        try:
            import google.genai as _genai
            _api_key = getattr(self, '_gemini_key', None)
            if not _api_key:
                import os
                _api_key = os.getenv('GEMINI_API_KEY', '')
                self._gemini_key = _api_key
            if _api_key:
                _client = _genai.Client(api_key=_api_key)
                _resp = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, lambda: _client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=f"You are JARVIS, a witty AI assistant. Keep replies to 1-2 sentences. Address user as 'sir'. Never break character. User says: {command}"
                    )),
                    timeout=5.0
                )
                if _resp and _resp.text:
                    return _resp.text.strip()
        except asyncio.TimeoutError:
            print(f"[WebSocket] Gemini API timed out (5s)")
        except Exception as e:
            print(f"[WebSocket] Gemini API error: {e}")
        
        # Final fallback
        return await self._fallback_process(command, websocket)
    
    def _route_through_router(self, command: str) -> str:
        """Route command through direct handlers first, then IntentRouter"""
        
        try:
            title = self.hud_perception.user_title

            # ══════════════════════════════════════════════════════════════
            # BRAIN-FIRST: Run through advanced ML pipeline before keywords
            # If the brain returns a valid high-confidence result, use its
            # intent + entities. Otherwise fall through to keyword engine.
            # ══════════════════════════════════════════════════════════════
            brain_result = None
            if getattr(self, '_brain', None):
                try:
                    brain_result = self._brain.process(command, source="voice")
                except Exception as be:
                    print(f"[WebSocket] Brain error (non-fatal): {be}")

            if brain_result and brain_result.is_valid:
                # Brain produced a confident result — use it
                intent_name = brain_result.action
                entities = brain_result.entities
                if jlog: jlog.intent(f"BRAIN:{intent_name}", entities=entities)
                else: print(f"[WebSocket] BRAIN Intent: {intent_name}, Entities: {entities}, Conf: {brain_result.confidence:.2f}")

                # If decision engine says CLARIFY or REFUSE, return that message
                if brain_result.decision_type in ('clarify', 'refuse') and brain_result.decision_message:
                    return brain_result.decision_message
                # If decision engine says WARN, prepend warning
                if brain_result.decision_type == 'warn' and brain_result.decision_message:
                    # Store warning to prepend to final response
                    self._brain_warning = brain_result.decision_message
            else:
                # Fallback to keyword-based classifier
                intent_name, entities = classify_intent(command)
                if jlog: jlog.intent(intent_name, entities=entities)
                else: print(f"[WebSocket] Intent: {intent_name}, Entities: {entities}")
            
            # ══════════════════════════════════════════════════════════════
            # CONTEXT RESOLUTION: Disambiguate based on active_app
            # "next" → next_track (spotify) or next_page (pdf) etc.
            # ══════════════════════════════════════════════════════════════
            active_app = getattr(self.state_manager, 'active_app', None)
            
            # Clear stale context (5 min timeout)
            app_set_time = getattr(self.state_manager, '_active_app_time', 0)
            if active_app and (time.time() - app_set_time) > 300:
                active_app = None
                self.state_manager.active_app = None
            
            CONTEXT_MAP = {
                'next': {
                    'spotify': 'next_track', 'music': 'next_track',
                    'pdf': 'next_page', 'reader': 'next_page',
                    'browser': 'next_tab', 'chrome': 'next_tab',
                },
                'previous': {
                    'spotify': 'previous_track', 'music': 'previous_track',
                    'pdf': 'previous_page', 'reader': 'previous_page',
                },
                'scroll': {
                    'pdf': 'scroll_pdf', 'browser': 'scroll_page',
                },
            }
            
            if intent_name in CONTEXT_MAP and active_app:
                app_key = active_app.lower()
                mapping = CONTEXT_MAP[intent_name]
                for key, resolved in mapping.items():
                    if key in app_key:
                        if jlog: jlog.intent(f'{intent_name}→{resolved}', context=active_app)
                        intent_name = resolved
                        break
            
            # ══════════════════════════════════════════════════════════════
            # DIRECT HANDLERS: Critical system commands that MUST execute
            # These bypass the router to guarantee actual hardware control
            # ══════════════════════════════════════════════════════════════
            
            # --- VOLUME ---
            if intent_name == 'volume' and self.system_control:
                action = entities.get('action', '')
                level = entities.get('level')
                if action == 'set' and level is not None:
                    if jlog: jlog.route('SystemControl', 'set_volume')
                    result = self.system_control.set_volume(level)
                    return result if isinstance(result, str) else f"Volume set to {level}%, {title}."
                elif action == 'up':
                    result = self.system_control.volume_up()
                    return result if isinstance(result, str) else f"Volume increased, {title}."
                elif action == 'down':
                    result = self.system_control.volume_down()
                    return result if isinstance(result, str) else f"Volume decreased, {title}."
                elif action == 'mute':
                    result = self.system_control.mute_volume()
                    return result if isinstance(result, str) else f"Volume muted, {title}."
                else:
                    # No specific action, try to extract number from command
                    import re
                    match = re.search(r'(\d+)\s*%?', command)
                    if match:
                        level = int(match.group(1))
                        result = self.system_control.set_volume(min(100, max(0, level)))
                        return result if isinstance(result, str) else f"Volume set to {level}%, {title}."
                    result = self.system_control.volume_up()
                    return result if isinstance(result, str) else f"Volume increased, {title}."
            
            # --- BRIGHTNESS ---
            if intent_name == 'brightness' and self.system_control:
                action = entities.get('action', '')
                level = entities.get('level')
                if action == 'set' and level is not None:
                    if jlog: jlog.route('SystemControl', 'set_brightness')
                    result = self.system_control.set_brightness(level)
                    return result if isinstance(result, str) else f"Brightness set to {level}%, {title}."
                elif action == 'up':
                    result = self.system_control.brightness_up()
                    return result if isinstance(result, str) else f"Brightness increased, {title}."
                elif action == 'down':
                    result = self.system_control.brightness_down()
                    return result if isinstance(result, str) else f"Brightness decreased, {title}."
                else:
                    import re
                    match = re.search(r'(\d+)\s*%?', command)
                    if match:
                        level = int(match.group(1))
                        result = self.system_control.set_brightness(min(100, max(0, level)))
                        return result if isinstance(result, str) else f"Brightness set to {level}%, {title}."
                    result = self.system_control.brightness_up()
                    return result if isinstance(result, str) else f"Brightness increased, {title}."
            
            # --- ALARM ---
            if intent_name == 'set_alarm' and self.alarm_system:
                import re
                from datetime import datetime, timedelta
                cmd_lower = command.lower()
                
                # Handle relative time: "5 minutes from now", "in 10 minutes"
                relative_match = re.search(r'(\d+)\s*(min|minute|minutes|hour|hours|hr|hrs)\s*(from now)?', cmd_lower)
                if relative_match:
                    amount = int(relative_match.group(1))
                    unit = relative_match.group(2)
                    if 'hour' in unit or 'hr' in unit:
                        alarm_time = datetime.now() + timedelta(hours=amount)
                    else:
                        alarm_time = datetime.now() + timedelta(minutes=amount)
                    time_str = alarm_time.strftime('%I:%M %p')
                    label = entities.get('label', 'Alarm')
                    result = self.alarm_system.set_alarm(time_str, label)
                    return result if isinstance(result, str) else f"Alarm set for {time_str} ({amount} {'hours' if 'hour' in unit else 'minutes'} from now), {title}."
                
                # Handle absolute time from entities
                hour = entities.get('hour')
                minute = entities.get('minute', 0)
                period = entities.get('period', '')
                if hour is not None:
                    time_str = f"{hour}:{minute:02d} {period}".strip()
                    label = entities.get('label', 'Alarm')
                    result = self.alarm_system.set_alarm(time_str, label)
                    return result if isinstance(result, str) else f"Alarm set for {time_str}, {title}."
                
                return f"What time should I set the alarm for, {title}?"
            
            if intent_name == 'list_alarms' and self.alarm_system:
                alarms = self.alarm_system.scheduler.get_all()
                if not alarms:
                    return f"No active alarms, {title}."
                alarm_list = ", ".join([f"{a.label} at {a.trigger_time.strftime('%I:%M %p')}" for a in alarms])
                return f"Active alarms: {alarm_list}, {title}."
            
            # --- OPEN APP ---
            if intent_name == 'open_app':
                app_name = entities.get('app', '')
                if app_name:
                    try:
                        from jarvis.core.app_finder import AppFinder
                        finder = AppFinder()
                        success = finder.open_app(app_name)
                        if success:
                            self.state_manager.active_app = app_name.lower()
                            self.state_manager._active_app_time = time.time()
                            if jlog: jlog.state(active_app=app_name.lower())
                            return f"Opening {app_name}, {title}."
                        else:
                            return f"Couldn't find {app_name}, {title}. Try the full name."
                    except Exception as e:
                        if jlog: jlog.error(f'App open failed: {app_name}', e)
                        else: print(f"[WebSocket] App open error: {e}")
                        return f"Had trouble opening {app_name}, {title}."
            
            # --- TOGGLE FEATURES (gesture, face, emotion) ---
            cmd_lower = command.lower()
            if any(w in cmd_lower for w in ['enable', 'disable', 'turn on', 'turn off', 'start', 'stop']):
                enabling = any(w in cmd_lower for w in ['enable', 'turn on', 'start'])
                
                if 'gesture' in cmd_lower:
                    if jlog: jlog.route('feature_toggle', 'gesture')
                    self.gesture_enabled = enabling
                    if enabling and self.gesture_controller:
                        self.gesture_controller.enable_tracking()
                    elif self.gesture_controller:
                        self.gesture_controller.disable_tracking()
                    return f"Gesture control {'enabled' if enabling else 'disabled'}, {title}."
                
                elif 'face' in cmd_lower:
                    if jlog: jlog.route('feature_toggle', 'face')
                    self.face_enabled = enabling
                    if enabling and self.face_recognition:
                        self.face_recognition.start_monitoring()
                    elif self.face_recognition:
                        self.face_recognition.stop_monitoring()
                    return f"Face recognition {'enabled' if enabling else 'disabled'}, {title}."
                
                elif 'emotion' in cmd_lower or 'mood' in cmd_lower:
                    if jlog: jlog.route('feature_toggle', 'emotion')
                    self.emotion_enabled = enabling
                    return f"Emotion detection {'enabled' if enabling else 'disabled'}, {title}."
            
            # --- MUSIC CONTROL ---
            if intent_name in ('play_music', 'pause_music', 'next_track', 'previous_track'):
                if jlog: jlog.route('music', intent_name)
                try:
                    from core.music_handler import MusicHandler
                    mh = MusicHandler()
                    result = mh.handle_command(command)
                    if result:
                        return result
                except Exception as e:
                    print(f"[WebSocket] MusicHandler error: {e}")
                # Fallback: use media keys via ctypes
                try:
                    from core.music_handler import MediaKeyController
                    mk = MediaKeyController()
                    if intent_name == 'play_music':
                        mk.play_pause()
                        return f"Playing music, {title}."
                    elif intent_name == 'pause_music':
                        mk.play_pause()
                        return f"Music paused, {title}."
                    elif intent_name == 'next_track':
                        mk.next_track()
                        return f"Next track, {title}."
                    elif intent_name == 'previous_track':
                        mk.previous_track()
                        return f"Previous track, {title}."
                except Exception as e:
                    print(f"[WebSocket] MediaKey error: {e}")
            
            # --- OCR / READ SCREEN ---
            if intent_name == 'ocr':
                if self.ocr_handler and hasattr(self.ocr_handler, 'read_screen'):
                    try:
                        text = self.ocr_handler.read_screen()
                        if text:
                            short_text = text[:200] + '...' if len(text) > 200 else text
                            return f"I found this text on screen: {short_text}"
                        return f"No readable text found on screen, {title}."
                    except Exception as e:
                        return f"Screen reading error: {e}"
                return f"OCR not available, {title}. Install pytesseract."
            
            # --- READ CLIPBOARD ---
            if intent_name == 'read_clipboard':
                try:
                    import subprocess
                    text = subprocess.run(['powershell', '-command', 'Get-Clipboard'],
                                         capture_output=True, text=True, timeout=5).stdout.strip()
                    if text:
                        short_text = text[:300] + '...' if len(text) > 300 else text
                        return f"Clipboard contains: {short_text}"
                    return f"Clipboard is empty, {title}."
                except Exception as e:
                    return f"Clipboard error: {e}"
            
            # ══════════════════════════════════════════════════════════════
            # HANDLER_MAP DISPATCH: Direct handler lookup for all other intents
            # Time, date, greeting, joke, weather, story, etc.
            # ══════════════════════════════════════════════════════════════
            if ROUTER_AVAILABLE and intent_name in HANDLER_MAP:
                try:
                    handler = HANDLER_MAP[intent_name]
                    
                    # Build handler context with all available subsystems
                    handler_context = {
                        'title': title,
                        'system_stats': self.get_system_stats() if hasattr(self, 'get_system_stats') else {},
                        'alarm_system': self.alarm_system,
                        'screenshot_handler': self.screenshot_handler,
                        'knowledge': self.knowledge,
                        'state_manager': self.state_manager,
                        'weather_handler': self.weather_handler,
                        'news_handler': self.news_handler,
                        'entertainment': self.entertainment,
                        'system_control': self.system_control,
                        'reminder_manager': getattr(self, 'reminder_manager', None),
                        'whatsapp_handler': getattr(self, 'whatsapp_handler', None),
                        'perception': self.hud_perception,
                        'face_auth': getattr(self, 'face_recognition', None),
                        'ai_search': self.knowledge,  # KnowledgeLayer doubles as AI search
                    }
                    
                    if jlog: jlog.route('HANDLER_MAP', intent_name)
                    else: print(f"[WebSocket] HANDLER_MAP dispatch: {intent_name}")
                    
                    result = handler(command, entities, handler_context)
                    
                    if result and result.success and result.response:
                        # Handle side-effects from handler data
                        if result.data and result.data.get('type') == 'switch_voice':
                            voice = result.data.get('voice', 'jarvis')
                            if voice == 'friday':
                                self.hud_perception.switch_to_friday()
                            else:
                                self.hud_perception.switch_to_jarvis()
                        return result.response
                except Exception as e:
                    if jlog: jlog.error(f'Handler dispatch failed: {intent_name}', e)
                    else: print(f"[WebSocket] Handler error for {intent_name}: {e}")
            
            # No handler found - fall through
            return None
            
        except Exception as e:
            if jlog: jlog.error('Router pipeline failed', e)
            else:
                print(f"[WebSocket] Router error: {e}")
                import traceback
                traceback.print_exc()
            return None
    
    def _stop_speaking(self):
        """Stop JARVIS from speaking immediately — both server-side and browser TTS"""
        # Stop through HUD perception
        if self.perception and hasattr(self.perception, 'stop_speaking'):
            self.perception.stop_speaking()
        
        # Reset mic mute flags
        if self.perception:
            self.perception.is_speaking = False
            self.perception.mic_muted = False
        
        # Stop through JARVIS backend perception
        if self.jarvis and hasattr(self.jarvis, 'perception') and hasattr(self.jarvis.perception, 'stop_speaking'):
            self.jarvis.perception.stop_speaking()
        
        # Stop entertainment/storyteller if running
        if self.entertainment and hasattr(self.entertainment, 'storyteller') and self.entertainment.storyteller:
            if hasattr(self.entertainment.storyteller, 'stop'):
                self.entertainment.storyteller.stop()
        
        # ━━━ BROADCAST TO ALL HUD CLIENTS: cancel browser speechSynthesis ━━━
        if self.clients:
            stop_msg = json.dumps({'type': 'stop_speaking'})
            for client in self.clients:
                try:
                    asyncio.ensure_future(client.send(stop_msg))
                except Exception:
                    pass
        
        self.state_manager.force_state("idle")
        print("[WebSocket] Speech interrupted (server + browser)")
    
    async def _fallback_process(self, command: str, websocket) -> str:
        """Fallback command processing when JARVIS not available"""
        cmd = command.lower().strip()
        name = self.hud_perception.assistant_name
        title = self.hud_perception.user_title
        
        # Voice switching (needs WebSocket - handle before router)
        if 'switch to friday' in cmd or 'activate friday' in cmd:
            self.hud_perception.switch_to_friday()
            await self._send_to(websocket, json.dumps({
                'type': 'assistant_info',
                'name': 'FRIDAY',
                'is_friday': True
            }))
            return "FRIDAY online. Hello, boss. How can I help you today?"
        
        if 'switch to jarvis' in cmd or 'activate jarvis' in cmd:
            self.hud_perception.switch_to_jarvis()
            await self._send_to(websocket, json.dumps({
                'type': 'assistant_info',
                'name': 'JARVIS',
                'is_friday': False
            }))
            return f"JARVIS back online, {title}. At your service."
        
        # ══════════════════════════════════════════════════════════════════
        # LEGACY HANDLERS: for commands not yet migrated to IntentRouter
        # IntentRouter is now checked FIRST in process_command()
        # ══════════════════════════════════════════════════════════════════
        
        # Greetings - use sir once
        if any(word in cmd for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'good night']):
            hour = datetime.now().hour
            greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening" if hour < 21 else "Hey there"
            return f"{greeting}, {title}. How may I help?"
        
        # Time - short response, sir once at end
        # Exclude 'bedtime story' — 'time' in 'bedtime' is a false match
        if 'time' in cmd and not any(w in cmd for w in ['story', 'bedtime', 'once upon', 'tale']):
            now = datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')}, {title}."
        
        # Date - short response, sir once
        if 'date' in cmd or ('what' in cmd and 'day' in cmd):
            now = datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}, {title}."
        
        # System status - long response, sir once at the END only
        if 'system status' in cmd or 'system report' in cmd:
            stats = self.get_system_stats()
            charge = " and charging" if stats.get('charging') else ""
            return f"All systems operational. CPU at {stats['cpu']}%, " \
                   f"memory at {stats['memory']}%, disk at {stats['disk']}%, " \
                   f"battery at {stats['battery']}%{charge}, {title}."
        
        # How are you - sir once at end
        if 'how are you' in cmd:
            stats = self.get_system_stats()
            if stats['cpu'] < 50:
                return f"Operating at peak efficiency, {title}. All systems nominal."
            else:
                return f"Functioning well, {title}. System load is moderate but manageable."
        
        # Weather
        if 'weather' in cmd:
            weather = self.get_weather_data()
            return f"Current conditions in {weather['location']}: {weather['temp']}°C, " \
                   f"{weather['condition']}. Humidity at {weather['humidity']}%, " \
                   f"wind {weather['wind']} kilometers per hour."
        
        # General news
        if 'news' in cmd or 'headline' in cmd:
            news = self.get_news_data()
            items = news['items'][:3]
            items_text = ". ".join(items)
            return f"Here are the top headlines, {title}: {items_text}"
        
        # Identity
        if 'who are you' in cmd or 'your name' in cmd:
            if self.hud_perception.is_friday:
                return "I'm FRIDAY - Female Replacement Intelligent Digital Assistant Youth. " \
                       "Your AI assistant, boss."
            return f"I am {name} - Just A Rather Very Intelligent System. " \
                   f"Your personal AI assistant, created by Raghava."
        
        # Creator
        if 'who made you' in cmd or 'who created you' in cmd or 'creator' in cmd:
            return f"I was created by Raghava, {title}. A brilliant engineer who envisioned " \
                   "the ultimate digital assistant."
        
        # Capabilities
        if 'what can you do' in cmd or 'capabilities' in cmd or cmd == 'help':
            return f"I can assist with many things, {title}: System monitoring, " \
                   "weather updates, news by category (try 'economics news' or 'politics news'), " \
                   "reminders, smart notes, alarms, opening applications, web searches, " \
                   "volume control, and intelligent conversation. Voice to voice mode is active. " \
                   "You can also interact with the globe to get location-specific news."
        
        # STORY - Check BEFORE jokes (so "horror story" doesn't match "joke")
        if 'story' in cmd and 'joke' not in cmd:
            genre = "adventure"
            if 'horror' in cmd or 'scary' in cmd or 'creepy' in cmd:
                genre = "horror"
            elif 'funny' in cmd or 'comedy' in cmd:
                genre = "comedy"
            elif 'romance' in cmd or 'love' in cmd:
                genre = "romance"
            elif 'bedtime' in cmd or 'sleep' in cmd:
                genre = "bedtime"
            elif 'mystery' in cmd or 'detective' in cmd:
                genre = "mystery"
            elif 'sci-fi' in cmd or 'science fiction' in cmd or 'space' in cmd:
                genre = "sci-fi"
            
            # Play ambient sound for horror stories
            if genre == 'horror' and self.entertainment and hasattr(self.entertainment, 'sound_library'):
                try:
                    self.entertainment.sound_library.play('suspense')
                except:
                    pass
            
            if self.knowledge and hasattr(self.knowledge, 'answer_question'):
                try:
                    prompts = {
                        'horror': """Tell a short, genuinely creepy horror story (3-4 paragraphs).
                            Build suspense slowly, use vivid atmospheric descriptions.
                            Include a twist ending. Make it unsettling but not too graphic.
                            Just tell the story, no intro.""",
                        'comedy': """Tell a short funny story (2-3 paragraphs).
                            Include humor, witty dialogue, and a hilarious punchline.
                            Make it genuinely laugh-out-loud funny.
                            Just tell the story, no intro.""",
                        'romance': """Tell a short, heartwarming romance story (2-3 paragraphs).
                            Make it sweet and touching with vivid emotions.
                            Just tell the story, no intro.""",
                        'mystery': """Tell a short mystery story (3-4 paragraphs).
                            Include clues, suspense, and a satisfying reveal.
                            Just tell the story, no intro.""",
                        'sci-fi': """Tell a short science fiction story (2-3 paragraphs).
                            Include futuristic elements, interesting technology.
                            Just tell the story, no intro.""",
                        'bedtime': """Tell a short, gentle bedtime story (2 paragraphs).
                            Make it calming and peaceful with a happy ending.
                            Just tell the story, no intro.""",
                        'adventure': """Tell a short adventure story (2-3 paragraphs).
                            Include action, excitement, and a triumphant ending.
                            Just tell the story, no intro."""
                    }
                    prompt = prompts.get(genre, prompts['adventure'])
                    story = self.knowledge.answer_question(prompt)
                    if story and len(story) > 50:
                        return story
                except Exception as e:
                    print(f"[WebSocket] Story generation error: {e}")
            
            # Fallback stories by genre
            fallback_stories = {
                'horror': "The old house stood silent in the moonlight. Sarah pushed open the door, her flashlight cutting through the darkness. 'Hello?' she called. No answer. But as she turned to leave, she felt cold breath on her neck. And in the mirror across the room, she saw that nothing was standing behind her...",
                'comedy': "Dave tried to impress his date by ordering in French at the Italian restaurant. The waiter, being a good sport, brought him exactly what he ordered: a taxi, three umbrellas, and his mother's phone number. His date still talks about it. They've been married 20 years.",
                'romance': "They met at the coffee shop every morning for a year, never speaking, just exchanging smiles. One day, she found a note on her usual table: 'I've memorized your coffee order. Can I finally learn your name?' She looked up. He was already smiling.",
                'adventure': "The map led to a cave no explorer had entered in centuries. Inside, golden artifacts gleamed in the torchlight. The adventure had only just begun..."
            }
            return fallback_stories.get(genre, fallback_stories['adventure'])
        
        # Jokes - use Gemini AI for unique jokes
        if 'joke' in cmd:
            if self.knowledge and hasattr(self.knowledge, 'answer_question'):
                try:
                    prompt = """Tell me ONE funny joke. Requirements:
                    - Be creative and original
                    - Can be tech humor, wordplay, or observational comedy
                    - Keep it short (1-3 sentences max)
                    - Just the joke, no intro like "here's a joke"
                    - Make it actually funny, not cringe"""
                    joke = self.knowledge.answer_question(prompt)
                    if joke and len(joke) > 10:
                        return joke
                except Exception as e:
                    print(f"[WebSocket] Joke generation error: {e}")
            # Fallback
            import random
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "A SQL query walks into a bar and asks: Can I join you?",
                "Why did the developer go broke? Because he used up all his cache."
            ]
            return random.choice(jokes)
        
        # Thank you - no 'sir' every time
        if 'thank' in cmd:
            responses = [
                "You're welcome!",
                "Anytime.",
                "Happy to help.",
                "My pleasure."
            ]
            import random
            return random.choice(responses)
        
        # PLAY MUSIC / SPOTIFY / YOUTUBE
        if 'play music' in cmd or 'play song' in cmd or 'spotify' in cmd or 'youtube' in cmd:
            import re
            
            # If YouTube is specifically mentioned
            if 'youtube' in cmd:
                # Extract query: play [query] on youtube
                query_match = re.search(r'(?:play|find|search)\s+(.+?)(?:\s+on|\s+in)?\s*youtube', cmd, re.I)
                # Or: youtube play [query]
                if not query_match:
                    query_match = re.search(r'youtube\s+(?:to\s+)?(?:play|find|search)\s+(.+)', cmd, re.I)
                
                query = query_match.group(1).strip() if query_match else cmd.replace('youtube', '').replace('play', '').strip()
                
                if not query:
                    import webbrowser
                    webbrowser.open("https://youtube.com")
                    return f"Opening YouTube{maybe_title(title)}."
                
                if hasattr(self, 'youtube') and hasattr(self.youtube, 'search_and_play'):
                    self.youtube.search_and_play(query)
                else:
                    from core.youtube_downloader import YouTubeDownloader
                    yt = YouTubeDownloader()
                    yt.search_and_play(query)
                return f"Playing your request on YouTube{maybe_title(title)}."
            
            # Default to Spotify
            import os
            try:
                os.startfile('spotify:')
                return f"Opening Spotify for you{maybe_title(title)}."
            except:
                return f"Couldn't open Spotify. Make sure it's installed{maybe_title(title)}."
        
        # Volume - actually control hardware
        if 'volume' in cmd:
            if 'up' in cmd or 'increase' in cmd:
                if self.system_control:
                    self.system_control.volume_up()
                return f"Volume increased{maybe_title(title)}."
            elif 'down' in cmd or 'decrease' in cmd:
                if self.system_control:
                    self.system_control.volume_down()
                return f"Volume decreased{maybe_title(title)}."
            elif 'mute' in cmd:
                if self.system_control:
                    self.system_control.mute_volume()
                return f"Audio muted{maybe_title(title)}."
        
        # SCREEN CONTROL - click, scroll, type, move mouse
        if self.screen_control:
            # Click commands
            if 'click' in cmd:
                result = self.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Clicked{maybe_title(title)}."
            
            # Scroll commands
            if 'scroll' in cmd:
                result = self.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Scrolling{maybe_title(title)}."
            
            # Type text commands
            if 'type ' in cmd or 'write ' in cmd:
                result = self.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Typing text{maybe_title(title)}."
            
            # Move mouse
            if 'move mouse' in cmd or 'move cursor' in cmd:
                result = self.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Moving cursor{maybe_title(title)}."
            
            # Press key commands
            if 'press ' in cmd and any(k in cmd for k in ['enter', 'escape', 'tab', 'delete', 'backspace', 'space']):
                result = self.screen_control.handle(cmd)
                return result if isinstance(result, str) else f"Key pressed{maybe_title(title)}."
        
        # WHATSAPP - send message, open whatsapp, read messages
        if self.whatsapp_handler:
            # Send WhatsApp message
            if 'whatsapp' in cmd or ('send' in cmd and 'message' in cmd):
                import re
                # Parse: send message to [contact] saying [message]
                # or: whatsapp [contact] [message]
                match = re.search(r'(?:send\s+(?:a\s+)?message\s+to|whatsapp)\s+([a-zA-Z\s]+?)(?:\s+saying|\s+that|\s+message)?\s*[:\-]?\s*(.+)?', cmd, re.I)
                if match:
                    contact = match.group(1).strip()
                    message = match.group(2).strip() if match.group(2) else None
                    result = self.whatsapp_handler.send_message(contact, message)
                    return result if isinstance(result, str) else f"Sending WhatsApp message to {contact}, {title}."
                elif 'open whatsapp' in cmd:
                    result = self.whatsapp_handler.open_whatsapp()
                    return result if isinstance(result, str) else f"Opening WhatsApp, {title}."
                elif 'read' in cmd and ('message' in cmd or 'whatsapp' in cmd):
                    result = self.whatsapp_handler.read_messages()
                    return result if isinstance(result, str) else f"Opening WhatsApp to view messages, {title}."
        
        # CALENDAR - events, schedule, meetings
        if self.calendar:
            # Today's events
            if 'calendar' in cmd or 'event' in cmd or 'schedule' in cmd or 'meeting' in cmd:
                if "today" in cmd or "what's on" in cmd:
                    events = self.calendar.get_today_events()
                    if events:
                        event_list = ", ".join([f"{e.summary} at {e.start.strftime('%I:%M %p')}" for e in events[:5]])
                        return f"Today's events, {title}: {event_list}."
                    return f"No events scheduled for today, {title}."
                elif "upcoming" in cmd or "next" in cmd:
                    events = self.calendar.get_upcoming_events(5)
                    if events:
                        event_list = ", ".join([f"{e.summary}" for e in events[:5]])
                        return f"Upcoming events, {title}: {event_list}."
                    return f"No upcoming events, {title}."
                elif "create" in cmd or "add" in cmd or "schedule" in cmd:
                    import re
                    # Quick add: schedule meeting with John tomorrow at 3pm
                    match = re.search(r'(?:create|add|schedule)\s+(?:a\s+)?(?:event|meeting|appointment)?\s*(.+)', cmd, re.I)
                    if match:
                        event_text = match.group(1).strip()
                        result = self.calendar.quick_add(event_text)
                        if result:
                            return f"Event created, {title}."
                        return f"Couldn't create event. Please try with more details, {title}."
                return f"Opening calendar, {title}. What would you like to do?"
        
        # EMAIL - read emails, summarize emails
        if self.email_handler_obj:
            if 'email' in cmd or 'mail' in cmd or 'gmail' in cmd:
                if 'summarize' in cmd or 'summary' in cmd:
                    self.email_handler_obj.summarize_emails()
                    return f"Summarizing your emails, {title}."
                elif 'unread' in cmd or 'read' in cmd or 'check' in cmd:
                    self.email_handler_obj.get_unread_emails()
                    return f"Checking your emails, {title}."
                else:
                    self.email_handler_obj.get_unread_emails()
                    return f"Checking your inbox, {title}."
        
        # YOUTUBE - download video, download audio
        if self.youtube_downloader:
            if 'youtube' in cmd or 'download video' in cmd or 'download audio' in cmd:
                # Extract URL from command
                url = self.youtube_downloader.extract_url_from_command(cmd)
                
                if url:
                    if 'audio' in cmd or 'mp3' in cmd or 'music' in cmd:
                        result = self.youtube_downloader.download_audio(url)
                        return f"Downloading audio from YouTube, {title}."
                    else:
                        result = self.youtube_downloader.download_video(url)
                        return f"Downloading video from YouTube, {title}."
                elif 'downloads' in cmd or 'folder' in cmd:
                    self.youtube_downloader.open_downloads_folder()
                    return f"Opening YouTube downloads folder, {title}."
                else:
                    return f"Please provide a YouTube URL for me to download, {title}."
        
        # HABITS - create, list, complete habits
        if self.habit_tracker:
            if 'habit' in cmd:
                if 'create' in cmd or 'add' in cmd or 'new' in cmd:
                    import re
                    # Parse: create habit [description] every [interval]
                    match = re.search(r'(?:create|add|new)\s+habit\s+(.+?)(?:\s+every\s+|\s+daily|\s+hourly|\s+morning|\s+evening|$)', cmd, re.I)
                    if match:
                        desc = match.group(1).strip()
                        interval = cmd  # Pass full command for interval parsing
                        self.habit_tracker.create_habit(desc, interval)
                        return f"Habit created, {title}."
                elif 'list' in cmd or 'show' in cmd or 'my habits' in cmd:
                    self.habit_tracker.list_habits()
                    return f"Listing your habits, {title}."
                elif 'check' in cmd or 'remind' in cmd:
                    reminders = self.habit_tracker.check_reminders()
                    if reminders:
                        return f"You have {len(reminders)} habit reminders, {title}."
                    return f"No habit reminders due, {title}."
        
        # TASKS - add, list, complete tasks
        if self.task_manager_obj:
            if 'task' in cmd or 'to do' in cmd or 'todo' in cmd:
                if 'add' in cmd or 'create' in cmd or 'new' in cmd:
                    import re
                    match = re.search(r'(?:add|create|new)\s+(?:a\s+)?task\s+(.+)', cmd, re.I)
                    if match:
                        desc = match.group(1).strip()
                        self.task_manager_obj.add_task(desc)
                        return f"Task added, {title}."
                elif 'list' in cmd or 'show' in cmd or 'my tasks' in cmd:
                    self.task_manager_obj.list_tasks()
                    return f"Listing your tasks, {title}."
                elif 'complete' in cmd or 'done' in cmd:
                    import re
                    match = re.search(r'(?:complete|done)\s+task\s+(\d+)', cmd, re.I)
                    if match:
                        index = int(match.group(1))
                        self.task_manager_obj.complete_task_by_index(index)
                        return f"Task marked complete, {title}."
        
        # WELLNESS - check wellness, session duration
        if self.wellness_monitor:
            if 'wellness' in cmd or 'health' in cmd or 'break' in cmd:
                if 'summary' in cmd or 'status' in cmd:
                    summary = self.wellness_monitor.get_wellness_summary()
                    return summary
                elif 'check' in cmd:
                    reminder = self.wellness_monitor.check_wellness()
                    if reminder:
                        return reminder
                    return f"You're doing well, {title}."
                elif 'reset' in cmd or 'took a break' in cmd:
                    self.wellness_monitor.reset_session()
                    return f"Session reset. Good on you for taking a break, {title}."
        
        # CHAT HISTORY - search conversations, recent chat
        if self.chat_history:
            if 'history' in cmd or 'conversation' in cmd or 'what did' in cmd:
                if 'search' in cmd:
                    import re
                    match = re.search(r'search\s+(?:for\s+)?(.+)', cmd, re.I)
                    if match:
                        query = match.group(1).strip()
                        results = self.chat_history.search(query)
                        if results:
                            return f"Found {len(results)} conversations matching '{query}', {title}."
                        return f"No conversations found matching '{query}', {title}."
                elif 'recent' in cmd or 'last' in cmd:
                    messages = self.chat_history.get_recent(5)
                    if messages:
                        return f"Here are your last {len(messages)} messages, {title}."
                    return f"No chat history yet, {title}."
                elif 'clear' in cmd or 'delete' in cmd:
                    self.chat_history.clear_history()
                    return f"Chat history cleared, {title}."

        if ' and search' in cmd and 'open ' in cmd:
            import re
            import subprocess
            # Parse: open [browser] and search for [query]
            match = re.search(r'open\s+(\w+)\s+and\s+(?:search|look)\s+(?:for\s+)?(.+)', cmd)
            if match:
                browser = match.group(1).lower()
                query = match.group(2).strip()
                
                # Browser command mappings
                browser_cmds = {
                    'edge': 'msedge',
                    'microsoft': 'msedge',
                    'chrome': 'chrome',
                    'brave': 'brave',
                    'firefox': 'firefox',
                }
                
                browser_cmd = browser_cmds.get(browser, 'msedge')
                encoded_query = query.replace(' ', '+')
                
                try:
                    # Open specific browser with search URL
                    search_url = f'https://www.google.com/search?q={encoded_query}'
                    if browser_cmd == 'msedge':
                        subprocess.Popen(['msedge', search_url], shell=True)
                    elif browser_cmd == 'brave':
                        subprocess.Popen(['brave', search_url], shell=True)
                    elif browser_cmd == 'chrome':
                        subprocess.Popen(['chrome', search_url], shell=True)
                    elif browser_cmd == 'firefox':
                        subprocess.Popen(['firefox', search_url], shell=True)
                    else:
                        import webbrowser
                        webbrowser.open(search_url)
                    return f"Opening {browser.capitalize()} and searching for '{query}', {title}."
                except Exception as e:
                    print(f"[WebSocket] Browser search error: {e}")
                    import webbrowser
                    webbrowser.open(f'https://www.google.com/search?q={encoded_query}')
                    return f"Searching for '{query}', {title}."
        # APP SWITCHING — switch to, switch with, go to, alt-tab
        switch_prefixes = ('switch to ', 'switch with ', 'switch tab to ', 'go to ', 'switch tab ')
        if any(cmd.startswith(p) for p in switch_prefixes):
            target = cmd
            for p in switch_prefixes:
                target = target.replace(p, '', 1)
            target = target.strip()
            # Skip assistant personality switches (handled elsewhere)
            if target in ('friday', 'jarvis'):
                pass  # Handled later at line ~2440
            else:
                try:
                    import pyautogui
                    import subprocess
                    # Try to find the window by title and activate it
                    result = subprocess.run(
                        ['powershell', '-command',
                         f'(Get-Process | Where-Object {{$_.MainWindowTitle -match "{target}"}} | Select-Object -First 1).MainWindowTitle'],
                        capture_output=True, text=True, timeout=3
                    )
                    window_title = result.stdout.strip()
                    if window_title:
                        # Use PowerShell to bring window to front
                        subprocess.run(
                            ['powershell', '-command', f'''
                            $window = Get-Process | Where-Object {{$_.MainWindowTitle -match "{target}"}} | Select-Object -First 1
                            if ($window) {{
                                $hwnd = $window.MainWindowHandle
                                Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class Win32 {{ [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow); }}'
                                [Win32]::ShowWindow($hwnd, 9)
                                [Win32]::SetForegroundWindow($hwnd)
                            }}
                            '''],
                            capture_output=True, timeout=3
                        )
                        self.state_manager.active_app = target.lower()
                        self.state_manager._active_app_time = time.time()
                        return f"Switching to {target}, {title}."
                    else:
                        return f"I can't find {target} running. Would you like me to open it?"
                except Exception as e:
                    print(f"[WebSocket] App switch error: {e}")
                    return f"Couldn't switch to {target}, {title}."
        
        if cmd in ('go back', 'alt tab', 'switch window', 'next window', 'previous window'):
            try:
                import pyautogui
                pyautogui.hotkey('alt', 'tab')
                return f"Switched to the previous window, {title}."
            except Exception as e:
                return f"Couldn't switch windows, {title}."
        
        # Open apps - ACTUALLY open them with fuzzy matching
        if cmd.startswith('open '):
            app = cmd.replace('open ', '').strip()
            import subprocess
            app_lower = app.lower()
            
            # Fuzzy matching for common typos
            typo_corrections = {
                'chatpgt': 'chatgpt',
                'chatgtp': 'chatgpt',
                'cahtgpt': 'chatgpt',
                'gpt': 'chatgpt',
                'whatspp': 'whatsapp',
                'whatapp': 'whatsapp',
                'watsapp': 'whatsapp',
                'spotfy': 'spotify',
                'spotofy': 'spotify',
                'perplexty': 'perplexity',
                'perplxity': 'perplexity',
                'telgram': 'telegram',
                'discod': 'discord',
                'edg': 'edge',
                'brav': 'brave',
            }
            app_lower = typo_corrections.get(app_lower, app_lower)
            
            app_paths = {
                # Browsers
                'edge': 'msedge',
                'microsoft edge': 'msedge',
                'brave': 'brave',
                'chrome': 'chrome',
                'firefox': 'firefox',
                # Messaging
                'whatsapp': 'whatsapp:',
                'telegram': 'telegram:',
                'discord': 'discord:',
                # System
                'notepad': 'notepad',
                'calculator': 'calc',
                'file explorer': 'explorer',
                'explorer': 'explorer',
                'settings': 'ms-settings:',
                'cmd': 'cmd',
                'terminal': 'wt',
                'powershell': 'powershell',
                # Development
                'vscode': 'code',
                'vs code': 'code',
                'visual studio code': 'code',
                # Media
                'spotify': 'spotify:',
                # AI Apps - use app_finder or web fallback
                'perplexity': 'perplexity',
                'chatgpt': 'chatgpt',
            }
            
            try:
                # Try using JARVIS app_finder first (most reliable)
                if self.jarvis and hasattr(self.jarvis, 'app_finder'):
                    try:
                        result = self.jarvis.app_finder.open_app(app_lower)
                        if result:
                            return f"Opening {app}, {title}."
                    except Exception as e:
                        print(f"[WebSocket] app_finder error: {e}")
                
                if app_lower in app_paths:
                    target = app_paths[app_lower]
                    
                    # Handle special cases
                    if app_lower == 'perplexity':
                        # Try Start Menu shortcut first
                        shortcut_path = rf'C:\Users\{os.getenv("USERNAME")}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Perplexity.lnk'
                        if os.path.exists(shortcut_path):
                            os.startfile(shortcut_path)
                        else:
                            # Fallback to web
                            import webbrowser
                            webbrowser.open('https://perplexity.ai')
                        return f"Opening Perplexity, {title}."
                    
                    elif app_lower == 'chatgpt':
                        # Try PWA/App first, then web
                        shortcut_path = rf'C:\Users\{os.getenv("USERNAME")}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\ChatGPT.lnk'
                        if os.path.exists(shortcut_path):
                            os.startfile(shortcut_path)
                        else:
                            import webbrowser
                            webbrowser.open('https://chat.openai.com')
                        return f"Opening ChatGPT, {title}."
                    
                    elif target.startswith('http') or target.endswith(':'):
                        os.startfile(target)
                    else:
                        subprocess.Popen(target, shell=True)
                else:
                    # Try to open by name directly
                    os.startfile(app)
                return f"Opening {app}, {title}."
            except Exception as e:
                print(f"[WebSocket] Open app error: {e}")
                # Web fallback for unknown apps
                import webbrowser
                webbrowser.open(f'https://www.google.com/search?q={app}+download')
                return f"{title}, I couldn't find {app} installed. Let me search for it online."
        
        # Search
        if 'search' in cmd:
            query = cmd.replace('search for', '').replace('search', '').strip()
            return f"Searching for '{query}', {title}."
        
        # Features status
        if 'features' in cmd or 'status' in cmd:
            status = self.get_feature_status()
            features = []
            if status['jarvis_full']:
                features.append("full JARVIS integration")
            if status['gesture_available']:
                features.append("gesture control")
            if status['face_available']:
                features.append("face recognition")
            if status['emotion_available']:
                features.append("emotion detection")
            
            if features:
                return f"Available features, {title}: {', '.join(features)}. " \
                       "All can be enabled from the interface."
            return f"Core features active, {title}. Advanced modules loading."
        
        # ══════════════════════════════════════════════════════════════════
        # NEW FEATURE COMMANDS
        # ══════════════════════════════════════════════════════════════════
        
        # SCREENSHOT
        if 'screenshot' in cmd or 'screen shot' in cmd or 'capture screen' in cmd:
            if self.screenshot_handler:
                path = self.screenshot_handler.take_fullscreen()
                if path:
                    await self._send_to(websocket, json.dumps({
                        'type': 'screenshot_taken',
                        'path': str(path),
                        'filename': path.name
                    }))
                    return f"Screenshot saved to {path.name}, {title}."
                return f"Failed to take screenshot, {title}."
            return f"Screenshot feature not available, {title}."
        
        # OCR / READ SCREEN
        if 'read screen' in cmd or 'read text' in cmd or 'extract text' in cmd or 'ocr' in cmd:
            if self.ocr_handler:
                text = self.ocr_handler.read_screen()
                if text:
                    # Limit for speech
                    short_text = text[:200] + "..." if len(text) > 200 else text
                    await self._send_to(websocket, json.dumps({
                        'type': 'ocr_result',
                        'text': text
                    }))
                    return f"I found this text: {short_text}"
                return f"No readable text found on screen, {title}."
            return f"OCR feature not available. Install pytesseract and Tesseract-OCR, {title}."
        
        # READ CLIPBOARD
        if 'read clipboard' in cmd:
            if self.ocr_handler:
                text = self.ocr_handler.read_clipboard_image()
                if text:
                    return f"Clipboard text: {text[:200]}"
                return f"No text in clipboard image, {title}."
            return f"OCR not available, {title}."
        
        # DICTIONARY
        if 'define ' in cmd or 'meaning of ' in cmd or 'definition of ' in cmd:
            word = cmd.replace('define ', '').replace('meaning of ', '').replace('definition of ', '').strip()
            if self.dictionary_handler and word:
                word_lower = word.lower()
                # Get definition directly from dictionary
                if word_lower in self.dictionary_handler.dictionary:
                    definition = self.dictionary_handler.dictionary[word_lower]
                    return f"{word.capitalize()}: {definition}"
                # Try online lookup
                online_def = self.dictionary_handler._lookup_online(word_lower)
                if online_def:
                    return f"{word.capitalize()}: {online_def}"
                return f"I couldn't find a definition for '{word}', {title}."
            return f"Dictionary not available, {title}."
        
        # SYNONYMS
        if 'synonym' in cmd:
            word = cmd.replace('synonym for ', '').replace('synonym of ', '').replace('synonyms of ', '').replace('synonym', '').strip()
            if self.dictionary_handler and word:
                import requests
                try:
                    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            meanings = data[0].get("meanings", [])
                            all_synonyms = []
                            for meaning in meanings:
                                synonyms = meaning.get("synonyms", [])
                                all_synonyms.extend(synonyms[:3])
                            if all_synonyms:
                                synonym_list = ", ".join(all_synonyms[:5])
                                return f"Synonyms for {word}: {synonym_list}"
                except:
                    pass
                return f"No synonyms found for '{word}', {title}."
            return f"Dictionary not available, {title}."
        
        # FACE REGISTRATION
        if 'register my face' in cmd or 'register face' in cmd or 'register owner' in cmd:
            if self.face_recognition:
                result = self.face_recognition.register_owner()
                if result:
                    self.current_user = self.face_recognition.current_user
                    await self._send_to(websocket, json.dumps({
                        'type': 'face_registered',
                        'success': True,
                        'user': 'Raghava'
                    }))
                    return f"Face registered successfully, {title}. You are now the verified owner."
                return f"Face registration failed, {title}. Please try again with better lighting."
            return f"Face recognition is not available, {title}. Install face_recognition and dlib."
        
        # VERIFY FACE
        if 'verify me' in cmd or 'authenticate' in cmd or 'who am i' in cmd:
            if self.face_recognition:
                result = self.face_recognition.authenticate()
                if result:
                    user = self.face_recognition.current_user
                    return f"Welcome, {user.name}. Access level: {user.user_type.value}."
                return f"Face not recognized, {title}."
            return f"Face recognition not available, {title}."
        
        # GESTURE CONTROL
        if 'enable gesture' in cmd or 'start gesture' in cmd or 'gesture on' in cmd:
            if self.gesture_controller:
                try:
                    self.gesture_controller.enable_tracking()
                    self.gesture_enabled = True
                    await self._send_to(websocket, json.dumps(self.get_feature_status()))
                    return f"Gesture control enabled, {title}. Use hand gestures to control."
                except Exception as e:
                    return f"Failed to start gesture control: {e}"
            return f"Gesture control not available. Install mediapipe, {title}."
        
        if 'disable gesture' in cmd or 'stop gesture' in cmd or 'gesture off' in cmd:
            if self.gesture_controller:
                self.gesture_controller.disable_tracking()
                self.gesture_enabled = False
                return f"Gesture control disabled, {title}."
            return f"Gesture control not active, {title}."
        
        # EMOTION DETECTION
        if 'enable emotion' in cmd or 'mood detection' in cmd:
            self.emotion_enabled = True
            await self._send_to(websocket, json.dumps(self.get_feature_status()))
            return f"Emotion detection enabled, {title}. I'll adapt my responses to your mood."
        
        if 'disable emotion' in cmd:
            self.emotion_enabled = False
            return f"Emotion detection disabled, {title}."
        
        # STORY handler moved earlier in file (before jokes) - see line ~1368\n        # This comment prevents duplicate handling
        
        # ENTERTAINMENT - POEM
        if 'recite a poem' in cmd or 'poem' in cmd:
            if self.entertainment:
                result = self.entertainment.recite_poem()
                if isinstance(result, str) and result:
                    return result
            if self.knowledge and hasattr(self.knowledge, 'answer_question'):
                try:
                    prompt = "Write a short 4-6 line poem. Make it thoughtful and meaningful. Just the poem, no intro."
                    poem = self.knowledge.answer_question(prompt)
                    if poem and len(poem) > 20:
                        return poem
                except Exception as e:
                    print(f"[WebSocket] Poem generation error: {e}")
            return f"Roses are red, violets are blue, I'm an AI here to help you."
        
        # ENTERTAINMENT - RIDDLE
        if 'riddle' in cmd:
            if self.entertainment:
                result = self.entertainment.tell_riddle()
                return result if isinstance(result, str) and result else f"Here's a riddle, {title}: What has keys but no locks? A keyboard!"
            return f"Here's a riddle, {title}: What has keys but no locks, space but no room? A keyboard!"
        
        # SMART NOTES
        if 'create note' in cmd or 'new note' in cmd or 'add note' in cmd:
            content = cmd.replace('create note', '').replace('new note', '').replace('add note', '').strip()
            if self.smart_notes and content:
                result = self.smart_notes.add_note(content=content)
                return result if isinstance(result, str) else f"Note created, {title}."
            return f"Please specify what to note, {title}. Say 'create note about [topic]'."
        
        if 'list notes' in cmd or 'show notes' in cmd or 'my notes' in cmd:
            if self.smart_notes:
                notes = self.smart_notes.read_notes()
                return notes if notes else f"You have no notes yet, {title}."
            return f"Notes feature not available, {title}."
        
        # ALARMS
        if 'set alarm' in cmd:
            # Extract time from command
            import re
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', cmd)
            if self.alarm_system and time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                period = time_match.group(3)
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                self.alarm_system.set_alarm(hour, minute)
                return f"Alarm set for {hour:02d}:{minute:02d}, {title}."
            return f"Please specify a time. Say 'set alarm for 7:30 am', {title}."
        
        if 'list alarm' in cmd or 'show alarm' in cmd or 'my alarm' in cmd:
            if self.alarm_system:
                alarms = self.alarm_system.list_alarms()
                return alarms if alarms else f"No alarms set, {title}."
            return f"Alarm system not available, {title}."
        
        # VOLUME CONTROL (with system control)
        if 'volume' in cmd:
            if self.system_control:
                if 'up' in cmd or 'increase' in cmd:
                    self.system_control.volume_up()
                    return f"Volume increased, {title}."
                elif 'down' in cmd or 'decrease' in cmd:
                    self.system_control.volume_down()
                    return f"Volume decreased, {title}."
                elif 'mute' in cmd:
                    self.system_control.mute_volume()
                    return f"Audio muted, {title}."
                # Check for specific percentage
                import re
                match = re.search(r'(\d+)\s*%?', cmd)
                if match:
                    level = int(match.group(1))
                    self.system_control.set_volume(level)
                    return f"Volume set to {level}%, {title}."
            return f"Adjusting volume, {title}."
        
        # BRIGHTNESS CONTROL
        if 'brightness' in cmd:
            if self.system_control:
                if 'up' in cmd or 'increase' in cmd:
                    self.system_control.brightness_up()
                    return f"Brightness increased, {title}."
                elif 'down' in cmd or 'decrease' in cmd:
                    self.system_control.brightness_down()
                    return f"Brightness decreased, {title}."
                # Check for specific percentage
                import re
                match = re.search(r'(\d+)\s*%?', cmd)
                if match:
                    level = int(match.group(1))
                    self.system_control.set_brightness(level)
                    return f"Brightness set to {level}%, {title}."
            return f"Adjusting brightness, {title}."
        
        # WEB SEARCH
        if 'search' in cmd or 'google' in cmd:
            query = cmd.replace('search for', '').replace('search', '').replace('google', '').strip()
            if query:
                import webbrowser
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Searching for '{query}'."
            return "What would you like me to search for?"
        
        # Default fallback - USE GEMINI AI for intelligent responses
        if self.knowledge and hasattr(self.knowledge, 'answer_question'):
            try:
                response = self.knowledge.answer_question(command)
                _err = ['trouble connecting', 'knowledge base', 'currently offline', 'Set GROQ_API_KEY']
                if response and not any(ep in (response or '') for ep in _err):
                    return response
            except Exception as e:
                print(f"[WebSocket] Knowledge error: {e}")
        
        # Gemini Flash fallback for general conversation
        try:
            import google.genai as _genai
            _api_key = getattr(self, '_gemini_key', None)
            if not _api_key:
                import os
                _api_key = os.getenv('GEMINI_API_KEY', '')
                self._gemini_key = _api_key
            if _api_key:
                _client = _genai.Client(api_key=_api_key)
                _resp = _client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=f"You are JARVIS, a witty AI assistant. Keep replies to 1-2 sentences. Address user as 'sir'. Never break character. User says: {command}"
                )
                if _resp and _resp.text:
                    return _resp.text.strip()
        except Exception as e:
            print(f"[WebSocket] Gemini fallback error: {e}")
        
        # Final fallback
        return "I'm not sure about that. Try asking differently or be more specific."
    
    async def broadcast(self, message, channel=None):
        """Broadcast to clients subscribed to a specific channel.
        
        If channel is None, sends to ALL clients (legacy behavior).
        If channel is specified, only sends to clients subscribed to that channel.
        
        Now routes through per-client queues for backpressure.
        """
        await self.dispatch(channel, message)
    
    # ═══════════════════════════════════════════════════════════════
    # UNIFIED DISPATCH LAYER — all sends go through here
    # ═══════════════════════════════════════════════════════════════
    
    # Priority levels for backpressure (higher = more important)
    _CHANNEL_PRIORITY = {'command': 3, 'live': 2, 'sensors': 1, 'stats': 0}
    
    async def dispatch(self, channel, message):
        """Single authoritative dispatcher — ALL sends go through here.
        
        Enqueues to per-client asyncio.Queue. If queue is full:
          - Drop low-priority messages (stats, sensors)
          - Force-enqueue high-priority (command, live)
        """
        if not self.clients:
            return
        
        # Tag message with channel
        if channel and isinstance(message, dict):
            message['channel'] = channel
        
        msg_str = json.dumps(message) if isinstance(message, dict) else message
        priority = self._CHANNEL_PRIORITY.get(channel, 1)
        
        if channel:
            targets = [
                c for c in list(self.clients)
                if channel in self._client_channels.get(c, {'command', 'stats', 'live', 'sensors'})
            ]
        else:
            targets = list(self.clients)
        
        for client in targets:
            q = self._client_queues.get(client)
            if q is None:
                continue
            try:
                q.put_nowait(msg_str)
            except asyncio.QueueFull:
                if priority >= 2:
                    # High priority: drop oldest to make room
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                    try:
                        q.put_nowait(msg_str)
                    except asyncio.QueueFull:
                        pass
                # else: silently drop low-priority message (stats/sensors spam)
    
    async def _send_to(self, websocket, message):
        """Point-to-point send via queue (for request-response within process_message).
        
        Use this instead of `await self._send_to(websocket, json.dumps(...))`.
        """
        msg_str = json.dumps(message) if isinstance(message, dict) else message
        q = self._client_queues.get(websocket)
        if q is None:
            # Fallback: direct send if queue not set up (shouldn't happen)
            try:
                await websocket.send(msg_str)
            except Exception:
                pass
            return
        try:
            q.put_nowait(msg_str)
        except asyncio.QueueFull:
            # For point-to-point, always force (these are user-facing responses)
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                q.put_nowait(msg_str)
            except asyncio.QueueFull:
                pass
    
    def _dispatch_from_thread(self, channel, message):
        """Thread-safe bridge: background threads call this instead of ws.send().
        
        Schedules dispatch() into the event loop via run_coroutine_threadsafe.
        """
        loop = self._voice_loop
        if not loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.dispatch(channel, message),
                loop
            )
        except Exception:
            pass
    
    async def _client_sender(self, websocket):
        """Per-client drain loop — pops from queue and sends.
        
        Runs as a task for the lifetime of the connection.
        Never blocks the event loop waiting on a slow client.
        """
        q = self._client_queues.get(websocket)
        if q is None:
            return
        try:
            while True:
                msg = await q.get()
                try:
                    await websocket.send(msg)
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception:
                    pass
        except asyncio.CancelledError:
            pass
    
    def push_live_transcription(self, text: str, role: str = 'jarvis', source: str = None, stream: str = None, kind: str = None, turn_id: int = None):
        """Central gateway for Gemini Live transcription messages.
        
        This is the SINGLE authoritative path for live transcriptions to reach clients.
        Handles cross-pipeline deduplication: if a 'result' message was just sent with
        similar text, this skips to prevent duplicates.
        """
        if not text or not text.strip():
            return
        text = text.strip()
        
        print(f"[TRANSCRIPT] src={source} stream={stream} kind={kind} turn={turn_id} | {text[:60]}")
        
        if getattr(self, "live_engine", None):
            if source != "gemini_live" or stream != "live" or kind != "transcript":
                return
        
        # Cross-pipeline dedup: check if command pipeline just sent this
        import time as _plt
        now = _plt.time()
        if self._recent_result_text and (now - self._recent_result_time) < 3:
            # Check word overlap between live transcription and recent result
            result_words = set(self._recent_result_text.lower().split())
            live_words = set(text.lower().split())
            if result_words and live_words:
                overlap = len(result_words & live_words) / max(len(live_words), 1)
                if overlap > 0.5:
                    return  # Skip — command pipeline already sent this
        
        msg = json.dumps({
            'type': 'live_transcription',
            'text': text,
            'role': role,
            'speak': False,
            'source': source if source else 'gemini_live',
            'channel': 'live'
        })
        
        loop = self._voice_loop
        if not loop:
            return
        
        # Route through per-client queue — prevents concurrent ws.send() violations
        for client in list(self.clients):
            channels = self._client_channels.get(client, {'command', 'stats', 'live', 'sensors'})
            if 'live' in channels:
                q = self._client_queues.get(client)
                if q:
                    try:
                        asyncio.run_coroutine_threadsafe(q.put(msg), loop)
                    except Exception:
                        pass
    
    async def start(self):
        """Start the server"""
        with open(self.log_file, "a") as f:
            f.write(f"[{datetime.now()}] Entering start()\n")
            
        self.running = True
        print(f"\n{'='*55}")
        print(f"  {self.hud_perception.assistant_name} WebSocket Server")
        print(f"{'='*55}")
        print(f"  Address: ws://{self.host}:{self.port}")
        print(f"  Status:  Online")
        print(f"  Voice:   {self.hud_perception.assistant_name}")
        print(f"  Full JARVIS: {'Yes' if self.jarvis else 'Fallback Mode'}")
        print(f"  Gesture: {'Available' if self.gesture_controller else 'Not Available'}")
        print(f"  Face:    {'Available' if self.face_recognition else 'Not Available'}")
        print(f"  Emotion: {'Available' if self.emotion_detector else 'Not Available'}")
        print(f"{'='*55}\n")
        
        try:
            with open(self.log_file, "a") as f:
                f.write(f"[{datetime.now()}] Starting websockets.serve on {self.host}:{self.port}\n")
            
            # Store event loop ref so voice thread can inject coroutines
            self._voice_loop = asyncio.get_event_loop()
            
            # Start voice listening thread
            self._start_voice_thread()
            
            # Start gesture processing thread
            self._start_gesture_thread()
                
            async with websockets.serve(self.handle_client, self.host, self.port):
                with open(self.log_file, "a") as f:
                    f.write(f"[{datetime.now()}] Server running, waiting for connections...\n")
                await asyncio.Future()
        except Exception as e:
            with open(self.log_file, "a") as f:
                f.write(f"[{datetime.now()}] Error in start(): {e}\n")
            print(f"[WebSocket] Error in start: {e}")
            import traceback
            traceback.print_exc()

    def run_in_thread(self):
        """Run in background thread"""
        with open(self.log_file, "a") as f:
            f.write(f"[{datetime.now()}] run_in_thread called\n")
            
        def run():
            try:
                with open(self.log_file, "a") as f:
                    f.write(f"[{datetime.now()}] Thread started, calling asyncio.run\n")
                asyncio.run(self.start())
            except Exception as e:
                with open(self.log_file, "a") as f:
                    f.write(f"[{datetime.now()}] Thread crashed: {e}\n")
                    
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread


if __name__ == "__main__":
    server = JARVISWebSocketServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n[WebSocket] Server stopped")
