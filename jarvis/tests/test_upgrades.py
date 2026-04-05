"""
JARVIS Upgrade Verification Tests
===================================
Run this to test all upgraded components
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

results = {"passed": [], "failed": [], "warnings": []}


def test(name, condition, warning=None):
    if condition:
        results["passed"].append(name)
        print(f"[PASS] {name}")
    else:
        if warning:
            results["warnings"].append(f"{name}: {warning}")
            print(f"[WARN] {name} - {warning}")
        else:
            results["failed"].append(name)
            print(f"[FAIL] {name}")


print("\n" + "=" * 60)
print("JARVIS UPGRADE VERIFICATION")
print("=" * 60 + "\n")


# ═══════════════════════════════════════════════════════════════
# TEST 1: Gesture Controller
# ═══════════════════════════════════════════════════════════════
print("\n--- GESTURE CONTROLLER ---")

try:
    from core.gesture_controller import GestureController, get_gesture_action, GESTURE_ACTIONS
    test("GestureController imports", True)
    
    # Test context mappings
    test("Music context exists", "music" in GESTURE_ACTIONS)
    test("PDF context exists", "pdf" in GESTURE_ACTIONS)
    test("Globe context exists", "globe" in GESTURE_ACTIONS)
    
    # Test gesture action mapping
    action = get_gesture_action("swipe_right", "music")
    test("Music swipe_right → next_track", action == "next_track")
    
    action = get_gesture_action("swipe_right", "pdf")
    test("PDF swipe_right → next_page", action == "next_page")
    
    # Test controller instantiation
    gc = GestureController()
    test("GestureController instantiates", gc is not None)
    test("Has detect method", hasattr(gc, 'detect'))
    
    # Check MediaPipe
    if gc.active:
        test("MediaPipe available", True)
    else:
        test("MediaPipe available", False, "MediaPipe not installed - gestures disabled")
        
except Exception as e:
    test("GestureController imports", False)
    print(f"   Error: {e}")


# ═══════════════════════════════════════════════════════════════
# TEST 2: Emotion State Machine
# ═══════════════════════════════════════════════════════════════
print("\n--- EMOTION STATE MACHINE ---")

try:
    from gui.websocket_server import EmotionState, EmotionStateMachine
    test("EmotionStateMachine imports", True)
    
    # Test states
    test("NEUTRAL state exists", EmotionState.NEUTRAL is not None)
    test("HAPPY state exists", EmotionState.HAPPY is not None)
    test("FRUSTRATED state exists", EmotionState.FRUSTRATED is not None)
    
    # Test machine
    esm = EmotionStateMachine()
    test("EmotionStateMachine instantiates", esm is not None)
    test("Initial state is NEUTRAL", esm.state == EmotionState.NEUTRAL)
    
    # Test transitions
    esm.trigger("polite")
    test("Polite → HAPPY", esm.state == EmotionState.HAPPY)
    
    esm = EmotionStateMachine()  # Reset
    esm.trigger("complex_task")
    test("Complex task → FOCUSED", esm.state == EmotionState.FOCUSED)
    
    # Test orb color
    color = esm.get_orb_color()
    test("Orb color exists", color is not None and len(color) > 0)
    
except Exception as e:
    test("EmotionStateMachine imports", False)
    print(f"   Error: {e}")


# ═══════════════════════════════════════════════════════════════
# TEST 3: PDF Handler
# ═══════════════════════════════════════════════════════════════
print("\n--- PDF HANDLER ---")

try:
    from core.pdf_handler import PDFHandler
    test("PDFHandler imports", True)
    
    pdf = PDFHandler()
    test("PDFHandler instantiates", pdf is not None)
    test("Has extract_text method", hasattr(pdf, 'extract_text'))
    test("Has summarize method", hasattr(pdf, 'summarize'))
    test("Has find_pdfs method", hasattr(pdf, 'find_pdfs'))
    
    # Check dependencies
    if pdf.pypdf_available:
        test("PyPDF2 available", True)
    else:
        test("PyPDF2 available", False, "pip install PyPDF2")
        
    if pdf.pdfplumber_available:
        test("pdfplumber available", True)
    else:
        test("pdfplumber available", False, "pip install pdfplumber (optional)")
        
except Exception as e:
    test("PDFHandler imports", False)
    print(f"   Error: {e}")


# ═══════════════════════════════════════════════════════════════
# TEST 4: WebSocket Channels
# ═══════════════════════════════════════════════════════════════
print("\n--- 4-CHANNEL WEBSOCKET ---")

try:
    from gui.ws_channels import (
        ui_handler, voice_handler, vision_handler, command_handler,
        UI_CLIENTS, VOICE_CLIENTS, VISION_CLIENTS, COMMAND_CLIENTS,
        send_to_ui, send_to_voice
    )
    test("ws_channels imports", True)
    test("ui_handler exists", ui_handler is not None)
    test("voice_handler exists", voice_handler is not None)
    test("vision_handler exists", vision_handler is not None)
    test("command_handler exists", command_handler is not None)
    test("send_to_ui helper exists", send_to_ui is not None)
    
except Exception as e:
    test("ws_channels imports", False)
    print(f"   Error: {e}")

# Check websockets library
try:
    import websockets
    test("websockets library available", True)
except ImportError:
    test("websockets library available", False, "pip install websockets")


# ═══════════════════════════════════════════════════════════════
# TEST 5: Entertainment (existing)
# ═══════════════════════════════════════════════════════════════
print("\n--- ENTERTAINMENT (EXISTING) ---")

try:
    from core.entertainment import JARVISEntertainment
    test("JARVISEntertainment imports", True)
    
    ent = JARVISEntertainment()
    test("Has tell_story method", hasattr(ent, 'tell_story'))
    test("Has tell_joke method", hasattr(ent, 'tell_joke'))
    
except Exception as e:
    test("JARVISEntertainment imports", False)
    print(f"   Error: {e}")


# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("VERIFICATION SUMMARY")
print("=" * 60)
print(f"\nPASSED: {len(results['passed'])}")
print(f"WARNINGS: {len(results['warnings'])}")
print(f"FAILED: {len(results['failed'])}")

if results["warnings"]:
    print("\nWARNINGS:")
    for w in results["warnings"]:
        print(f"   - {w}")

if results["failed"]:
    print("\nFAILED:")
    for f in results["failed"]:
        print(f"   - {f}")
else:
    print("\nAll core components working!")

print("\n" + "=" * 60)
