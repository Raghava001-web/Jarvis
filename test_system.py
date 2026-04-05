"""
JARVIS System Test Script
Tests all core modules and reports status
"""
import sys
sys.path.insert(0, 'jarvis')

def test_module(name, test_fn):
    try:
        result = test_fn()
        print(f"  {name}: OK {result if result else ''}")
        return True
    except Exception as e:
        print(f"  {name}: FAILED - {e}")
        return False

print("=" * 50)
print("JARVIS System Test")
print("=" * 50)

passed = 0
failed = 0

# Test StateManager
print("\n[1] Core Modules:")
if test_module("StateManager", lambda: (
    __import__('core.state_manager', fromlist=['get_state_manager']).get_state_manager(),
    ""
)[1]):
    passed += 1
else:
    failed += 1

if test_module("IntentClassifier", lambda: (
    __import__('core.intent_classifier', fromlist=['classify_intent']).classify_intent("hello"),
    ""
)[1]):
    passed += 1
else:
    failed += 1

if test_module("ContextMemory", lambda: (
    __import__('core.context_memory', fromlist=['get_context_memory']).get_context_memory(),
    ""
)[1]):
    passed += 1
else:
    failed += 1

# Test Vision
print("\n[2] Vision Modules:")
try:
    from core.gesture_controller import get_gesture_controller
    gc = get_gesture_controller()
    status = "Active" if gc.active else "Disabled"
    print(f"  GestureController: {status}")
    passed += 1
except Exception as e:
    print(f"  GestureController: FAILED - {e}")
    failed += 1

try:
    from core.face_auth import get_face_auth
    fa = get_face_auth()
    status = "dlib" if fa.available else "OpenCV fallback"
    users = len(fa.known_users)
    print(f"  FaceAuth: {status} ({users} users)")
    passed += 1
except Exception as e:
    print(f"  FaceAuth: FAILED - {e}")
    failed += 1

try:
    from core.emotion_detector import EmotionDetector
    ed = EmotionDetector()
    print(f"  EmotionDetector: OK")
    passed += 1
except Exception as e:
    print(f"  EmotionDetector: FAILED - {e}")
    failed += 1

# Test Handlers
print("\n[3] Handlers:")
handlers = [
    ("MusicHandler", "core.music_handler", "MusicHandler"),
    ("AlarmSystem", "core.alarm_system", "AlarmSystem"),
    ("AISearchHandler", "core.ai_search_handler", "AISearchHandler"),
    ("OCRHandler", "core.ocr_handler", "OCRHandler"),
    ("YouTubeDownloader", "core.youtube_downloader", "YouTubeDownloader"),
    ("HotkeySystem", "core.hotkey_system", "HotkeySystem"),
]

for name, module, cls in handlers:
    try:
        mod = __import__(module, fromlist=[cls])
        obj = getattr(mod, cls)
        # Try to check availability for relevant handlers
        status = "OK"
        if name == "OCRHandler":
            instance = obj()
            status = "OK (pytesseract)" if instance.pytesseract_available else "OK (no pytesseract)"
        elif name == "YouTubeDownloader":
            instance = obj()
            status = "OK (pytube)" if instance.pytube_available else "OK (no pytube)"
        print(f"  {name}: {status}")
        passed += 1
    except Exception as e:
        print(f"  {name}: FAILED - {e}")
        failed += 1

# Test Wake Word Detection
print("\n[4] Wake Word System:")
try:
    from core.perception import PerceptionLayer
    perception = PerceptionLayer()
    wake_words = perception.get_wake_words()
    print(f"  Wake Words: {wake_words}")
    passed += 1
except Exception as e:
    print(f"  Wake Words: FAILED - {e}")
    failed += 1

# Test JARVISUltimate
print("\n[4] Main Brain:")
try:
    from jarvis_ultimate import JARVISUltimate
    print("  JARVISUltimate: Import OK")
    passed += 1
except Exception as e:
    print(f"  JARVISUltimate: FAILED - {e}")
    failed += 1

# Summary
print("\n" + "=" * 50)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 50)
