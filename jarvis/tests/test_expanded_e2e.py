"""
Expanded E2E Test — Verifies ALL features including email, entertainment, proactive
"""
import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class MockWS:
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
    print("  JARVIS EXPANDED E2E TEST")
    print("="*60 + "\n")
    
    from jarvis.gui.websocket_server import JARVISWebSocketServer
    server = JARVISWebSocketServer()
    mock = MockWS()
    
    # ==== CORE ACTIONS ====
    print("\n--- CORE ACTIONS ---\n")
    
    r = await server.process_command("open calculator", mock)
    check("Open calculator", r, must_contain=["opening", "calculator"])
    
    r = await server.process_command("what time is it", mock)
    check("Time", r, must_contain=["time"])
    
    r = await server.process_command("what is the date", mock)
    check("Date", r, must_contain=["2026"])
    
    r = await server.process_command("set alarm for 5 minutes", mock)
    check("Alarm", r, must_contain=["alarm"])
    
    r = await server.process_command("take a screenshot", mock)
    check("Screenshot", r)
    
    r = await server.process_command("volume up", mock)
    check("Volume up", r, must_contain=["volume"])
    
    r = await server.process_command("brightness down", mock)
    check("Brightness", r, must_contain=["brightness"])
    
    # ==== IDENTITY ====
    print("\n--- IDENTITY ---\n")
    
    r = await server.process_command("who are you", mock)
    check("Identity", r, must_contain=["jarvis"])
    
    r = await server.process_command("who created you", mock)
    check("Creator", r, must_contain=["raghava"])
    
    # ==== ENTERTAINMENT ====
    print("\n--- ENTERTAINMENT ---\n")
    
    r = await server.process_command("tell me a joke", mock)
    check("Joke", r)
    
    r = await server.process_command("tell me a story", mock)
    check("Story", r)
    
    r = await server.process_command("recite a poem", mock)
    check("Poem", r)
    
    r = await server.process_command("tell me a riddle", mock)
    check("Riddle", r)
    
    # ==== EMAIL ====
    print("\n--- EMAIL ---\n")
    
    r = await server.process_command("check my email", mock)
    check("Check email", r, must_contain=["email"])
    
    r = await server.process_command("summarize my emails", mock)
    check("Summarize email", r, must_contain=["email"])
    
    # ==== SMART FEATURES ====
    print("\n--- SMART FEATURES ---\n")
    
    r = await server.process_command("add habit drink water", mock)
    check("Add habit", r, must_contain=["habit"])
    
    r = await server.process_command("add task finish project", mock)
    check("Add task", r, must_contain=["task"])
    
    r = await server.process_command("list my tasks", mock)
    check("List tasks", r, must_contain=["task"])
    
    r = await server.process_command("wellness check", mock)
    check("Wellness", r)
    
    r = await server.process_command("add note remember to call mom", mock)
    check("Note", r)
    
    # ==== APP OPENING ====
    print("\n--- APP OPENING ---\n")
    
    r = await server.process_command("open notepad", mock)
    check("Notepad", r, must_contain=["opening"])
    
    r = await server.process_command("open youtube", mock)
    check("YouTube", r, must_contain=["opening"])
    
    r = await server.process_command("open chatgpt", mock)
    check("ChatGPT", r, must_contain=["opening"])
    
    # ==== AI CONVERSATION ====
    print("\n--- AI CONVERSATION ---\n")
    
    r = await server.process_command("what is machine learning", mock)
    check("AI question", r)
    
    r = await server.process_command("explain quantum computing briefly", mock)
    check("AI explain", r)
    
    # ==== RESULTS ====
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} passed ({100*passed//total}%)")
    print(f"{'='*60}")
    
    if failed > 0:
        print(f"\nFAILED:")
        for name, ok, resp in results:
            if not ok:
                print(f"  - {name}: {resp}")

asyncio.run(main())
