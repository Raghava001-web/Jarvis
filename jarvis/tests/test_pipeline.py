"""
FINAL comprehensive pipeline test — all Phase 5 fixes
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from core.intent_classifier import classify_intent
from core.intent_handlers import HANDLER_MAP

handler_context = {
    'title': 'sir',
    'system_stats': {'cpu': 30, 'memory': 55, 'disk': 70, 'battery': 80, 'charging': True},
    'alarm_system': None,
    'screenshot_handler': None,
    'knowledge': None,
    'state_manager': None,
    'weather_handler': None,
    'news_handler': None,
    'entertainment': None,
}

test_commands = [
    # Basic intents
    'what time is it',
    'what is the date',
    'hello jarvis',
    'goodbye',
    'tell me a joke',
    'who are you',
    'who created you',
    'system status',
    'help',
    'tell me a story',
    'how are you',
    'thank you',
    # System control
    'volume up',
    'volume down',
    'mute',
    'set volume to 50',
    'brightness up',
    # App control
    'open chrome',
    'open notepad',
    'switch to firefox',
    'go to calculator',
    'close chrome',
    # Music
    'play music',
    'pause music',
    'next song',
    'previous song',
    # Memory
    'remember my name is raghava',
    'recall my name',
    # Screen
    'take a screenshot',
    'what is on my screen',
    'read clipboard',
    # Misc
    'whats up',
    'set alarm for 7am',
]

# Direct hardware intents (handled before HANDLER_MAP in _route_through_router)
DIRECT_INTENTS = {'volume', 'brightness', 'open_app', 'close_app',
                  'play_music', 'pause_music', 'next_track', 'previous_track',
                  'ocr', 'read_clipboard'}

passed = 0
failed = 0

print('=' * 70)
print(f'  INTENT{"":32s} HANDLER       RESULT')
print('=' * 70)

for cmd in test_commands:
    try:
        intent_name, entities = classify_intent(cmd)
        
        if intent_name in DIRECT_INTENTS:
            print(f'  {cmd:38s} {intent_name:14s} [DIRECT HANDLER]')
            passed += 1
            continue
        
        if intent_name in HANDLER_MAP:
            handler = HANDLER_MAP[intent_name]
            result = handler(cmd, entities, handler_context)
            
            if result and result.success and result.response:
                resp = result.response[:30] + '...' if len(result.response) > 30 else result.response
                print(f'  {cmd:38s} {intent_name:14s} {resp}')
                passed += 1
            else:
                print(f'  {cmd:38s} {intent_name:14s} [NO RESPONSE]')
                failed += 1
        else:
            print(f'  {cmd:38s} {intent_name:14s} [NO HANDLER]')
            failed += 1
    except Exception as e:
        print(f'  {cmd:38s} ERROR: {e}')
        failed += 1

print('=' * 70)
print(f'  RESULT: {passed} passed, {failed} failed out of {len(test_commands)}')
print('=' * 70)
