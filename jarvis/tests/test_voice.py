"""
JARVIS Feature Test #1: Voice Recognition (PerceptionLayer)
Tests: Speech recognition (listen) and Text-to-Speech (speak)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("  JARVIS Feature Test #1: Voice Recognition")
print("=" * 60)
print()

try:
    from core.perception import PerceptionLayer
    print("[OK] PerceptionLayer imported successfully")
except ImportError as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Initialize perception layer
print("\n[1] Initializing PerceptionLayer...")
try:
    perception = PerceptionLayer()
    print("[OK] PerceptionLayer initialized")
    print(f"    Assistant: {perception.assistant_name}")
    print(f"    User title: {perception.user_title}")
except Exception as e:
    print(f"[FAIL] Init error: {e}")
    sys.exit(1)

# Test Text-to-Speech
print("\n[2] Testing Text-to-Speech (speak)...")
try:
    perception.speak("Hello sir, JARVIS voice system test initiated.")
    print("[OK] TTS working - you should have heard JARVIS speak")
except Exception as e:
    print(f"[FAIL] TTS error: {e}")

# Test voice switching
print("\n[3] Testing voice switching...")
try:
    print("    Switching to FRIDAY...")
    perception.switch_to_friday()
    perception.speak("FRIDAY online. Voice switching test successful, boss.")
    print("[OK] FRIDAY voice activated")
    
    print("    Switching back to JARVIS...")
    perception.switch_to_jarvis()
    perception.speak("JARVIS back online, sir.")
    print("[OK] JARVIS voice restored")
except Exception as e:
    print(f"[FAIL] Voice switch error: {e}")

# Test Speech Recognition
print("\n[4] Testing Speech Recognition (listen)...")
print("    Please say something when prompted...")
try:
    perception.speak("Sir, please say something for the speech recognition test.")
    
    # Listen for input
    result = perception.listen(timeout=10)
    
    if result:
        print(f"[OK] Heard: '{result}'")
        perception.speak(f"I heard you say: {result}")
    else:
        print("[!] No speech detected (timeout or error)")
        perception.speak("I didn't catch that, sir.")
except Exception as e:
    print(f"[FAIL] Listen error: {e}")

# Summary
print("\n" + "=" * 60)
print("  Test Complete - Voice Recognition")
print("=" * 60)
print("""
Results:
- TTS (speak): Check if you heard JARVIS speak
- Voice switch: Check if FRIDAY and JARVIS voices were different
- STT (listen): Check if your speech was recognized

If all worked, voice recognition is ready for HUD integration!
""")
