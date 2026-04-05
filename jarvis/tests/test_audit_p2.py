"""
JARVIS Module Audit - Part 2: Priority 5-7 (FIXED)
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

results = []

def test_result(name, passed, error=None):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status}: {name}")
    if error and not passed:
        print(f"         Error: {str(error)[:80]}")
    results.append((name, passed))
    return passed

def header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

# =====================================================
# PRIORITY 5: INTENT SYSTEM
# =====================================================

header("PRIORITY 5: INTENT SYSTEM")

# ---------- Intent Classifier ----------
print("\n[1] intent_classifier.py")
try:
    from core.intent_classifier import classify_intent, split_commands
    test_result("intent_classifier: Import", True)
    # Test classify
    intent, entities = classify_intent("what is the time")
    test_result("intent_classifier: classify", intent is not None)
except Exception as e:
    test_result("intent_classifier", False, e)

# ---------- Intent Handlers ----------
print("\n[2] intent_handlers.py")
try:
    from core.intent_handlers import handle_time, handle_weather, handle_greeting
    test_result("intent_handlers: Import", True)
    # Test handle_time
    result = handle_time("what time", {}, None)
    test_result("intent_handlers: handle_time", result is not None)
except Exception as e:
    test_result("intent_handlers", False, e)

# ---------- Intent Router ----------
print("\n[3] intent_router.py")
try:
    from core.intent_router import IntentRouter, Intent, HandlerResult
    ir = IntentRouter()
    test_result("intent_router: Init", True)
    test_result("intent_router: has_route", hasattr(ir, 'route'))
except Exception as e:
    test_result("intent_router", False, e)

# =====================================================
# PRIORITY 6: CORE SYSTEM
# =====================================================

header("PRIORITY 6: CORE SYSTEM")

# ---------- Perception ----------
print("\n[4] perception.py")
try:
    from core.perception import PerceptionLayer
    test_result("perception: Import", True)
except Exception as e:
    test_result("perception", False, e)

# ---------- Personality ----------
print("\n[5] personality.py")
try:
    from core.personality import JARVISPersonality
    jp = JARVISPersonality()
    test_result("personality: Init", True)
except Exception as e:
    test_result("personality", False, e)

# ---------- State Manager ----------
print("\n[6] state_manager.py")
try:
    from core.state_manager import StateManager
    sm = StateManager()
    test_result("state_manager: Init", True)
except Exception as e:
    test_result("state_manager", False, e)

# =====================================================
# PRIORITY 7: ALL REMAINING
# =====================================================

header("PRIORITY 7: ALL REMAINING")

remaining = [
    "context_memory", "chat_history", "smooth_voice", "sound_effects",
    "smart_notes", "task_manager", "habit_tracker", "wellness_monitor",
    "proactive_assistant", "learning", "knowledge", "action", 
    "understanding", "calendar_integration", "hotkey_system",
    "youtube_downloader", "settings_manager"
]

for mod_name in remaining:
    print(f"\n[*] {mod_name}.py")
    try:
        mod = __import__(f"core.{mod_name}", fromlist=['*'])
        attrs = [a for a in dir(mod) if not a.startswith('_')]
        test_result(f"{mod_name}: Import", len(attrs) > 0)
    except Exception as e:
        test_result(mod_name, False, e)

# =====================================================
# SUMMARY
# =====================================================

header("FINAL SUMMARY")
passed = sum(1 for _, p in results if p)
failed = sum(1 for _, p in results if not p)
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Total: {len(results)}")

if failed > 0:
    print("\nFailed tests:")
    for name, p in results:
        if not p:
            print(f"  - {name}")
else:
    print("\n  ALL TESTS PASSED!")
