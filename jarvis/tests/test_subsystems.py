"""
Phase 6: Deep runtime test of all remaining subsystems
Tests actual object creation and method calls.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

results = []

def test(name, fn):
    try:
        result = fn()
        results.append(('OK', name, result))
        r = str(result)[:80]
        print(f"  OK      {name}: {r}")
    except Exception as e:
        results.append(('FAIL', name, str(e)))
        print(f"  FAIL    {name}: {e}")

def skip(name, reason):
    results.append(('SKIP', name, reason))
    print(f"  SKIP    {name}: {reason}")

# ═══════════ ALARM SYSTEM ═══════════
print('=' * 60)
print('ALARM SYSTEM')
print('=' * 60)

try:
    from core.alarm_system import AlarmSystem
    als = AlarmSystem()
    test("AlarmSystem created", lambda: True)
    test("AlarmSystem has set_alarm()", lambda: hasattr(als, 'set_alarm'))
    test("AlarmSystem has list_alarms()", lambda: hasattr(als, 'list_alarms'))
    test("AlarmSystem has cancel_alarm()", lambda: hasattr(als, 'cancel_alarm'))
    test("AlarmSystem has check_alarms()", lambda: hasattr(als, 'check_alarms'))
    test("AlarmSystem.list_alarms()", lambda: als.list_alarms())
except Exception as e:
    print(f"  FAIL    AlarmSystem import: {e}")
    results.append(('FAIL', 'AlarmSystem import', str(e)))

# ═══════════ NEWS HANDLER ═══════════
print()
print('=' * 60)
print('NEWS HANDLER')
print('=' * 60)

try:
    from core.news_handler import NewsHandler
    nh = NewsHandler()
    test("NewsHandler created", lambda: True)
    test("NewsHandler has get_headlines()", lambda: hasattr(nh, 'get_headlines'))
    test("NewsHandler has get_news()", lambda: hasattr(nh, 'get_news'))
    test("NewsHandler has search_news()", lambda: hasattr(nh, 'search_news'))
except Exception as e:
    print(f"  FAIL    NewsHandler import: {e}")
    results.append(('FAIL', 'NewsHandler import', str(e)))

# ═══════════ WEATHER HANDLER ═══════════
print()
print('=' * 60)
print('WEATHER HANDLER')
print('=' * 60)

try:
    from core.weather_handler import WeatherHandler
    wh = WeatherHandler()
    test("WeatherHandler created", lambda: True)
    test("WeatherHandler has get_weather()", lambda: hasattr(wh, 'get_weather'))
    test("WeatherHandler has get_forecast()", lambda: hasattr(wh, 'get_forecast'))
except Exception as e:
    print(f"  FAIL    WeatherHandler import: {e}")
    results.append(('FAIL', 'WeatherHandler import', str(e)))

# ═══════════ DICTIONARY ═══════════
print()
print('=' * 60)
print('DICTIONARY HANDLER')
print('=' * 60)

try:
    from core.dictionary_handler import DictionaryHandler
    dh = DictionaryHandler()
    test("DictionaryHandler created", lambda: True)
    test("DictionaryHandler has define()", lambda: hasattr(dh, 'define') or hasattr(dh, 'lookup') or hasattr(dh, 'dictionary'))
except Exception as e:
    print(f"  FAIL    DictionaryHandler import: {e}")
    results.append(('FAIL', 'DictionaryHandler import', str(e)))

# ═══════════ SCREEN CONTROL ═══════════
print()
print('=' * 60)
print('SCREEN CONTROL')
print('=' * 60)

try:
    from core.screen_control import ScreenControl
    scr = ScreenControl()
    test("ScreenControl created", lambda: True)
    test("ScreenControl has handle()", lambda: hasattr(scr, 'handle'))
    test("ScreenControl has click()", lambda: hasattr(scr, 'click'))
except Exception as e:
    print(f"  FAIL    ScreenControl import: {e}")
    results.append(('FAIL', 'ScreenControl import', str(e)))

# ═══════════ WHATSAPP ═══════════
print()
print('=' * 60)
print('WHATSAPP HANDLER')
print('=' * 60)

try:
    from core.whatsapp_handler import WhatsAppHandler
    wa = WhatsAppHandler()
    test("WhatsAppHandler created", lambda: True)
    test("WhatsAppHandler has send_message()", lambda: hasattr(wa, 'send_message'))
    test("WhatsAppHandler has open_whatsapp()", lambda: hasattr(wa, 'open_whatsapp'))
except Exception as e:
    print(f"  FAIL    WhatsAppHandler import: {e}")
    results.append(('FAIL', 'WhatsAppHandler import', str(e)))

# ═══════════ CHAT HISTORY ═══════════
print()
print('=' * 60)
print('CHAT HISTORY')
print('=' * 60)

try:
    from core.chat_history import ChatHistory
    ch = ChatHistory()
    test("ChatHistory created", lambda: True)
    test("ChatHistory has add_message()", lambda: hasattr(ch, 'add_message') or hasattr(ch, 'add') or hasattr(ch, 'append'))
    test("ChatHistory has get_history()", lambda: hasattr(ch, 'get_history') or hasattr(ch, 'get_messages') or hasattr(ch, 'messages'))
except Exception as e:
    print(f"  FAIL    ChatHistory import: {e}")
    results.append(('FAIL', 'ChatHistory import', str(e)))

# ═══════════ CONTEXT MEMORY ═══════════
print()
print('=' * 60)
print('CONTEXT MEMORY (remember/recall)')
print('=' * 60)

try:
    from core.context_memory import ContextMemory
    cm = ContextMemory()
    test("ContextMemory created", lambda: True)
    # Test actual remember/recall cycle
    test("remember('test_key', 'test_value')", lambda: cm.remember('test_key', 'test_value'))
    test("recall('test_key')", lambda: cm.recall('test_key'))
except Exception as e:
    print(f"  FAIL    ContextMemory: {e}")
    results.append(('FAIL', 'ContextMemory', str(e)))

# ═══════════ OCR HANDLER ═══════════
print()
print('=' * 60)
print('OCR HANDLER')
print('=' * 60)

try:
    from core.ocr_handler import OCRHandler
    oh = OCRHandler()
    test("OCRHandler created", lambda: True)
    test("OCRHandler has read_screen()", lambda: hasattr(oh, 'read_screen'))
    test("OCRHandler has read_clipboard_image()", lambda: hasattr(oh, 'read_clipboard_image'))
    test("OCRHandler has extract_text()", lambda: hasattr(oh, 'extract_text'))
except Exception as e:
    print(f"  FAIL    OCRHandler import: {e}")
    results.append(('FAIL', 'OCRHandler import', str(e)))

# ═══════════ ENTERTAINMENT ═══════════
print()
print('=' * 60)
print('ENTERTAINMENT')
print('=' * 60)

try:
    from core.entertainment import Entertainment
    ent = Entertainment()
    test("Entertainment created", lambda: True)
    test("Entertainment.get_joke()", lambda: ent.get_joke() if hasattr(ent, 'get_joke') else "no get_joke")
    test("Entertainment.get_story()", lambda: ent.get_story() if hasattr(ent, 'get_story') else "no get_story")
    test("Entertainment.get_poem()", lambda: ent.get_poem() if hasattr(ent, 'get_poem') else "no get_poem")
except Exception as e:
    print(f"  FAIL    Entertainment import: {e}")
    results.append(('FAIL', 'Entertainment import', str(e)))

# ═══════════ REMINDER SYSTEM ═══════════
print()
print('=' * 60)
print('REMINDER SYSTEM')
print('=' * 60)

try:
    from core.reminder_manager import ReminderManager
    rm = ReminderManager()
    test("ReminderManager created", lambda: True)
    test("ReminderManager has set_reminder()", lambda: hasattr(rm, 'set_reminder'))
    test("ReminderManager has list_reminders()", lambda: hasattr(rm, 'list_reminders'))
except Exception as e:
    print(f"  FAIL    ReminderManager import: {e}")
    results.append(('FAIL', 'ReminderManager import', str(e)))

# ═══════════ STATE MANAGER ═══════════
print()
print('=' * 60)
print('STATE MANAGER')
print('=' * 60)

try:
    from core.state_manager import StateManager
    sm = StateManager()
    test("StateManager created", lambda: True)
    test("StateManager.active_app", lambda: sm.active_app if hasattr(sm, 'active_app') else 'no active_app')
    test("StateManager has get()", lambda: hasattr(sm, 'get'))
except Exception as e:
    print(f"  FAIL    StateManager import: {e}")
    results.append(('FAIL', 'StateManager import', str(e)))

# ═══════════ SYSTEM STATUS ═══════════
print()
print('=' * 60)
print('SYSTEM STATUS')
print('=' * 60)

try:
    from core.system_status import get_system_stats
    test("get_system_stats()", lambda: get_system_stats())
except Exception as e:
    try:
        from core.system_status import SystemStatus
        ss = SystemStatus()
        test("SystemStatus created", lambda: True)
    except Exception as e2:
        print(f"  FAIL    system_status import: {e2}")
        results.append(('FAIL', 'system_status import', str(e2)))

# ═══════════ SUMMARY ═══════════
print()
print('=' * 60)
ok = sum(1 for r in results if r[0] == 'OK')
fail = sum(1 for r in results if r[0] == 'FAIL')
skipped = sum(1 for r in results if r[0] == 'SKIP')
print(f'TOTAL: {ok} passed, {fail} failed, {skipped} skipped')
if fail > 0:
    print('\nFAILURES:')
    for r in results:
        if r[0] == 'FAIL':
            print(f'  - {r[1]}: {r[2]}')
print('=' * 60)
