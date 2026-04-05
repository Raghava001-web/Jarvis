"""
Phase 7: Server Startup Integration Test
Simulates the full import chain and initialization flow of websocket_server.py
to catch runtime errors before the user starts the server.
"""
import sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

results = []

def test(name, fn):
    try:
        result = fn()
        results.append(('OK', name))
        r = str(result)[:80]
        print(f"  OK      {name}: {r}")
    except Exception as e:
        results.append(('FAIL', name))
        tb = traceback.format_exc().strip().split('\n')
        print(f"  FAIL    {name}")
        for line in tb[-3:]:
            print(f"          {line}")

# ═══════════════════════════════════════════════════════
# STEP 1: Test all imports used by websocket_server.py
# ═══════════════════════════════════════════════════════
print('=' * 70)
print('STEP 1: Import Chain')
print('=' * 70)

test("core.intent_classifier", lambda: __import__('core.intent_classifier', fromlist=['classify_intent']))
test("core.intent_handlers", lambda: __import__('core.intent_handlers', fromlist=['HANDLER_MAP']))
test("core.intent_router", lambda: __import__('core.intent_router', fromlist=['IntentRouter']))
test("core.perception", lambda: __import__('core.perception', fromlist=['PerceptionLayer']))
test("core.alarm_system", lambda: __import__('core.alarm_system', fromlist=['AlarmSystem']))
test("core.system_control", lambda: __import__('core.system_control', fromlist=['SystemControl']))
test("core.app_finder", lambda: __import__('core.app_finder', fromlist=['AppFinder', 'AppManager']))
test("core.music_handler", lambda: __import__('core.music_handler', fromlist=['MusicHandler']))
test("core.weather_handler", lambda: __import__('core.weather_handler', fromlist=['WeatherHandler']))
test("core.news_handler", lambda: __import__('core.news_handler', fromlist=['NewsHandler']))
test("core.dictionary_handler", lambda: __import__('core.dictionary_handler', fromlist=['DictionaryHandler']))
test("core.entertainment", lambda: __import__('core.entertainment', fromlist=['JARVISEntertainment']))
test("core.screenshot_handler", lambda: __import__('core.screenshot_handler', fromlist=['ScreenshotHandler']))
test("core.ocr_handler", lambda: __import__('core.ocr_handler', fromlist=['OCRHandler']))
test("core.context_memory", lambda: __import__('core.context_memory', fromlist=['ContextMemory']))
test("core.chat_history", lambda: __import__('core.chat_history', fromlist=['ChatHistory']))
test("core.state_manager", lambda: __import__('core.state_manager', fromlist=['StateManager']))
test("core.reminder_manager", lambda: __import__('core.reminder_manager', fromlist=['ReminderManager']))
test("core.knowledge", lambda: __import__('core.knowledge', fromlist=['KnowledgeLayer']))
test("core.system_status", lambda: __import__('core.system_status', fromlist=['SystemStatus']))

# Try screen_control and whatsapp
test("core.screen_control", lambda: __import__('core.screen_control'))
test("core.whatsapp_handler", lambda: __import__('core.whatsapp_handler'))

# ═══════════════════════════════════════════════════════
# STEP 2: Test websocket_server.py imports
# ═══════════════════════════════════════════════════════
print()
print('=' * 70)
print('STEP 2: WebSocket Server Module Import')
print('=' * 70)

test("gui.websocket_server (full import)", lambda: __import__('gui.websocket_server'))

# ═══════════════════════════════════════════════════════
# STEP 3: Test critical class instantiation
# ═══════════════════════════════════════════════════════
print()
print('=' * 70)
print('STEP 3: Critical Class Instantiation')
print('=' * 70)

# Classes that don't need perception
test("AlarmSystem()", lambda: __import__('core.alarm_system', fromlist=['AlarmSystem']).AlarmSystem())
test("ChatHistory()", lambda: __import__('core.chat_history', fromlist=['ChatHistory']).ChatHistory())
test("StateManager()", lambda: __import__('core.state_manager', fromlist=['StateManager']).StateManager())
test("ContextMemory()", lambda: __import__('core.context_memory', fromlist=['ContextMemory']).ContextMemory())
test("DictionaryHandler()", lambda: __import__('core.dictionary_handler', fromlist=['DictionaryHandler']).DictionaryHandler())
test("WeatherHandler()", lambda: __import__('core.weather_handler', fromlist=['WeatherHandler']).WeatherHandler())
test("ReminderManager()", lambda: __import__('core.reminder_manager', fromlist=['ReminderManager']).ReminderManager())
test("AppManager()", lambda: __import__('core.app_finder', fromlist=['AppManager']).AppManager())
test("OCRHandler()", lambda: __import__('core.ocr_handler', fromlist=['OCRHandler']).OCRHandler())
test("SystemControl(None)", lambda: __import__('core.system_control', fromlist=['SystemControl']).SystemControl(None))

# ═══════════════════════════════════════════════════════
# STEP 4: Test HANDLER_MAP completeness
# ═══════════════════════════════════════════════════════
print()
print('=' * 70)
print('STEP 4: HANDLER_MAP vs Intent Classifier Coverage')
print('=' * 70)

from core.intent_classifier import classify_intent
from core.intent_handlers import HANDLER_MAP

# Direct-handled intents (not in HANDLER_MAP, handled by _route_through_router)
DIRECT = {'volume', 'brightness', 'open_app', 'close_app',
          'play_music', 'pause_music', 'next_track', 'previous_track',
          'ocr', 'read_clipboard'}

# All possible intents from classifier
all_intents = set()
test_phrases = [
    'hello', 'goodbye', 'what time is it', 'what is the date',
    'who are you', 'who created you', 'system status', 'help',
    'tell me a joke', 'tell me a story', 'tell me a poem',
    'how are you', 'thank you',
    'what is the weather', 'tell me the news', 'search for AI',
    'volume up', 'volume down', 'mute', 'brightness up',
    'open chrome', 'switch to firefox', 'close notepad',
    'play music', 'pause music', 'next song', 'previous song',
    'set alarm for 7am', 'set timer for 5 minutes',
    'remind me to call mom in 30 minutes', 'list my reminders',
    'take a screenshot', 'what is on my screen', 'read clipboard',
    'define programming', 'remember my name is raghava', 'recall my name',
    'search for cats on reddit', 'search the web for python',
    'whats up', 'tell me something interesting',
    'play rain sounds', 'enable gesture control',
    'recognize face', 'improve yourself',
]

for phrase in test_phrases:
    intent, _ = classify_intent(phrase)
    all_intents.add(intent)

unhandled = []
for intent in all_intents:
    if intent not in HANDLER_MAP and intent not in DIRECT:
        unhandled.append(intent)

if unhandled:
    print(f"  WARN    Intents without handlers: {unhandled}")
else:
    print(f"  OK      All {len(all_intents)} intents have handlers or direct dispatch")
    results.append(('OK', 'Intent coverage'))

# ═══════════════════════════════════════════════════════
# STEP 5: Test _route_through_router dispatch conflicts
# ═══════════════════════════════════════════════════════
print()
print('=' * 70)
print('STEP 5: Dispatch Conflict Detection')
print('=' * 70)

# Check if same intent handled both directly AND in HANDLER_MAP
overlap = DIRECT.intersection(HANDLER_MAP.keys())
if overlap:
    print(f"  WARN    Intents in BOTH direct dispatch and HANDLER_MAP: {overlap}")
    print(f"          Direct dispatch takes priority, HANDLER_MAP versions unreachable")
    results.append(('OK', f'Dispatch overlap (ok, direct wins): {overlap}'))
else:
    print(f"  OK      No dispatch conflicts")
    results.append(('OK', 'No dispatch conflicts'))

# ═══════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════
print()
print('=' * 70)
ok = sum(1 for r in results if r[0] == 'OK')
fail = sum(1 for r in results if r[0] == 'FAIL')
print(f'TOTAL: {ok} passed, {fail} failed')
if fail > 0:
    print('\nFAILURES:')
    for r in results:
        if r[0] == 'FAIL':
            print(f'  - {r[1]}')
print('=' * 70)
