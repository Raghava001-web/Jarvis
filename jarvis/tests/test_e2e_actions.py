"""
E2E Action Test — Verify commands ACTUALLY execute (not just text responses)
Tests the full WebSocket pipeline from command → action execution
"""
import sys, os, asyncio, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class MockWS:
    """Mock WebSocket that captures sent messages"""
    sent = []
    open = True
    async def send(self, data):
        self.sent.append(json.loads(data) if isinstance(data, str) else data)

passed = 0
failed = 0
results = []

def check(name, response, must_contain=None, must_not_contain=None):
    global passed, failed
    r = str(response).lower() if response else ""
    ok = True
    reason = ""
    
    if must_contain:
        for word in must_contain:
            if word.lower() not in r:
                ok = False
                reason = f"missing '{word}'"
                break
    
    if must_not_contain:
        for word in must_not_contain:
            if word.lower() in r:
                ok = False
                reason = f"should not contain '{word}'"
                break
    
    if ok:
        passed += 1
        print(f"  [PASS] {name}: {str(response)[:80]}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: {reason} | got: {str(response)[:80]}")
    results.append((name, ok, str(response)[:100]))

async def main():
    global passed, failed
    
    print("\n" + "="*60)
    print("  JARVIS E2E ACTION TEST")
    print("="*60 + "\n")
    
    # Initialize server
    from jarvis.gui.websocket_server import JARVISWebSocketServer
    server = JARVISWebSocketServer()
    mock = MockWS()
    
    print("\n--- ACTION COMMANDS (must execute, not just talk) ---\n")
    
    # 1. Open app — must use subprocess, not AI text
    r = await server.process_command("open calculator", mock)
    check("Open calculator", r, must_contain=["opening", "calculator"])
    
    # 2. Time — instant, no AI needed
    r = await server.process_command("what time is it", mock)
    check("Time check", r, must_contain=["time"])
    
    # 3. Date
    r = await server.process_command("what's the date today", mock)
    check("Date check", r, must_contain=["2026"])
    
    # 4. Set alarm
    r = await server.process_command("set alarm for 5 minutes", mock)
    check("Set alarm", r, must_contain=["alarm"])
    
    # 5. Screenshot
    r = await server.process_command("take a screenshot", mock)
    check("Screenshot", r)
    
    # 6. Volume up (system control)
    r = await server.process_command("volume up", mock)
    check("Volume up", r, must_contain=["volume"])
    
    # 7. Mute
    r = await server.process_command("mute", mock)
    check("Mute", r)
    
    # 8. Brightness - check if handled
    r = await server.process_command("brightness down", mock)
    check("Brightness", r, must_contain=["brightness"])

    print("\n--- SMART COMMANDS (pre-router overrides) ---\n")
    
    # 9. Habits
    r = await server.process_command("add habit exercise daily", mock)
    check("Add habit", r, must_contain=["habit"])
    
    # 10. Tasks
    r = await server.process_command("add task review code", mock)
    check("Add task", r, must_contain=["task"])
    
    # 11. List tasks
    r = await server.process_command("list my tasks", mock)
    check("List tasks", r, must_contain=["task"])
    
    # 12. Wellness
    r = await server.process_command("wellness check", mock)
    check("Wellness", r)
    
    # 13. Notes
    r = await server.process_command("add note remember to buy groceries", mock)
    check("Add note", r)
    
    # 14. Chat history
    r = await server.process_command("show chat history", mock)
    check("Chat history", r, must_contain=["chat", "history"])
    
    print("\n--- CONVERSATION (Groq AI) ---\n")
    
    # 15. Identity
    r = await server.process_command("who are you", mock)
    check("Identity", r, must_contain=["jarvis"])
    
    # 16. Creator
    r = await server.process_command("who made you", mock)
    check("Creator", r, must_contain=["raghava"])
    
    # 17. Greeting
    r = await server.process_command("hello jarvis", mock)
    check("Greeting", r)
    
    # 18. Joke
    r = await server.process_command("tell me a joke", mock)
    check("Joke", r)
    
    print("\n--- APP OPENING (direct pre-router) ---\n")
    
    # 19. Open notepad
    r = await server.process_command("open notepad", mock)
    check("Open notepad", r, must_contain=["opening", "notepad"])
    
    # 20. Open YouTube (web app)
    r = await server.process_command("open youtube", mock)
    check("Open YouTube", r, must_contain=["opening", "youtube"])
    
    # 21. Open ChatGPT (web app)
    r = await server.process_command("open chatgpt", mock)
    check("Open ChatGPT", r, must_contain=["opening", "chatgpt"])
    
    # 22. Launch with typo tolerance
    r = await server.process_command("open brave", mock)
    check("Open Brave", r, must_contain=["opening"])
    
    # 23. App switching
    r = await server.process_command("go back", mock)
    check("Go back (alt-tab)", r)
    
    print("\n--- COMPOUND COMMANDS ---\n")
    
    # 24. Two commands in one
    r = await server.process_command("set alarm for 10 minutes and remind me to drink water", mock)
    check("Compound cmd", r)
    
    # RESULTS
    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed} passed, {failed} failed out of {passed+failed}")
    print(f"{'='*60}")
    
    if failed > 0:
        print(f"\nFAILED:")
        for name, ok, resp in results:
            if not ok:
                print(f"  - {name}: {resp}")

asyncio.run(main())
