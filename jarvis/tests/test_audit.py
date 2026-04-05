"""
JARVIS Module Audit - Systematic Testing
Tests each module individually with ACTUAL execution
"""
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

results = []

def test_result(name, passed, error=None):
    """Print test result"""
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
# PRIORITY 1: Core User-Facing Features
# =====================================================

header("PRIORITY 1: CORE USER-FACING FEATURES")

# ---------- Weather Handler ----------
print("\n[1] weather_handler.py")
try:
    from core.weather_handler import WeatherHandler
    wh = WeatherHandler()
    test_result("weather_handler: Init", True)
    # Try get_weather
    try:
        result = wh.get_weather("Mumbai")
        test_result("weather_handler: get_weather", result is not None)
    except Exception as e:
        test_result("weather_handler: get_weather", False, e)
except Exception as e:
    test_result("weather_handler", False, e)

# ---------- Music Handler ----------
print("\n[2] music_handler.py")
try:
    from core.music_handler import MusicHandler
    mh = MusicHandler()
    test_result("music_handler: Init", True)
    has_play = hasattr(mh, 'play')
    test_result("music_handler: has_play", has_play)
except Exception as e:
    test_result("music_handler", False, e)

# ---------- Alarm System ----------
print("\n[3] alarm_system.py")
try:
    from core.alarm_system import AlarmSystem
    als = AlarmSystem(perception=None)  # Pass None if optional
    test_result("alarm_system: Init", True)
    has_set = hasattr(als, 'set_alarm')
    test_result("alarm_system: has_set_alarm", has_set)
except Exception as e:
    test_result("alarm_system", False, e)

# ---------- Reminder Manager ----------
print("\n[4] reminder_manager.py")
try:
    from core.reminder_manager import ReminderManager
    rm = ReminderManager()
    test_result("reminder_manager: Init", True)
    has_set = hasattr(rm, 'set_reminder') or hasattr(rm, 'add_reminder')
    test_result("reminder_manager: has_set", has_set)
except Exception as e:
    test_result("reminder_manager", False, e)

# ---------- News Handler ----------
print("\n[5] news_handler.py")
try:
    from core.news_handler import NewsHandler
    nh = NewsHandler(perception=None)  # Pass None
    test_result("news_handler: Init", True)
    has_get = hasattr(nh, 'get_news') or hasattr(nh, 'fetch_news') or hasattr(nh, 'get_headlines')
    test_result("news_handler: has_get", has_get)
except Exception as e:
    test_result("news_handler", False, e)

# ---------- App Finder ----------
print("\n[6] app_finder.py")
try:
    from core.app_finder import AppFinder
    af = AppFinder()
    test_result("app_finder: Init", True)
    result = af.find_app("chrome")
    test_result("app_finder: find_app", result is not None)
except Exception as e:
    test_result("app_finder", False, e)

# ---------- System Control ----------
print("\n[7] system_control.py")
try:
    from core.system_control import SystemControl
    sc = SystemControl(perception=None)
    test_result("system_control: Init", True)
    test_result("system_control: volume", sc.volume_interface is not None)
except Exception as e:
    test_result("system_control", False, e)

# =====================================================
# PRIORITY 2: Communication
# =====================================================

header("PRIORITY 2: COMMUNICATION")

# ---------- WhatsApp Handler ----------
print("\n[8] whatsapp_handler.py")
try:
    from core.whatsapp_handler import WhatsAppHandler
    test_result("whatsapp_handler: Import", True)
except Exception as e:
    test_result("whatsapp_handler", False, e)

# ---------- Email Handler ----------
print("\n[9] email_handler.py")
try:
    from core.email_handler import EmailHandler
    test_result("email_handler: Import", True)
except Exception as e:
    test_result("email_handler", False, e)

# =====================================================
# PRIORITY 3: Entertainment
# =====================================================

header("PRIORITY 3: ENTERTAINMENT")

# ---------- Entertainment ----------
print("\n[10] entertainment.py")
try:
    from core.entertainment import EntertainmentEngine
    ee = EntertainmentEngine()
    test_result("entertainment: Init", True)
    has_joke = hasattr(ee, 'tell_joke') or hasattr(ee, 'get_joke')
    test_result("entertainment: has_joke", has_joke)
except Exception as e:
    test_result("entertainment", False, e)

# ---------- Dictionary Handler ----------
print("\n[11] dictionary_handler.py")
try:
    from core.dictionary_handler import DictionaryHandler
    dh = DictionaryHandler()
    test_result("dictionary_handler: Init", True)
except Exception as e:
    test_result("dictionary_handler", False, e)

# =====================================================
# PRIORITY 4: Utilities
# =====================================================

header("PRIORITY 4: UTILITIES")

# ---------- Screenshot Handler ----------
print("\n[12] screenshot_handler.py")
try:
    from core.screenshot_handler import ScreenshotHandler
    test_result("screenshot_handler: Import", True)
except Exception as e:
    test_result("screenshot_handler", False, e)

# ---------- OCR Handler ----------
print("\n[13] ocr_handler.py")
try:
    from core.ocr_handler import OCRHandler
    test_result("ocr_handler: Import", True)
except Exception as e:
    test_result("ocr_handler", False, e)

# =====================================================
# SUMMARY
# =====================================================

header("TEST SUMMARY")
passed = sum(1 for _, p in results if p)
failed = sum(1 for _, p in results if not p)
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Total: {len(results)}")

print("\nFailed tests:")
for name, p in results:
    if not p:
        print(f"  - {name}")
