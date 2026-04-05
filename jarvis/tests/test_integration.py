"""
Phase 11: Full Feature-to-WebSocket Integration Test
=====================================================
Tests that EVERY feature handler is properly wired to the WebSocket
dispatch pipeline. Simulates actual command processing without network.
"""
import sys, os, asyncio, json, time
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
print("PHASE 11: FULL FEATURE-WEBSOCKET INTEGRATION TEST")
print("=" * 70)

# ============================================================
# SECTION 1: SERVER INITIALIZATION
# ============================================================
print("\n" + "=" * 70)
print("SECTION 1: SERVER INITIALIZATION")
print("=" * 70)

server = None
try:
    from jarvis.gui.websocket_server import JARVISWebSocketServer
    server = JARVISWebSocketServer()
    check("Server instantiated", server is not None)
except Exception as e:
    check("Server init", False, str(e))
    print("\nCANNOT CONTINUE WITHOUT SERVER. Exiting.")
    sys.exit(1)

# Check all subsystem initializations
subsystems = {
    'knowledge': 'Knowledge/AI Layer',
    'entertainment': 'Entertainment',
    'whatsapp_handler': 'WhatsApp',
    'email_handler': 'Email',
    'alarm_system': 'Alarm System',
    'reminder_manager': 'Reminder Manager',
    'system_control': 'System Control',
    'screenshot_handler': 'Screenshot',
    'ocr_handler': 'OCR',
    'dictionary_handler': 'Dictionary',
    'smart_notes': 'Smart Notes',
    'screen_control': 'Screen Control',
    'chat_history': 'Chat History',
    'context_memory': 'Context Memory',
    'proactive_assistant': 'Proactive Assistant',
    'state_manager': 'State Manager',
}

print("\n--- Subsystem Initialization ---")
for attr, name in subsystems.items():
    val = getattr(server, attr, None)
    check(f"{name} init", val is not None, f"({attr}={'OK' if val else 'NONE'})")

# ============================================================
# SECTION 2: DISPATCH INTEGRATION (process_command)
# ============================================================
print("\n" + "=" * 70)
print("SECTION 2: DISPATCH INTEGRATION (process_command)")
print("=" * 70)

# Create a mock websocket
class MockWebSocket:
    """Simulates websocket for testing"""
    def __init__(self):
        self.sent = []
        self.readyState = 1
    async def send(self, data):
        self.sent.append(json.loads(data))
    @property
    def open(self):
        return True

mock_ws = MockWebSocket()

async def test_command(command, expected_keywords=None, should_not_contain=None):
    """Test a command through the full dispatch pipeline"""
    mock_ws.sent.clear()
    try:
        response = await server.process_command(command, mock_ws)
        success = response is not None and isinstance(response, str) and len(response) > 0
        
        if expected_keywords and success:
            for kw in expected_keywords:
                if kw.lower() not in response.lower():
                    success = False
                    break
        
        if should_not_contain and success:
            for kw in should_not_contain:
                if kw.lower() in response.lower():
                    success = False
                    break
        
        detail = response[:60] if response else "EMPTY RESPONSE"
        return success, detail
    except Exception as e:
        return False, f"ERROR: {e}"

async def run_dispatch_tests():
    # --- TIME ---
    print("\n--- Time/Date ---")
    ok, d = await test_command("what time is it")
    check("Time command", ok, d)
    ok, d = await test_command("what is today's date")
    check("Date command", ok, d)
    
    # --- VOLUME ---
    print("\n--- System Control ---")
    ok, d = await test_command("increase volume")
    check("Volume up", ok, d)
    ok, d = await test_command("decrease brightness")
    check("Brightness down", ok, d)
    ok, d = await test_command("mute")
    check("Mute", ok, d)
    
    # --- ALARM ---
    print("\n--- Alarm ---")
    ok, d = await test_command("set alarm for 5 minutes")
    check("Set alarm", ok, d)
    ok, d = await test_command("list alarms")
    check("List alarms", ok, d)
    
    # --- REMINDER ---
    print("\n--- Reminder ---")
    ok, d = await test_command("remind me to drink water in 10 minutes")
    check("Set reminder", ok, d)
    
    # --- OPEN APP ---
    print("\n--- Open App ---")
    ok, d = await test_command("open calculator")
    check("Open calculator", ok, d)
    # Don't actually open apps in test, just check routing
    
    # --- ENTERTAINMENT ---
    print("\n--- Entertainment ---")
    ok, d = await test_command("tell me a joke")
    check("Tell joke", ok, d)
    ok, d = await test_command("recite a poem")
    check("Recite poem", ok, d)
    ok, d = await test_command("tell me a riddle")
    check("Tell riddle", ok, d)
    
    # --- DICTIONARY ---
    print("\n--- Dictionary ---")
    ok, d = await test_command("define ambiguous")
    check("Dictionary define", ok, d)
    
    # --- SCREENSHOT ---
    print("\n--- Screenshot ---")
    ok, d = await test_command("take a screenshot")
    check("Screenshot", ok, d)
    
    # --- OCR ---
    print("\n--- OCR ---")
    ok, d = await test_command("read screen")
    check("OCR read screen", ok, d)
    
    # --- CLIPBOARD ---
    print("\n--- Clipboard ---")
    ok, d = await test_command("read clipboard")
    check("Clipboard read", ok, d)
    
    # --- EMAIL ---
    print("\n--- Email ---")
    ok, d = await test_command("check my emails")
    check("Check emails", ok, d)
    
    # --- WHATSAPP ---
    print("\n--- WhatsApp ---")
    ok, d = await test_command("open whatsapp")
    check("Open WhatsApp", ok, d)
    
    # --- NOTES ---
    print("\n--- Smart Notes ---")
    ok, d = await test_command("create note about testing JARVIS")
    check("Create note", ok, d)
    ok, d = await test_command("list notes")
    check("List notes", ok, d)
    
    # --- WEATHER ---
    print("\n--- Weather ---")
    ok, d = await test_command("what's the weather")
    check("Weather", ok, d)
    
    # --- CHAT HISTORY ---
    print("\n--- Chat History ---")
    ok, d = await test_command("show chat history")
    check("Chat history", ok, d)
    
    # --- APP SWITCHING ---
    print("\n--- App Switching ---")
    ok, d = await test_command("go back")
    check("Alt-tab / go back", ok, d)
    
    # --- SEARCH ---
    print("\n--- Search ---")
    ok, d = await test_command("search for python tutorials")
    check("Web search", ok, d)
    
    # --- GREETING ---
    print("\n--- Conversational ---")
    ok, d = await test_command("hello jarvis")
    check("Greeting", ok, d)
    ok, d = await test_command("who are you")
    check("Identity", ok, d)
    ok, d = await test_command("who created you")
    check("Creator", ok, d)
    
    # --- SYSTEM INFO ---
    print("\n--- System Info ---")
    ok, d = await test_command("system status")
    check("System status", ok, d)
    
    # --- COMPOUND ---
    print("\n--- Compound Command ---")
    # Test the splitter integration
    cmds = server._split_compound_command("open notepad and set alarm for 5 minutes")
    check("Compound split", len(cmds) == 2, str(cmds))

# Run async tests
asyncio.run(run_dispatch_tests())

# ============================================================
# SECTION 3: SUMMARY
# ============================================================
print("\n" + "=" * 70)
print(f"RESULTS: {PASSED} passed, {FAILED} failed")
print("=" * 70)

if ERRORS:
    print("\nFAILED TESTS:")
    for e in ERRORS:
        print(f"  - {e}")
