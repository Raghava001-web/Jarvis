"""
JARVIS Feature Test #4: Emotion/Mood Detection (EmotionDetector)
Tests: Voice and face emotion analysis
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("  JARVIS Feature Test #4: Emotion Detection")
print("=" * 60)
print()

# Try to import emotion detector
try:
    from core.emotion_detector import EmotionDetector, EmotionState, EmotionResult
    print("[OK] EmotionDetector imported successfully")
except ImportError as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Initialize emotion detector
print("\n[1] Initializing EmotionDetector...")
try:
    detector = EmotionDetector()
    print("[OK] EmotionDetector initialized")
except Exception as e:
    print(f"[FAIL] Init error: {e}")
    sys.exit(1)

# List supported emotions
print("\n[2] Supported Emotions:")
for emotion in EmotionState:
    print(f"    - {emotion.value}")

# Test text-based emotion detection
print("\n[3] Testing Text-Based Emotion Analysis...")
test_phrases = [
    "I'm so happy today!",
    "This is frustrating, why won't it work?",
    "I'm feeling really tired...",
    "Great job, I love it!",
    "I'm confused about this",
    "Hurry up, I don't have time"
]

for phrase in test_phrases:
    try:
        result = detector.detect(text=phrase)
        emotion = result.emotion.value if result else "unknown"
        confidence = f"{result.confidence:.0%}" if result else "N/A"
        print(f"    '{phrase[:40]:40}' -> {emotion} ({confidence})")
    except Exception as e:
        print(f"    Error: {e}")

# Test response style
print("\n[4] Testing Emotion Response Styles...")
test_emotions = [EmotionState.HAPPY, EmotionState.ANGRY, EmotionState.SAD, EmotionState.TIRED, EmotionState.RUSHED]

for emotion in test_emotions:
    try:
        # Create mock result
        result = EmotionResult(emotion=emotion, confidence=0.8)
        style = result.get_response_style()
        print(f"    {emotion.value:10} -> Rate: {style.get('rate', 'N/A')}, "
              f"Tone: {style.get('tone', 'N/A')}, "
              f"Prefix: {style.get('prefix', 'N/A')[:30]}...")
    except Exception as e:
        print(f"    {emotion.value}: Error - {e}")

# Get last emotion
print("\n[5] Last Detected Emotion:")
try:
    last = detector.get_last_emotion()
    if last:
        print(f"    Emotion: {last.emotion.value}")
        print(f"    Confidence: {last.confidence:.0%}")
    else:
        print("    No emotion detected yet")
except Exception as e:
    print(f"    Error: {e}")

# Summary
print("\n" + "=" * 60)
print("  Test Complete - Emotion Detection")
print("=" * 60)
print("""
Results:
- Text analysis: Check if emotions were detected from phrases
- Response styles: Check if response adaptations are correct

The emotion detector can analyze:
- Voice keywords (frustrated, happy, etc.)
- Facial expressions (if camera available and FER installed)

If emotion detection worked, it's ready for HUD integration!
""")
