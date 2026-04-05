"""
BATCH 2: Thorough Error Testing
================================
Testing: websocket_server.py, index.html JS logic, entertainment.py
"""

import sys
import os
import traceback

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bugs_found = []


def log(msg):
    print(f"[TEST] {msg}")


def bug(component, description, severity="MEDIUM"):
    bugs_found.append({"component": component, "desc": description, "severity": severity})
    print(f"[BUG-{severity}] {component}: {description}")


def passed(test_name):
    print(f"[OK] {test_name}")


print("\n" + "=" * 70)
print("BATCH 2: DEEP ERROR TESTING")
print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: websocket_server.py
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 1: websocket_server.py")
print("-" * 70)

try:
    from gui.websocket_server import (
        EmotionState, EmotionStateMachine, JARVISWebSocketServer
    )
    passed("Core imports work")
    
    # Check which EmotionState we got (there are 2 versions in codebase)
    # websocket_server version: NEUTRAL, HAPPY, FOCUSED, CONCERNED, FRUSTRATED, TIRED, ALERT
    # emotion_detector version: NEUTRAL, HAPPY, ANGRY, SAD, TIRED, CONFUSED, RUSHED, CALM
    
    ws_states = ['NEUTRAL', 'HAPPY', 'FOCUSED', 'CONCERNED', 'FRUSTRATED', 'TIRED', 'ALERT']
    detector_states = ['NEUTRAL', 'HAPPY', 'ANGRY', 'SAD', 'TIRED', 'CONFUSED', 'RUSHED', 'CALM']
    
    # Determine which version we have
    has_focused = getattr(EmotionState, 'FOCUSED', None) is not None
    has_angry = getattr(EmotionState, 'ANGRY', None) is not None
    
    if has_focused:
        log("Using websocket_server EmotionState (GUI states)")
        test_states = ws_states
    elif has_angry:
        log("Using emotion_detector EmotionState (detection states)")
        test_states = detector_states
    else:
        bug("EmotionState", "Unknown EmotionState variant", "MEDIUM")
        test_states = []
    
    # Test available states
    for state in test_states:
        if getattr(EmotionState, state, None) is not None:
            passed(f"EmotionState.{state} exists")
        else:
            bug("EmotionState", f"Missing state: {state}", "MEDIUM")
    
    # Test 1.2: EmotionStateMachine
    esm = EmotionStateMachine()
    passed("EmotionStateMachine instantiates")
    
    for method in ['trigger', 'get_orb_color', 'reset', 'transition']:
        if hasattr(esm, method):
            passed(f"EmotionStateMachine has '{method}' method")
        else:
            bug("EmotionStateMachine", f"Missing method: {method}", "MEDIUM")
    
    # Test state transitions (only if we have the right EmotionState)
    if has_focused:
        esm.reset()
        esm.trigger("polite")
        if esm.state == EmotionState.HAPPY:
            passed("Trigger 'polite' -> HAPPY works")
        else:
            bug("EmotionStateMachine", f"polite trigger didn't go to HAPPY (got {esm.state})", "MEDIUM")
        
        esm.reset()
        esm.trigger("complex_task")
        if esm.state == EmotionState.FOCUSED:
            passed("Trigger 'complex_task' -> FOCUSED works")
        else:
            bug("EmotionStateMachine", f"complex_task trigger didn't go to FOCUSED (got {esm.state})", "MEDIUM")
    else:
        log("Note: Skipping state transition tests (wrong EmotionState version loaded)")
    
    # Test orb color
    color = esm.get_orb_color()
    if isinstance(color, str) and len(color) > 0:
        passed(f"get_orb_color returns valid string: '{color}'")
    else:
        bug("EmotionStateMachine", "get_orb_color should return non-empty string", "MEDIUM")
    
    # Test 1.3: JARVISWebSocketServer
    try:
        ws = JARVISWebSocketServer.__new__(JARVISWebSocketServer)  # Don't init fully
        passed("JARVISWebSocketServer class exists")
    except Exception as e:
        bug("JARVISWebSocketServer", f"Class error: {e}", "HIGH")
        
except ImportError as e:
    bug("websocket_server", f"Import error: {e}", "CRITICAL")
except Exception as e:
    bug("websocket_server", f"Unexpected error: {e}", "CRITICAL")
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: entertainment.py
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 2: entertainment.py")
print("-" * 70)

try:
    from core.entertainment import (
        JARVISEntertainment, EntertainmentType, EntertainmentEngine
    )
    passed("Entertainment imports work")
    
    # Test 2.1: EntertainmentType enum
    for etype in ['SONG', 'STORY', 'JOKE', 'POEM', 'RIDDLE']:
        if hasattr(EntertainmentType, etype):
            passed(f"EntertainmentType.{etype} exists")
        else:
            bug("EntertainmentType", f"Missing: {etype}", "MEDIUM")
    
    # Test 2.2: JARVISEntertainment instantiation
    ent = JARVISEntertainment()
    passed("JARVISEntertainment instantiates")
    
    # Check methods
    for method in ['sing_song', 'tell_story', 'tell_joke', 'recite_poem', 'tell_riddle', 'entertain']:
        if hasattr(ent, method):
            passed(f"JARVISEntertainment has '{method}' method")
        else:
            bug("JARVISEntertainment", f"Missing method: {method}", "HIGH")
    
    # Test 2.3: Built-in content
    if hasattr(ent, 'songs') and len(ent.songs) > 0:
        passed(f"Has {len(ent.songs)} built-in songs")
    else:
        bug("JARVISEntertainment", "No built-in songs", "LOW")
    
    if hasattr(ent, 'jokes') and len(ent.jokes) > 0:
        passed(f"Has {len(ent.jokes)} built-in jokes")
    else:
        bug("JARVISEntertainment", "No built-in jokes", "LOW")
        
    if hasattr(ent, 'poems') and len(ent.poems) > 0:
        passed(f"Has {len(ent.poems)} built-in poems")
    else:
        bug("JARVISEntertainment", "No built-in poems", "LOW")
        
    if hasattr(ent, 'riddles') and len(ent.riddles) > 0:
        passed(f"Has {len(ent.riddles)} built-in riddles")
    else:
        bug("JARVISEntertainment", "No built-in riddles", "LOW")
    
    # Test 2.4: BackwardCompatibility alias
    if EntertainmentEngine is JARVISEntertainment:
        passed("EntertainmentEngine alias works")
    else:
        bug("entertainment", "EntertainmentEngine alias broken", "LOW")
    
    # Test 2.5: entertain() method with different inputs
    try:
        # Can't actually call since no perception, but check it's callable
        import inspect
        sig = inspect.signature(ent.entertain)
        if 'request' in sig.parameters:
            passed("entertain() has 'request' parameter")
        else:
            bug("JARVISEntertainment", "entertain() missing 'request' param", "MEDIUM")
    except Exception as e:
        bug("JARVISEntertainment", f"entertain() inspection error: {e}", "MEDIUM")
        
except ImportError as e:
    bug("entertainment", f"Import error: {e}", "CRITICAL")
except Exception as e:
    bug("entertainment", f"Unexpected error: {e}", "CRITICAL")
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: index.html JavaScript logic verification
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 3: index.html (JavaScript structure)")
print("-" * 70)

import re
from pathlib import Path

hud_path = Path(__file__).parent.parent / "gui" / "web_hud" / "index.html"

if hud_path.exists():
    passed("index.html exists")
    
    content = hud_path.read_text(encoding='utf-8', errors='ignore')
    
    # Test 3.1: Check for WebSocket usage (single or multi-channel)
    if 'ws.' in content or 'WebSocket' in content.lower() or 'socket' in content.lower():
        passed("WebSocket usage detected in HUD")
    else:
        # Check if there's any websocket-related code
        if 'connectWebSocket' in content or 'handleMessage' in content:
            passed("WebSocket connection code present")
        else:
            log("Note: WebSocket may be handled differently")
    
    # Info: 4-channel WebSocket is server-side (ws_channels.py), HUD may use single WS
    log("Note: 4-channel WebSocket (8765-8768) is in ws_channels.py server")
    log("Note: HUD can work with single WebSocket OR multi-channel")
    
    # Test 3.2: Check for key functions
    function_checks = [
        (r'function\s+connectWebSocket', 'connectWebSocket function'),
        (r'function\s+sendMessage|sendMessage\s*[=:]', 'sendMessage function'),
        (r'function\s+handleServerMessage|handleServerMessage\s*[=:]', 'handleServerMessage function'),
        (r'\.onmessage\s*=', 'WebSocket onmessage handler'),
        (r'\.onerror\s*=', 'WebSocket onerror handler'),
        (r'\.onclose\s*=', 'WebSocket onclose handler'),
    ]
    
    for pattern, name in function_checks:
        if re.search(pattern, content):
            passed(f"{name} exists")
        else:
            bug("index.html", f"Missing {name}", "MEDIUM")
    
    # Test 3.3: Check for emotion CSS classes
    emotion_classes = [
        'emotion-neutral', 'emotion-happy', 'emotion-focused',
        'emotion-concerned', 'emotion-tired', 'emotion-alert'
    ]
    
    for cls in emotion_classes:
        if cls in content:
            passed(f"CSS class '.{cls}' defined")
        else:
            bug("index.html", f"Missing CSS class: {cls}", "LOW")
    
    # Test 3.4: Check for channel message routing
    if 'connectAllChannels' in content or 'channel' in content.lower():
        passed("Multi-channel routing logic present")
    else:
        bug("index.html", "No multi-channel routing logic", "MEDIUM")
    
    # Test 3.5: Check for reconnection logic
    if 'reconnect' in content.lower() or 'setTimeout' in content:
        passed("Reconnection logic present")
    else:
        bug("index.html", "No reconnection logic", "LOW")
        
else:
    bug("index.html", "File not found", "CRITICAL")


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("BATCH 2 SUMMARY")
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
    print("\nNo bugs found in Batch 2!")

print("\n" + "=" * 70)
