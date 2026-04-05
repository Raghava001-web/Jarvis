"""
BATCH 1: Thorough Error Testing
================================
Testing: gesture_controller.py, pdf_handler.py, ws_channels.py
"""

import sys
import os
import asyncio
import traceback

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bugs_found = []
fixes_needed = []


def log(msg):
    print(f"[TEST] {msg}")


def bug(component, description, severity="MEDIUM"):
    bugs_found.append({"component": component, "desc": description, "severity": severity})
    print(f"[BUG-{severity}] {component}: {description}")


def passed(test_name):
    print(f"[OK] {test_name}")


print("\n" + "=" * 70)
print("BATCH 1: DEEP ERROR TESTING")
print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: gesture_controller.py
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 1: gesture_controller.py")
print("-" * 70)

try:
    from core.gesture_controller import (
        GestureController, GestureState, get_gesture_action, GESTURE_ACTIONS
    )
    passed("Imports work")
    
    # Test 1.1: GestureState class
    try:
        gs = GestureState()
        gs.update((0.5, 0.5), 0.1)  # Test update
        passed("GestureState.update() works")
        
        vel = gs.smoothed_velocity()
        if isinstance(vel, tuple) and len(vel) == 2:
            passed("GestureState.smoothed_velocity() returns tuple")
        else:
            bug("GestureState", f"smoothed_velocity returns {type(vel)}, expected tuple")
            
        pinch = gs.smoothed_pinch()
        if isinstance(pinch, (int, float)):
            passed("GestureState.smoothed_pinch() returns number")
        else:
            bug("GestureState", f"smoothed_pinch returns {type(pinch)}, expected number")
            
        gs.set_cooldown(10)
        can = gs.can_trigger()
        if isinstance(can, bool):
            passed("GestureState.can_trigger() returns bool")
        else:
            bug("GestureState", "can_trigger should return bool")
            
    except Exception as e:
        bug("GestureState", f"Error in methods: {e}", "HIGH")
    
    # Test 1.2: GestureController instantiation
    try:
        gc = GestureController()
        passed("GestureController instantiates")
        
        # Check required attributes
        for attr in ['active', 'hands', 'state', 'tracking_mode']:
            if hasattr(gc, attr):
                passed(f"GestureController has '{attr}' attribute")
            else:
                bug("GestureController", f"Missing attribute: {attr}", "HIGH")
        
        # Check required methods
        for method in ['detect', '_distance', '_is_open_palm', 'enable_tracking', 'disable_tracking']:
            if hasattr(gc, method):
                passed(f"GestureController has '{method}' method")
            else:
                bug("GestureController", f"Missing method: {method}", "MEDIUM")
                
    except Exception as e:
        bug("GestureController", f"Instantiation error: {e}", "HIGH")
    
    # Test 1.3: GESTURE_ACTIONS contexts
    expected_contexts = ['youtube', 'spotify', 'browser', 'globe', 'music', 'pdf', 'default']
    for ctx in expected_contexts:
        if ctx in GESTURE_ACTIONS:
            passed(f"Context '{ctx}' exists")
        else:
            bug("GESTURE_ACTIONS", f"Missing context: {ctx}", "MEDIUM")
    
    # Test 1.4: get_gesture_action for each context
    test_gestures = ['swipe_right', 'swipe_left', 'pinch', 'open_palm']
    for ctx in ['music', 'pdf', 'globe', 'default']:
        for gesture in test_gestures:
            action = get_gesture_action(gesture, ctx)
            if action is not None:
                passed(f"get_gesture_action('{gesture}', '{ctx}') = '{action}'")
            else:
                bug("get_gesture_action", f"No action for {gesture} in {ctx}", "LOW")
    
    # Test 1.5: Edge cases
    action = get_gesture_action("invalid_gesture", "default")
    if action is None:
        passed("Invalid gesture returns None (expected)")
    else:
        bug("get_gesture_action", "Invalid gesture should return None", "LOW")
        
    action = get_gesture_action("swipe_right", "nonexistent_context")
    if action is not None:
        passed("Falls back to default context")
    else:
        log("Note: No fallback for unknown context (not a bug)")
        
except ImportError as e:
    bug("gesture_controller", f"Import error: {e}", "CRITICAL")
except Exception as e:
    bug("gesture_controller", f"Unexpected error: {e}", "CRITICAL")
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: pdf_handler.py
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 2: pdf_handler.py")
print("-" * 70)

try:
    from core.pdf_handler import PDFHandler
    passed("PDFHandler imports")
    
    # Test 2.1: Instantiation
    pdf = PDFHandler()
    passed("PDFHandler instantiates")
    
    # Test 2.2: Required methods
    for method in ['extract_text', 'get_info', 'summarize', 'find_pdfs', '_get_title', '_speak']:
        if hasattr(pdf, method):
            passed(f"PDFHandler has '{method}' method")
        else:
            bug("PDFHandler", f"Missing method: {method}", "HIGH")
    
    # Test 2.3: extract_text with invalid path
    try:
        result = pdf.extract_text("nonexistent_file.pdf")
        if result == "":
            passed("extract_text handles missing file gracefully")
        else:
            bug("PDFHandler", "extract_text should return empty string for missing file", "MEDIUM")
    except Exception as e:
        bug("PDFHandler", f"extract_text crashes on missing file: {e}", "HIGH")
    
    # Test 2.4: extract_text with non-PDF
    try:
        result = pdf.extract_text(__file__)  # This Python file
        if result == "":
            passed("extract_text handles non-PDF gracefully")
        else:
            bug("PDFHandler", "extract_text should return empty for non-PDF", "MEDIUM")
    except Exception as e:
        bug("PDFHandler", f"extract_text crashes on non-PDF: {e}", "HIGH")
    
    # Test 2.5: get_info with invalid path
    try:
        info = pdf.get_info("nonexistent.pdf")
        if info == {}:
            passed("get_info handles missing file gracefully")
        else:
            bug("PDFHandler", "get_info should return empty dict for missing file", "MEDIUM")
    except Exception as e:
        bug("PDFHandler", f"get_info crashes on missing file: {e}", "HIGH")
    
    # Test 2.6: find_pdfs with valid directory
    try:
        pdfs = pdf.find_pdfs()  # Default = Documents folder
        if isinstance(pdfs, list):
            passed(f"find_pdfs returns list (found {len(pdfs)} PDFs)")
        else:
            bug("PDFHandler", "find_pdfs should return list", "MEDIUM")
    except Exception as e:
        bug("PDFHandler", f"find_pdfs crashes: {e}", "MEDIUM")
    
    # Test 2.7: find_pdfs with invalid directory
    try:
        pdfs = pdf.find_pdfs("C:\\nonexistent\\directory\\path")
        if pdfs == []:
            passed("find_pdfs handles invalid directory gracefully")
        else:
            bug("PDFHandler", "find_pdfs should return empty list for invalid dir", "LOW")
    except Exception as e:
        bug("PDFHandler", f"find_pdfs crashes on invalid dir: {e}", "MEDIUM")
        
except ImportError as e:
    bug("pdf_handler", f"Import error: {e}", "CRITICAL")
except Exception as e:
    bug("pdf_handler", f"Unexpected error: {e}", "CRITICAL")
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: ws_channels.py
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 3: ws_channels.py")
print("-" * 70)

try:
    from gui.ws_channels import (
        UI_CLIENTS, VOICE_CLIENTS, VISION_CLIENTS, COMMAND_CLIENTS,
        register, unregister, broadcast, send_to_ui, send_to_voice,
        ui_handler, voice_handler, vision_handler, command_handler,
        start_channels
    )
    passed("ws_channels imports all components")
    
    # Test 3.1: Client registries are sets
    for name, registry in [("UI", UI_CLIENTS), ("VOICE", VOICE_CLIENTS), 
                           ("VISION", VISION_CLIENTS), ("COMMAND", COMMAND_CLIENTS)]:
        if isinstance(registry, set):
            passed(f"{name}_CLIENTS is a set")
        else:
            bug("ws_channels", f"{name}_CLIENTS should be set, got {type(registry)}", "HIGH")
    
    # Test 3.2: Handlers are async functions
    import asyncio
    for name, handler in [("ui", ui_handler), ("voice", voice_handler),
                          ("vision", vision_handler), ("command", command_handler)]:
        if asyncio.iscoroutinefunction(handler):
            passed(f"{name}_handler is async function")
        else:
            bug("ws_channels", f"{name}_handler should be async", "HIGH")
    
    # Test 3.3: Broadcast function
    if asyncio.iscoroutinefunction(broadcast):
        passed("broadcast is async function")
    else:
        bug("ws_channels", "broadcast should be async", "HIGH")
    
    # Test 3.4: Register/unregister are async
    if asyncio.iscoroutinefunction(register):
        passed("register is async function")
    else:
        bug("ws_channels", "register should be async", "MEDIUM")
        
    if asyncio.iscoroutinefunction(unregister):
        passed("unregister is async function")
    else:
        bug("ws_channels", "unregister should be async", "MEDIUM")
    
    # Test 3.5: Check for websockets dependency
    try:
        import websockets
        passed("websockets library available")
    except ImportError:
        bug("ws_channels", "websockets library not installed", "CRITICAL")
        
except ImportError as e:
    bug("ws_channels", f"Import error: {e}", "CRITICAL")
except Exception as e:
    bug("ws_channels", f"Unexpected error: {e}", "CRITICAL")
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("BATCH 1 SUMMARY")
print("=" * 70)

critical = [b for b in bugs_found if b["severity"] == "CRITICAL"]
high = [b for b in bugs_found if b["severity"] == "HIGH"]
medium = [b for b in bugs_found if b["severity"] == "MEDIUM"]
low = [b for b in bugs_found if b["severity"] == "LOW"]

print(f"\nCRITICAL: {len(critical)}")
print(f"HIGH: {len(high)}")
print(f"MEDIUM: {len(medium)}")
print(f"LOW: {len(low)}")
print(f"TOTAL BUGS: {len(bugs_found)}")

if bugs_found:
    print("\nBUGS TO FIX:")
    for b in bugs_found:
        print(f"  [{b['severity']}] {b['component']}: {b['desc']}")
else:
    print("\nNo bugs found in Batch 1!")

print("\n" + "=" * 70)
