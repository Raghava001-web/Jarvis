"""
Live Server Init Test - Tests the ACTUAL JARVISWebSocketServer initialization
without starting the WebSocket listener. Catches all runtime init errors.
"""
import sys, os, traceback
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Set up paths the same way websocket_server.py does
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
jarvis_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if jarvis_dir not in sys.path:
    sys.path.insert(0, jarvis_dir)

os.chdir(jarvis_dir)

print("=" * 70)
print("LIVE SERVER INIT TEST")
print("=" * 70)
print()

# Load .env
from dotenv import load_dotenv
env_path = os.path.join(jarvis_dir, '.env')
load_dotenv(env_path)
print(f"[ENV] GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'MISSING'}")
print(f"[ENV] OPENWEATHER_API_KEY: {'SET' if os.getenv('OPENWEATHER_API_KEY') else 'MISSING'}")
print(f"[ENV] SPOTIPY_CLIENT_ID: {'SET' if os.getenv('SPOTIPY_CLIENT_ID') else 'MISSING'}")
print()

# Test server construction
try:
    from gui.websocket_server import JARVISWebSocketServer
    print("[TEST] Creating JARVISWebSocketServer...")
    server = JARVISWebSocketServer()
    print()
    print("[TEST] Server created successfully!")
    print()
    
    # Check what actually initialized
    checks = [
        ('self.jarvis (JARVISUltimate)', server.jarvis),
        ('self.hud_perception', server.hud_perception),
        ('self.system_control', server.system_control),
        ('self.alarm_system', server.alarm_system),
        ('self.weather_handler', server.weather_handler),
        ('self.news_handler', server.news_handler),
        ('self.entertainment', server.entertainment),
        ('self.screenshot_handler', server.screenshot_handler),
        ('self.ocr_handler', getattr(server, 'ocr_handler', None)),
        ('self.knowledge', server.knowledge),
        ('self.state_manager', server.state_manager),
        ('self.chat_history', getattr(server, 'chat_history', None)),
        ('self.reminder_manager', getattr(server, 'reminder_manager', None)),
        ('self.screen_control', getattr(server, 'screen_control', None)),
        ('self.whatsapp_handler', getattr(server, 'whatsapp_handler', None)),
        ('self.gesture_controller', server.gesture_controller),
        ('self.face_recognition', server.face_recognition),
        ('self.emotion_detector', server.emotion_detector),
        ('self.dictionary_handler', getattr(server, 'dictionary_handler', None)),
        ('self.music_handler', getattr(server, 'music_handler', None)),
        ('self.app_manager', getattr(server, 'app_manager', None)),
        ('ROUTER_AVAILABLE', None),  # Special check
    ]
    
    print("=" * 70)
    print("MODULE STATUS")
    print("=" * 70)
    
    ok = 0
    missing = 0
    for name, obj in checks:
        if name == 'ROUTER_AVAILABLE':
            from gui.websocket_server import ROUTER_AVAILABLE
            status = "[OK]" if ROUTER_AVAILABLE else "[XX]"
            val = str(ROUTER_AVAILABLE)
            if ROUTER_AVAILABLE: ok += 1
            else: missing += 1
        elif obj is not None:
            status = "[OK]"
            val = type(obj).__name__
            ok += 1
        else:
            status = "[--]"
            val = "None"
            missing += 1
        print(f"  {status} {name:40s} {val}")
    
    print()
    print(f"RESULT: {ok} initialized, {missing} missing/None")
    
    # Test a command through the pipeline
    print()
    print("=" * 70)
    print("COMMAND DISPATCH TEST")
    print("=" * 70)
    
    test_commands = [
        "what time is it",
        "tell me a joke",
        "volume up",
        "set alarm for 7am",
    ]
    
    for cmd in test_commands:
        try:
            result = server._route_through_router(cmd)
            status = "[OK]" if result else "[--]"
            display = (result[:60] + "...") if result and len(result) > 60 else result
            print(f"  {status} '{cmd}' => {display}")
        except Exception as e:
            print(f"  [XX] '{cmd}' => ERROR: {e}")
            traceback.print_exc()
    
except Exception as e:
    print(f"[FAIL] Server init crashed: {e}")
    traceback.print_exc()
