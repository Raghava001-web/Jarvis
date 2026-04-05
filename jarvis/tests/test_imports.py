"""
Phase 7: Test whether the sys.path fix makes all imports succeed
"""
import sys, os

# Simulate running from jarvis/ directory  
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.getcwd())

# Add project root (same as websocket_server.py now does)
project_root = os.path.dirname(os.getcwd())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Testing 'from jarvis.core.X' imports...")
print()

modules = [
    ('jarvis.core.intent_classifier', 'classify_intent'),
    ('jarvis.core.intent_handlers', 'HANDLER_MAP'),
    ('jarvis.core.intent_router', 'IntentRouter'),
    ('jarvis.core.perception', 'PerceptionLayer'),
    ('jarvis.core.alarm_system', 'AlarmSystem'),
    ('jarvis.core.system_control', 'SystemControl'),
    ('jarvis.core.app_finder', 'AppFinder'),
    ('jarvis.core.music_handler', 'MusicHandler'),
    ('jarvis.core.weather_handler', 'WeatherHandler'),
    ('jarvis.core.news_handler', 'NewsHandler'),
    ('jarvis.core.dictionary_handler', 'DictionaryHandler'),
    ('jarvis.core.entertainment', 'JARVISEntertainment'),
    ('jarvis.core.screenshot_handler', 'ScreenshotHandler'),
    ('jarvis.core.ocr_handler', 'OCRHandler'),
    ('jarvis.core.context_memory', 'ContextMemory'),
    ('jarvis.core.chat_history', 'ChatHistory'),
    ('jarvis.core.state_manager', 'StateManager'),
    ('jarvis.core.reminder_manager', 'ReminderManager'),
    ('jarvis.core.knowledge', 'KnowledgeLayer'),
    ('jarvis.core.system_status', 'SystemStatus'),
    ('jarvis.core.screen_control', 'ScreenControlHandler'),
    ('jarvis.core.whatsapp_handler', 'WhatsAppHandler'),
]

ok = 0
fail = 0
for mod_path, cls_name in modules:
    try:
        mod = __import__(mod_path, fromlist=[cls_name])
        cls = getattr(mod, cls_name)
        print(f"  OK   {mod_path}.{cls_name}")
        ok += 1
    except Exception as e:
        print(f"  FAIL {mod_path}.{cls_name}: {e}")
        fail += 1

print(f"\n{ok} passed, {fail} failed")
