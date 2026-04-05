"""Phase 10 — Quick verification of all new features"""
import sys, os
os.chdir(r'c:\Users\chrag\OneDrive\Documents\AI_Voice_Assistant')
sys.path.insert(0, '.')
sys.path.insert(0, 'jarvis')

PASSED = 0
FAILED = 0

def check(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name} {detail}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} {detail}")

print("=" * 60)
print("PHASE 10 VERIFICATION")
print("=" * 60)

# 1. Chat History
print("\n--- 1. Chat History ---")
try:
    from jarvis.core.chat_history import ChatHistory
    ch = ChatHistory()
    ch.add_message('user', 'open youtube')
    ch.add_message('assistant', 'Opening YouTube, sir.')
    ch.add_message('user', 'play some music')
    ch.add_message('assistant', 'Playing music, sir.')
    recent = ch.get_recent(3)
    check("ChatHistory stores messages", len(recent) >= 2)
    check("get_recent returns messages", any(m.role == 'user' for m in recent))
    stats = ch.get_statistics()
    check("get_statistics works", 'total_messages' in stats)
except Exception as e:
    check("ChatHistory", False, str(e))

# 2. WebSocket server imports cleanly
print("\n--- 2. WebSocket Server Import ---")
try:
    from jarvis.gui.websocket_server import JARVISWebSocketServer
    check("JARVISWebSocketServer imports", True)
    
    # Check compound command splitting
    server = JARVISWebSocketServer.__new__(JARVISWebSocketServer)
    
    r1 = server._split_compound_command("switch to chrome and open youtube")
    check("Split switch+open", len(r1) == 2, str(r1))
    
    r2 = server._split_compound_command("open notepad then set alarm for 5 minutes")
    check("Split with 'then'", len(r2) == 2, str(r2))
except Exception as e:
    check("WebSocket import", False, str(e))

# 3. AppFinder — all features
print("\n--- 3. AppFinder Full Test ---")
try:
    from jarvis.core.app_finder import AppFinder, AppManager
    af = AppFinder()
    
    # Web apps 
    for app in ['youtube', 'gmail', 'chatgpt', 'whatsapp', 'spotify']:
        result = af.find(app)
        check(f"find({app})", result is not None, f"type={result.app_type if result else 'None'}")
    
    # Typos
    for typo, expected in [('chatpgt', 'chatgpt'), ('spotofy', 'spotify')]:
        result = af.find(typo)
        status = result.name if result else "None"
        check(f"typo {typo}", result is not None, status)
    
    # AppManager (backward compat)
    am = AppManager()
    check("AppManager init", am is not None)
except Exception as e:
    check("AppFinder", False, str(e))

# 4. Context Memory
print("\n--- 4. Context Memory ---")
try:
    from jarvis.core.context_memory import ContextMemory
    cm = ContextMemory()
    cm.working.add_turn("open youtube", "Opening YouTube", "open_app")
    ctx = cm.working.get_context_prompt()
    check("Context prompt", len(ctx) > 10)
except Exception as e:
    check("Context Memory", False, str(e))

print("\n" + "=" * 60)
print(f"RESULTS: {PASSED} passed, {FAILED} failed")
print("=" * 60)
