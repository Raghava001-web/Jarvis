"""
Phase 17 E2E Test — YouTube, News, Music, Face Auth, Emotion
Tests all remaining features
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

def check(name, response, must_contain=None):
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
    if not response:
        ok = False
        reason = "no response"
    if ok:
        passed += 1
        print(f"  [PASS] {name}: {str(response)[:90]}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: {reason} | got: {str(response)[:90]}")
    results.append((name, ok, str(response)[:100]))

async def main():
    global passed, failed
    print("\n" + "="*60)
    print("  JARVIS PHASE 17 E2E TEST")
    print("="*60 + "\n")
    
    from jarvis.gui.websocket_server import JARVISWebSocketServer
    server = JARVISWebSocketServer()
    mock = MockWS()
    
    # ==== PREVIOUS PASSING (quick sanity) ====
    print("\n--- SANITY CHECK ---\n")
    
    r = await server.process_command("open calculator", mock)
    check("Calculator", r, ["opening"])
    
    r = await server.process_command("what time is it", mock)
    check("Time", r, ["time"])
    
    r = await server.process_command("who are you", mock)
    check("Identity", r, ["jarvis"])
    
    r = await server.process_command("show my chat history", mock)
    check("Chat history", r, ["chat"])
    
    # ==== NEWS ====
    print("\n--- NEWS ---\n")
    
    r = await server.process_command("tell me the latest news", mock)
    check("News general", r)
    
    r = await server.process_command("technology news", mock)
    check("Tech news", r)
    
    r = await server.process_command("sports news", mock)
    check("Sports news", r)
    
    # ==== WEATHER ====
    print("\n--- WEATHER ---\n")
    
    r = await server.process_command("what's the weather", mock)
    check("Weather", r)
    
    # ==== MUSIC ====
    print("\n--- MUSIC ---\n")
    
    r = await server.process_command("play music", mock)
    check("Play music", r)
    
    r = await server.process_command("pause music", mock)
    check("Pause", r)
    
    r = await server.process_command("next song", mock)
    check("Next", r)
    
    # ==== YOUTUBE ====
    print("\n--- YOUTUBE ---\n")
    
    r = await server.process_command("download youtube video https://youtu.be/dQw4w9WgXcQ", mock)
    check("YouTube DL", r)
    
    # ==== FACE/EMOTION ====
    print("\n--- FACE & EMOTION ---\n")
    
    r = await server.process_command("verify me", mock)
    check("Face verify", r)
    
    r = await server.process_command("enable mood detection", mock)
    check("Mood enable", r)
    
    r = await server.process_command("disable mood detection", mock)
    check("Mood disable", r)
    
    r = await server.process_command("enable gesture control", mock)
    check("Gesture enable", r)
    
    r = await server.process_command("disable gesture control", mock)
    check("Gesture disable", r)
    
    # ==== SMART FEATURES ====
    print("\n--- SMART FEATURES ---\n")
    
    r = await server.process_command("read my clipboard", mock)
    check("Clipboard", r)
    
    r = await server.process_command("define algorithm", mock)
    check("Dictionary", r)
    
    r = await server.process_command("set reminder to call mom in 30 minutes", mock)
    check("Reminder", r)
    
    r = await server.process_command("what are my reminders", mock)
    check("List reminders", r)
    
    # ==== COMPOUND + SYSTEM ====
    print("\n--- SYSTEM ---\n")
    
    r = await server.process_command("go back", mock)
    check("Alt-tab", r)
    
    r = await server.process_command("mute volume", mock)
    check("Mute", r, ["volume", "mute"])
    
    r = await server.process_command("take a screenshot", mock)
    check("Screenshot", r)
    
    # ==== RESULTS ====
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} passed ({100*passed//total if total > 0 else 0}%)")
    print(f"{'='*60}")
    
    if failed > 0:
        print(f"\nFAILED:")
        for name, ok, resp in results:
            if not ok:
                print(f"  - {name}: {resp}")

asyncio.run(main())
