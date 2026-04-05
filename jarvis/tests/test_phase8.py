"""Phase 8 Comprehensive Verification Test"""
import sys, os
os.chdir(r'c:\Users\chrag\OneDrive\Documents\AI_Voice_Assistant')
sys.path.insert(0, '.')
sys.path.insert(0, 'jarvis')

class MockPerception:
    user_title = 'sir'
    def speak(self, t): pass

PASSED = 0
FAILED = 0

def check(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name} {detail}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} {detail}")

print("=" * 60)
print("PHASE 8 VERIFICATION TEST")
print("=" * 60)

# 1. Email Handler
print("\n--- 1. Email Handler ---")
try:
    from jarvis.core.email_handler import EmailHandler
    eh = EmailHandler(MockPerception())
    check("send_email exists", hasattr(eh, 'send_email'))
    check("send_reminder_email exists", hasattr(eh, 'send_reminder_email'))
    check("smtp_email set", eh.smtp_email == "jarvisaif0009@gmail.com")
except Exception as e:
    check("import", False, str(e))

# 2. Entertainment
print("\n--- 2. Entertainment ---")
try:
    from jarvis.core.entertainment import JARVISEntertainment, EntertainmentEngine
    ent = JARVISEntertainment()
    
    joke = ent.tell_joke()
    check("tell_joke returns str", isinstance(joke, str) and len(joke) > 5, joke[:40])
    
    riddle = ent.tell_riddle()
    check("tell_riddle returns str", isinstance(riddle, str) and len(riddle) > 5)
    
    poem = ent.recite_poem()
    check("recite_poem returns str", isinstance(poem, str) and len(poem) > 5)
    
    song = ent.sing_song()
    check("sing_song returns str", isinstance(song, str) and len(song) > 5)
    
    result = ent.entertain("tell me a joke")
    check("entertain returns str", isinstance(result, str) and len(result) > 5)
    
    check("EntertainmentEngine alias", EntertainmentEngine is JARVISEntertainment)
except Exception as e:
    check("import", False, str(e))

# 3. WhatsApp
print("\n--- 3. WhatsApp ---")
try:
    from jarvis.core.whatsapp_handler import WhatsAppHandler
    wh = WhatsAppHandler(MockPerception())
    result = wh.send_message()
    check("send_message(no args) returns str", isinstance(result, str))
    check("has open_whatsapp", hasattr(wh, 'open_whatsapp'))
    check("has read_messages", hasattr(wh, 'read_messages'))
except Exception as e:
    check("import", False, str(e))

# 4. Context Memory
print("\n--- 4. Context Memory ---")
try:
    from jarvis.core.context_memory import ContextMemory
    cm = ContextMemory()
    cm.working.add_turn("hello", "Hi!", "greeting")
    ctx = cm.working.get_context_prompt()
    check("WorkingMemory works", isinstance(ctx, str) and len(ctx) > 0)
    
    cm.long_term.remember("user likes Python", "preference")
    results = cm.long_term.recall("what does user like")
    check("LongTermMemory recall", len(results) > 0)
except Exception as e:
    check("import", False, str(e))

# 5. Reminder
print("\n--- 5. Reminder ---")
try:
    from jarvis.core.reminder_manager import ReminderManager
    rm = ReminderManager()
    result = rm.parse_reminder("remind me to drink water in 10 minutes")
    check("parse_reminder works", result is not None, str(result[0]) if result else "None")
except Exception as e:
    check("import", False, str(e))

# 6. Proactive Assistant
print("\n--- 6. Proactive Assistant ---")
try:
    from jarvis.core.proactive_assistant import ProactiveAssistant
    pa = ProactiveAssistant()
    check("ProactiveAssistant init", pa is not None)
except Exception as e:
    check("import", False, str(e))

# 7. Music Handler
print("\n--- 7. Music Handler ---")
try:
    from jarvis.core.music_handler import MusicHandler
    mh = MusicHandler()
    check("MusicHandler init", mh is not None)
except Exception as e:
    check("import", False, str(e))

# 8. Intent Handlers HANDLER_MAP
print("\n--- 8. HANDLER_MAP ---")
try:
    from jarvis.core.intent_handlers import HANDLER_MAP
    for intent in ['set_reminder', 'list_reminders', 'dictionary', 'joke', 'poem', 'story']:
        check(f"HANDLER_MAP[{intent}]", intent in HANDLER_MAP)
except Exception as e:
    check("import", False, str(e))

print("\n" + "=" * 60)
print(f"RESULTS: {PASSED} passed, {FAILED} failed")
print("=" * 60)
