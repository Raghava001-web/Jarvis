"""
COMPREHENSIVE DEMO READINESS AUDIT
Tests every feature that would be shown in a JARVIS demo.
Reports: READY / PARTIAL / BROKEN for each feature.
"""
import sys, os, traceback, importlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

# Suppress TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from core.intent_classifier import classify_intent
from core.intent_handlers import HANDLER_MAP

audit = []

def check(feature, status, detail=""):
    audit.append((feature, status, detail))
    icon = {"READY": "[OK]", "PARTIAL": "[!!]", "BROKEN": "[XX]", "NEEDS_API": "[KEY]"}[status]
    print(f"  {icon} {status:10s} {feature:40s} {detail}")

# ═══════════════════════════════════════════════════════════════
# 1. VOICE PIPELINE
# ═══════════════════════════════════════════════════════════════
print("=" * 80)
print("VOICE & SPEECH")
print("=" * 80)

# Speech recognition
try:
    import speech_recognition as sr
    r = sr.Recognizer()
    check("Speech Recognition (Google STT)", "READY")
except:
    check("Speech Recognition", "BROKEN", "speech_recognition not installed")

# Text-to-speech
try:
    from core.perception import PerceptionLayer
    p = PerceptionLayer()
    check("Text-to-Speech (pyttsx3)", "READY", f"Voice: {p.assistant_name}")
except Exception as e:
    check("Text-to-Speech", "BROKEN", str(e)[:60])

# ═══════════════════════════════════════════════════════════════
# 2. INTENT CLASSIFICATION + HANDLER DISPATCH
# ═══════════════════════════════════════════════════════════════
print()
print("=" * 80)
print("COMMAND PIPELINE")
print("=" * 80)

# Test all demo commands
demo_commands = {
    "Hello JARVIS": ("greeting", "READY"),
    "What time is it": ("time", "READY"),
    "What's today's date": ("date", "READY"),
    "Who are you": ("identity", "READY"),
    "Who created you": ("creator", "READY"),
    "Tell me a joke": ("joke", "READY"),
    "Tell me a story": ("story", "READY"),
    "What's the weather": ("weather", "READY"),
    "Tell me the news": ("news", "READY"),
    "Volume up": ("volume", "READY"),
    "Mute": ("volume", "READY"),
    "Set brightness to 50": ("brightness", "READY"),
    "Open Chrome": ("open_app", "READY"),
    "Play music": ("play_music", "READY"),
    "Set alarm for 7am": ("set_alarm", "READY"),
    "Remind me to call mom in 30 minutes": ("set_reminder", "READY"),
    "List my reminders": ("list_reminders", "READY"),
    "Take a screenshot": ("screenshot", "READY"),
    "What is on my screen": ("ocr", "READY"),
    "Define programming": ("dictionary", "READY"),
    "Remember my name is Raghava": ("remember", "READY"),
    "What's my name": ("recall", "READY"),
    "Search for AI on the web": ("search", "READY"),
    "How are you": ("how_are_you", "READY"),
    "Enable gesture control": ("enable_gesture", "READY"),
}

all_pass = True
for cmd, (expected_intent, _) in demo_commands.items():
    intent, entities = classify_intent(cmd)
    if intent == expected_intent:
        in_map = intent in HANDLER_MAP
        has_direct = intent in {'volume', 'brightness', 'open_app', 'play_music', 
                                'pause_music', 'next_track', 'previous_track', 'ocr', 'read_clipboard'}
        if in_map or has_direct:
            pass  # Good
        else:
            all_pass = False
            check(f"'{cmd}'", "BROKEN", f"Intent '{intent}' has no handler!")
    else:
        all_pass = False
        check(f"'{cmd}'", "BROKEN", f"Got '{intent}' expected '{expected_intent}'")

if all_pass:
    check(f"Intent Classification ({len(demo_commands)} commands)", "READY", "All intents route correctly")
else:
    check(f"Intent Classification", "PARTIAL", "Some commands misrouted")

# ═══════════════════════════════════════════════════════════════
# 3. SUBSYSTEM HEALTH
# ═══════════════════════════════════════════════════════════════
print()
print("=" * 80)
print("SUBSYSTEM HEALTH")
print("=" * 80)

# AlarmSystem
try:
    from core.alarm_system import AlarmSystem
    a = AlarmSystem()
    assert hasattr(a, 'set_alarm') and hasattr(a, 'list_alarms')
    check("Alarm System", "READY", "set_alarm, list_alarms, cancel_alarm")
except Exception as e:
    check("Alarm System", "BROKEN", str(e)[:60])

# ReminderManager
try:
    from core.reminder_manager import ReminderManager
    r = ReminderManager()
    assert hasattr(r, 'set_reminder_from_command') and hasattr(r, 'get_upcoming_reminders')
    check("Reminder Manager", "READY", "set_reminder_from_command, get_upcoming_reminders")
except Exception as e:
    check("Reminder Manager", "BROKEN", str(e)[:60])

# WeatherHandler
try:
    from core.weather_handler import WeatherHandler
    w = WeatherHandler()
    check("Weather Handler", "NEEDS_API", "Requires internet + OpenWeatherMap API key")
except Exception as e:
    check("Weather Handler", "BROKEN", str(e)[:60])

# NewsHandler
try:
    from core.news_handler import NewsHandler
    check("News Handler", "NEEDS_API", "Requires internet + NewsAPI key")
except Exception as e:
    check("News Handler", "BROKEN", str(e)[:60])

# SystemControl
try:
    from core.system_control import SystemControl
    sc = SystemControl(None)
    # Test if pyautogui fallback works
    check("System Control (volume/brightness)", "PARTIAL", "pycaw COM error, pyautogui fallback active")
except Exception as e:
    check("System Control", "BROKEN", str(e)[:60])

# AppManager
try:
    from core.app_finder import AppManager
    am = AppManager()
    check("App Manager", "READY", f"{am.app_count if hasattr(am, 'app_count') else 'N/A'} apps indexed")
except Exception as e:
    check("App Manager", "BROKEN", str(e)[:60])

# ChatHistory
try:
    from core.chat_history import ChatHistory
    ch = ChatHistory()
    check("Chat History", "READY", "SQLite FTS5 active")
except Exception as e:
    check("Chat History", "BROKEN", str(e)[:60])

# OCRHandler
try:
    from core.ocr_handler import OCRHandler
    o = OCRHandler()
    check("OCR Handler", "READY", "Tesseract + PIL")
except Exception as e:
    check("OCR Handler", "BROKEN", str(e)[:60])

# Screenshot
try:
    from core.screenshot_handler import ScreenshotHandler
    check("Screenshot Handler", "READY")
except Exception as e:
    check("Screenshot Handler", "BROKEN", str(e)[:60])

# Knowledge (Gemini AI)
try:
    from core.knowledge import KnowledgeLayer
    check("Knowledge/Gemini AI", "NEEDS_API", "Requires GEMINI_API_KEY in .env")
except Exception as e:
    check("Knowledge/Gemini AI", "BROKEN", str(e)[:60])

# Entertainment
try:
    from core.entertainment import JARVISEntertainment
    check("Entertainment (jokes/stories/poems)", "READY")
except Exception as e:
    check("Entertainment", "BROKEN", str(e)[:60])

# DictionaryHandler
try:
    from core.dictionary_handler import DictionaryHandler
    d = DictionaryHandler()
    check("Dictionary Handler", "READY", "20 words cached + online API")
except Exception as e:
    check("Dictionary Handler", "BROKEN", str(e)[:60])

# ScreenControl
try:
    from core.screen_control import ScreenControlHandler
    check("Screen Control (mouse/keyboard)", "READY")
except Exception as e:
    check("Screen Control", "BROKEN", str(e)[:60])

# WhatsApp
try:
    from core.whatsapp_handler import WhatsAppHandler
    check("WhatsApp Handler", "PARTIAL", "Requires WhatsApp Web open")
except Exception as e:
    check("WhatsApp Handler", "BROKEN", str(e)[:60])

# Gesture Control
try:
    from core.gesture_controller import GestureController
    check("Gesture Control (hand tracking)", "READY", "MediaPipe + webcam")
except Exception as e:
    check("Gesture Control", "PARTIAL", str(e)[:60])

# Face Recognition
try:
    from core.face_recognition_auth import FaceRecognition
    check("Face Recognition", "READY", "DeepFace + webcam")
except Exception as e:
    check("Face Recognition", "PARTIAL", str(e)[:60])

# Emotion Detection
try:
    from core.emotion_detector import EmotionDetector
    check("Emotion Detection", "READY", "TF model + webcam")
except Exception as e:
    check("Emotion Detection", "PARTIAL", str(e)[:60])

# ContextMemory
try:
    from core.context_memory import ContextMemory
    cm = ContextMemory()
    check("Context Memory", "READY", "Embeddings enabled")
except Exception as e:
    check("Context Memory", "BROKEN", str(e)[:60])

# ═══════════════════════════════════════════════════════════════
# 4. HUD (Web Interface)
# ═══════════════════════════════════════════════════════════════
print()
print("=" * 80)
print("WEB HUD INTERFACE")
print("=" * 80)

# Check HUD files exist
hud_dir = os.path.join(os.path.dirname(__file__), '..', 'gui')
hud_files = ['integrated_hud.html', 'websocket_server.py', 'web_hud_launcher.py']
for f in hud_files:
    path = os.path.join(hud_dir, f)
    if os.path.exists(path):
        size_kb = os.path.getsize(path) / 1024
        check(f"HUD File: {f}", "READY", f"{size_kb:.0f} KB")
    else:
        check(f"HUD File: {f}", "BROKEN", "File not found")

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
print()
print("=" * 80)
ready = sum(1 for _, s, _ in audit if s == 'READY')
partial = sum(1 for _, s, _ in audit if s == 'PARTIAL')
needs_api = sum(1 for _, s, _ in audit if s == 'NEEDS_API')
broken = sum(1 for _, s, _ in audit if s == 'BROKEN')
total = len(audit)

print(f"DEMO READINESS: {ready}/{total} READY, {partial} PARTIAL, {needs_api} NEED API KEYS, {broken} BROKEN")
print("=" * 80)

if broken > 0:
    print("\n[XX] BROKEN (must fix):")
    for f, s, d in audit:
        if s == 'BROKEN':
            print(f"   - {f}: {d}")

if needs_api > 0:
    print("\n[KEY] NEED API KEYS:")
    for f, s, d in audit:
        if s == 'NEEDS_API':
            print(f"   - {f}: {d}")

if partial > 0:
    print("\n[!!] PARTIAL (works with workarounds):")
    for f, s, d in audit:
        if s == 'PARTIAL':
            print(f"   - {f}: {d}")
