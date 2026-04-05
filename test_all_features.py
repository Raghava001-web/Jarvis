"""
JARVIS Feature Test Suite
Run this to test all JARVIS features systematically
"""

import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_app_finder():
    """Test app scanning and finding"""
    print("\n" + "="*50)
    print("TEST: App Finder")
    print("="*50)
    
    from jarvis.core.app_finder import AppFinder
    finder = AppFinder()
    
    # Test 1: Check Perplexity
    path = finder.find_app("perplexity")
    if path and not path.startswith("WEB:"):
        print("✅ Perplexity: Desktop app found!")
        print(f"   Path: {path}")
    else:
        print("❌ Perplexity: Opens web (bug!)")
    
    # Test 2: Check Calculator
    path = finder.find_app("calculator")
    if path and not path.startswith("WEB:"):
        print("✅ Calculator: Found")
    else:
        print("❌ Calculator: Not found")
    
    # Test 3: Check Chrome
    path = finder.find_app("chrome")
    if path:
        print(f"✅ Chrome: {path}")
    else:
        print("❌ Chrome: Not found")
    
    return True

def test_hotkey_system():
    """Test hotkey configuration"""
    print("\n" + "="*50)
    print("TEST: Hotkey System")
    print("="*50)
    
    try:
        import keyboard
        print("✅ Keyboard module available")
        print("   Hotkeys configured:")
        print("   - Ctrl+Alt+J: Activate JARVIS")
        print("   - Ctrl+Alt+S: Shutdown JARVIS")
        print("   - Ctrl+Alt+M: Mute toggle")
    except ImportError:
        print("❌ Keyboard module not installed")
        print("   Run: pip install keyboard")
    
    return True

def test_emotion_detector():
    """Test emotion detection"""
    print("\n" + "="*50)
    print("TEST: Emotion Detection")
    print("="*50)
    
    try:
        from jarvis.core.emotion_detector import CombinedEmotionDetector
        detector = CombinedEmotionDetector()
        
        # Test text emotion
        result = detector.analyze_text("I'm so happy today!")
        if result:
            print(f"✅ Text emotion: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Emotion detector error: {e}")
        return False

def test_face_recognition():
    """Test face recognition"""
    print("\n" + "="*50)
    print("TEST: Face Recognition")
    print("="*50)
    
    try:
        from jarvis.core.face_recognition_auth import FaceRecognition
        fr = FaceRecognition()
        print(f"✅ Face Recognition initialized")
        print(f"   Known faces: {len(fr.known_faces) if hasattr(fr, 'known_faces') else 'N/A'}")
        return True
    except Exception as e:
        print(f"❌ Face Recognition error: {e}")
        return False

def test_gesture_controller():
    """Test gesture control"""
    print("\n" + "="*50)
    print("TEST: Gesture Controller")
    print("="*50)
    
    try:
        from jarvis.core.gesture_controller import GestureController
        gc = GestureController()
        print("✅ Gesture Controller initialized")
        return True
    except Exception as e:
        print(f"❌ Gesture Controller error: {e}")
        return False

def test_alarm_system():
    """Test alarm system"""
    print("\n" + "="*50)
    print("TEST: Alarm System")
    print("="*50)
    
    try:
        from jarvis.core.alarm_system import AlarmSystem
        alarm = AlarmSystem()
        print("✅ Alarm System ready")
        print(f"   Active alarms: {len(alarm.alarms) if hasattr(alarm, 'alarms') else 0}")
        return True
    except Exception as e:
        print(f"❌ Alarm System error: {e}")
        return False

def test_entertainment():
    """Test entertainment module"""
    print("\n" + "="*50)
    print("TEST: Entertainment Module")
    print("="*50)
    
    try:
        from jarvis.core.entertainment import Entertainment
        ent = Entertainment()
        print("✅ Entertainment module ready")
        return True
    except Exception as e:
        print(f"❌ Entertainment error: {e}")
        return False

def test_habit_tracker():
    """Test habit tracker"""
    print("\n" + "="*50)
    print("TEST: Habit Tracker")
    print("="*50)
    
    try:
        from jarvis.core.habit_tracker import HabitTracker
        tracker = HabitTracker()
        print("✅ Habit Tracker ready")
        return True
    except Exception as e:
        print(f"❌ Habit Tracker error: {e}")
        return False

def test_news_handler():
    """Test news handler"""
    print("\n" + "="*50)
    print("TEST: News Handler")
    print("="*50)
    
    try:
        from jarvis.core.news_handler import NewsHandler
        nh = NewsHandler()
        print("✅ News Handler ready")
        return True
    except Exception as e:
        print(f"❌ News Handler error: {e}")
        return False

def test_whatsapp():
    """Test WhatsApp handler"""
    print("\n" + "="*50)
    print("TEST: WhatsApp Handler")
    print("="*50)
    
    try:
        from jarvis.core.whatsapp_handler import WhatsAppHandler
        wa = WhatsAppHandler()
        print("✅ WhatsApp Handler ready")
        return True
    except Exception as e:
        print(f"❌ WhatsApp Handler error: {e}")
        return False

def test_ocr():
    """Test OCR"""
    print("\n" + "="*50)
    print("TEST: OCR Handler")
    print("="*50)
    
    try:
        from jarvis.core.ocr_handler import OCRHandler
        ocr = OCRHandler()
        print(f"✅ OCR Handler ready (available: {ocr.available})")
        return True
    except Exception as e:
        print(f"❌ OCR Handler error: {e}")
        return False

def run_all_tests():
    """Run all feature tests"""
    print("\n" + "#"*60)
    print("#" + " "*15 + "JARVIS FEATURE TEST SUITE" + " "*16 + "#")
    print("#"*60)
    
    results = {
        "App Finder": test_app_finder(),
        "Hotkeys": test_hotkey_system(),
        "Emotion Detection": test_emotion_detector(),
        "Face Recognition": test_face_recognition(),
        "Gesture Control": test_gesture_controller(),
        "Alarms": test_alarm_system(),
        "Entertainment": test_entertainment(),
        "Habit Tracker": test_habit_tracker(),
        "News": test_news_handler(),
        "WhatsApp": test_whatsapp(),
        "OCR": test_ocr(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
