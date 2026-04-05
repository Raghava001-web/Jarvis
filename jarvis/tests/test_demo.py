"""
JARVIS Phase 4A: Live Demo Test Script
======================================
Tests all demo commands without actually executing actions.
Verifies intent classification and handler routing.
"""

import sys
sys.path.insert(0, '.')

from core.understanding import UnderstandingLayer

def test_intent(text, expected_intent, description=""):
    """Test intent classification"""
    understanding = UnderstandingLayer()
    intent, confidence = understanding.classify(text)
    
    passed = intent == expected_intent or expected_intent in str(intent).lower()
    status = "✅" if passed else "❌"
    
    print(f"{status} {description or text}")
    print(f"   Expected: {expected_intent}, Got: {intent} ({confidence:.2f})")
    return passed

def run_demo_tests():
    print("\n" + "="*60)
    print("         JARVIS LIVE DEMO TEST SCRIPT")
    print("="*60 + "\n")
    
    results = []
    
    # ========== A. VOICE CORE ==========
    print("A. VOICE CORE")
    print("-" * 40)
    results.append(test_intent("play music", "play_music", "Play music"))
    results.append(test_intent("next", "next_track", "Next track"))
    results.append(test_intent("pause", "pause_music", "Pause"))
    results.append(test_intent("resume", "play_music", "Resume"))
    print()
    
    # ========== B. CONTEXT COMMANDS ==========
    print("B. CONTEXT / APP COMMANDS")
    print("-" * 40)
    results.append(test_intent("open chrome", "open_app", "Open Chrome"))
    results.append(test_intent("close chrome", "close_app", "Close Chrome"))
    results.append(test_intent("switch to spotify", "open_app", "Switch to Spotify"))
    print()
    
    # ========== C. OCR + SCREEN ==========
    print("C. OCR + SCREEN")
    print("-" * 40)
    results.append(test_intent("take a screenshot", "screenshot", "Take screenshot"))
    results.append(test_intent("read my screen", "ocr", "Read screen (OCR)"))
    results.append(test_intent("summarize this pdf", "summarize", "Summarize PDF"))
    print()
    
    # ========== D. SYSTEM CONTROL ==========
    print("D. SYSTEM CONTROL")
    print("-" * 40)
    results.append(test_intent("minimize window", "system", "Minimize window"))
    results.append(test_intent("scroll down", "system", "Scroll down"))
    results.append(test_intent("volume up", "volume_up", "Volume up"))
    print()
    
    # ========== E. ENTERTAINMENT ==========
    print("E. ENTERTAINMENT")
    print("-" * 40)
    results.append(test_intent("tell me a horror story", "story", "Horror story"))
    results.append(test_intent("tell me a joke", "joke", "Tell joke"))
    print()
    
    # ========== SUMMARY ==========
    passed = sum(results)
    total = len(results)
    
    print("="*60)
    print(f"        RESULTS: {passed}/{total} PASSED")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL DEMO COMMANDS WORKING!")
    else:
        print(f"\n⚠️  {total - passed} commands need attention")
    
    return passed, total

if __name__ == "__main__":
    run_demo_tests()
