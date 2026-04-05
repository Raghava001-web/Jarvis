"""
JARVIS Phase 2 Stabilization Tests
===================================
Run this to validate:
1. Core commands work
2. Context resolution works (next in Spotify vs PDF)
3. Priority conflict resolution works
"""

import sys
from pathlib import Path
# Add parent jarvis folder to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_core_commands():
    """Test Set A: Core Commands"""
    print("\n" + "="*50)
    print("TEST SET A: Core Commands")
    print("="*50)
    
    from core.intent_classifier import classify_intent, ClassificationContext
    
    test_cases = [
        ("play music", "play_music"),
        ("next", None),  # Without context, "next" is ambiguous
        ("pause", "pause_music"),
        ("resume", "play_music"),  # resume → play_music
        ("open chrome", "open_app"),
        ("close chrome", "close_app"),
        ("what time is it", "time"),  # Uses "time" not "get_time"
        ("set alarm for 7 am", "set_alarm"),
        ("volume up", "volume"),  # Uses "volume" not "volume_up"
        ("volume down", "volume"),  # Uses "volume" not "volume_down"
    ]
    
    passed = 0
    failed = 0
    
    for command, expected in test_cases:
        intent, entities = classify_intent(command)
        if expected is None:
            # Ambiguous case - just check we get something
            status = "✓" if intent else "✗"
            passed += 1 if intent else 0
            failed += 0 if intent else 1
        else:
            status = "✓" if intent == expected else "✗"
            passed += 1 if intent == expected else 0
            failed += 0 if intent == expected else 1
        
        print(f"  {status} \"{command}\" → {intent} (expected: {expected})")
    
    print(f"\nResult: {passed}/{passed+failed} passed")
    return failed == 0


def test_context_resolution():
    """Test Set B: Context Resolution"""
    print("\n" + "="*50)
    print("TEST SET B: Context Resolution")
    print("="*50)
    
    from core.intent_classifier import classify_intent, ClassificationContext
    
    # Test "next" in Spotify context
    spotify_ctx = ClassificationContext(active_app="spotify")
    intent_spotify, _ = classify_intent("next", spotify_ctx)
    
    # Test "next" in PDF context
    pdf_ctx = ClassificationContext(active_app="pdf reader")
    intent_pdf, _ = classify_intent("next", pdf_ctx)
    
    # Test "play" in Spotify context
    intent_play_spotify, _ = classify_intent("play", spotify_ctx)
    
    # Test "pause" in Spotify context
    intent_pause_spotify, _ = classify_intent("pause", spotify_ctx)
    
    results = [
        ("next in Spotify", intent_spotify, "next_track"),
        ("next in PDF", intent_pdf, "next_page"),
        ("play in Spotify", intent_play_spotify, "play_music"),
        ("pause in Spotify", intent_pause_spotify, "pause_music"),
    ]
    
    passed = 0
    for desc, actual, expected in results:
        status = "✓" if actual == expected else "✗"
        print(f"  {status} \"{desc}\" → {actual} (expected: {expected})")
        passed += 1 if actual == expected else 0
    
    print(f"\nResult: {passed}/{len(results)} passed")
    return passed == len(results)


def test_priority_conflict():
    """Test Set C: Priority Conflict Resolution"""
    print("\n" + "="*50)
    print("TEST SET C: Priority Conflict Resolution")
    print("="*50)
    
    from core.input_priority import InputPriorityManager, PrioritizedInput, InputSource
    import time
    
    manager = InputPriorityManager()
    
    # Simulate simultaneous inputs
    t = time.time()
    manager.add(PrioritizedInput(source=InputSource.UI_BUTTON, text="click action", timestamp=t))
    manager.add(PrioritizedInput(source=InputSource.GESTURE, text="swipe action", timestamp=t))
    manager.add(PrioritizedInput(source=InputSource.VOICE, text="voice command", timestamp=t))
    
    winner = manager.get_winner()
    
    voice_wins = winner and winner.source == InputSource.VOICE
    print(f"  {'✓' if voice_wins else '✗'} Voice wins over Gesture and UI")
    print(f"    Winner: {winner.source.name if winner else 'None'} → \"{winner.text if winner else ''}\"")
    
    # Test emergency priority
    manager2 = InputPriorityManager()
    t2 = time.time()
    manager2.add(PrioritizedInput(source=InputSource.VOICE, text="play music", timestamp=t2))
    manager2.add(PrioritizedInput(source=InputSource.EMERGENCY, text="stop!", timestamp=t2))
    
    winner2 = manager2.get_winner()
    emergency_wins = winner2 and winner2.source == InputSource.EMERGENCY
    print(f"  {'✓' if emergency_wins else '✗'} Emergency wins over Voice")
    print(f"    Winner: {winner2.source.name if winner2 else 'None'} → \"{winner2.text if winner2 else ''}\"")
    
    passed = voice_wins and emergency_wins
    print(f"\nResult: {'2/2' if passed else 'FAILED'} passed")
    return passed


def test_session_logic():
    """Test Session Smart Pause Logic"""
    print("\n" + "="*50)
    print("TEST: Session Smart Pause Logic")
    print("="*50)
    
    from core.state_manager import Session
    
    test_cases = [
        # (detected_faces, primary_user, user_confidence, expected_pause)
        (1, None, 1.0, False),           # Single face - OK
        (2, None, 1.0, True),            # 2 faces, no primary - PAUSE
        (2, "Raghava", 0.8, False),      # 2 faces, primary, high conf - OK
        (2, "Raghava", 0.5, True),       # 2 faces, primary, low conf - PAUSE
        (0, None, 1.0, False),           # No faces - OK
    ]
    
    passed = 0
    for faces, primary, conf, expected in test_cases:
        session = Session(detected_faces=faces, primary_user=primary, user_confidence=conf)
        result = session.should_pause()
        status = "✓" if result == expected else "✗"
        print(f"  {status} faces={faces}, primary={primary}, conf={conf} → {'PAUSE' if result else 'OK'} (expected: {'PAUSE' if expected else 'OK'})")
        passed += 1 if result == expected else 0
    
    print(f"\nResult: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("JARVIS PHASE 2 STABILIZATION TESTS")
    print("="*60)
    
    results = []
    results.append(("Core Commands", test_core_commands()))
    results.append(("Context Resolution", test_context_resolution()))
    results.append(("Priority Conflict", test_priority_conflict()))
    results.append(("Session Logic", test_session_logic()))
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    for name, passed in results:
        print(f"  {'✓' if passed else '✗'} {name}")
    
    all_passed = all(r[1] for r in results)
    print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
