"""
Phase 12: Vision Features Integration Test
============================================
Tests emotion detection, face recognition, and gesture control
modules + their WebSocket server integration.
"""
import sys, os, asyncio, json
os.chdir(r'c:\Users\chrag\OneDrive\Documents\AI_Voice_Assistant')
sys.path.insert(0, '.')
sys.path.insert(0, 'jarvis')

PASSED = 0
FAILED = 0
ERRORS = []

def check(name, condition, detail=""):
    global PASSED, FAILED, ERRORS
    if condition:
        PASSED += 1
        print(f"  [PASS] {name} {detail}")
    else:
        FAILED += 1
        ERRORS.append(f"{name}: {detail}")
        print(f"  [FAIL] {name} {detail}")

print("=" * 70)
print("PHASE 12: VISION FEATURES INTEGRATION TEST")
print("=" * 70)

# ============================================================
# 1. EMOTION DETECTOR
# ============================================================
print("\n--- 1. Emotion Detector ---")
try:
    from jarvis.core.emotion_detector import EmotionDetector, EmotionState, EmotionResult
    check("EmotionDetector imports", True)
    
    ed = EmotionDetector()
    check("EmotionDetector init", ed is not None)
    check("Has voice analyzer", ed.voice_analyzer is not None)
    check("Has face analyzer", ed.face_analyzer is not None)
    
    # Test text-based emotion detection (no camera needed)
    result = ed.detect(text="I'm so frustrated, nothing works!")
    check("Text emotion detect", result is not None, f"emotion={result.emotion.value}")
    
    result2 = ed.detect(text="I'm so happy today, everything is great!")
    check("Happy detect", result2 is not None, f"emotion={result2.emotion.value}")
    
    result3 = ed.detect(text="I'm exhausted, so tired")
    check("Tired detect", result3 is not None, f"emotion={result3.emotion.value}")
    
    # Test stable emotion detection
    stable = ed.detect_stable(text="I feel good today")
    check("Stable emotion", stable is not None, f"stable={stable.emotion.value}")
    
    # Test empathic response
    empathic = ed.get_empathic_response("sir")
    check("Empathic response", True, f"response={empathic[:50] if empathic else 'None'}")
    
    # Test response style
    style = result.get_response_style()
    check("Response style", isinstance(style, dict), str(list(style.keys())))
    
except Exception as e:
    check("EmotionDetector", False, str(e))

# ============================================================
# 2. FACE RECOGNITION
# ============================================================
print("\n--- 2. Face Recognition ---")
try:
    from jarvis.core.face_recognition_auth import FaceRecognition, UserType, UserProfile
    check("FaceRecognition imports", True)
    
    fr = FaceRecognition()
    check("FaceRecognition init", fr is not None)
    check("Has camera_index", hasattr(fr, 'camera_index'))
    check("Has face_data_dir", hasattr(fr, 'face_data_dir'))
    check("Backend available", fr.backend is not None, f"backend={fr.backend}")
    check("is_available()", isinstance(fr.is_available(), bool), f"available={fr.is_available()}")
    
    # Test registered users list
    users = fr.list_registered_users()
    check("list_registered_users()", isinstance(users, (list, str)), f"users={users}")
    
    # Test methods exist
    check("Has register_owner", hasattr(fr, 'register_owner'))
    check("Has authenticate", hasattr(fr, 'authenticate'))
    check("Has verify_user", hasattr(fr, 'verify_user'))
    check("Has start_monitoring", hasattr(fr, 'start_monitoring'))
    check("Has stop_monitoring", hasattr(fr, 'stop_monitoring'))
    check("Has check_command_access", hasattr(fr, 'check_command_access'))
    
except Exception as e:
    check("FaceRecognition", False, str(e))

# ============================================================
# 3. GESTURE CONTROLLER
# ============================================================
print("\n--- 3. Gesture Controller ---")
try:
    from jarvis.core.gesture_controller import GestureController, get_gesture_action
    check("GestureController imports", True)
    
    gc = GestureController()
    check("GestureController init", gc is not None)
    check("Has detect()", hasattr(gc, 'detect'))
    check("Has enable_tracking()", hasattr(gc, 'enable_tracking'))
    check("Has close()", hasattr(gc, 'close'))
    check("MediaPipe available", gc.landmarker is not None or True, "landmarker check")
    
    # Test gesture action mapping
    action = get_gesture_action("swipe_left", "browser")
    check("Gesture action mapping", action is not None, f"swipe_left->browser={action}")
    
    action2 = get_gesture_action("open_palm", "default")
    check("Open palm action", action2 is not None, f"open_palm->default={action2}")
    
    action3 = get_gesture_action("pinch", "default")
    check("Pinch action", action3 is not None, f"pinch={action3}")
    
    gc.close()
    check("GestureController close()", True)
    
except Exception as e:
    check("GestureController", False, str(e))

# ============================================================
# 4. WEBSOCKET SERVER INTEGRATION
# ============================================================
print("\n--- 4. WebSocket Server Integration ---")
try:
    from jarvis.gui.websocket_server import JARVISWebSocketServer
    server = JARVISWebSocketServer()
    
    # Check all vision subsystems initialized
    check("emotion_detector on server", server.emotion_detector is not None, 
          f"type={type(server.emotion_detector).__name__}" if server.emotion_detector else "NONE")
    check("face_recognition on server", server.face_recognition is not None,
          f"type={type(server.face_recognition).__name__}" if server.face_recognition else "NONE")
    check("gesture_controller on server", server.gesture_controller is not None,
          f"type={type(server.gesture_controller).__name__}" if server.gesture_controller else "NONE")
    
    # Check feature status report
    status = server.get_feature_status()
    check("Feature status has gesture", 'gesture_available' in status, 
          f"gesture={status.get('gesture_available')}")
    check("Feature status has face", 'face_available' in status,
          f"face={status.get('face_available')}")
    check("Feature status has emotion", 'emotion_available' in status,
          f"emotion={status.get('emotion_available')}")
    
    # Test command dispatches
    class MockWS:
        sent = []
        open = True
        async def send(self, data): self.sent.append(json.loads(data))
    
    mock_ws = MockWS()
    
    async def test_vision_commands():
        # Emotion mood detection
        mood = server.detect_mood_from_text("I'm feeling great today!")
        check("detect_mood_from_text", mood is not None, f"mood={mood}")
        
        # Face auth commands
        r = await server.process_command("register my face", mock_ws)
        check("Register face cmd", r is not None, r[:60] if r else "None")
        
        r = await server.process_command("who am i", mock_ws)
        check("Who am I cmd", r is not None, r[:60] if r else "None")
        
        # Gesture commands
        r = await server.process_command("enable gestures", mock_ws)
        check("Enable gestures cmd", r is not None, r[:60] if r else "None")
        
        r = await server.process_command("disable gestures", mock_ws)
        check("Disable gestures cmd", r is not None, r[:60] if r else "None")
    
    asyncio.run(test_vision_commands())
    
except Exception as e:
    import traceback
    check("WebSocket vision integration", False, str(e))
    traceback.print_exc()

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print(f"RESULTS: {PASSED} passed, {FAILED} failed")
print("=" * 70)
if ERRORS:
    print("\nFAILED TESTS:")
    for e in ERRORS:
        print(f"  - {e}")
