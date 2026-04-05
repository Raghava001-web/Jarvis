"""
Phase 13: Remaining Subsystems Integration Test
=================================================
Tests: PDF, Music, Calendar, WhatsApp messaging, Habit Tracker,
Task Manager, Wellness Monitor, Hotkeys, Proactive, YouTube
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
        print(f"  [PASS] {name} {detail[:70]}")
    else:
        FAILED += 1
        ERRORS.append(f"{name}: {detail}")
        print(f"  [FAIL] {name} {detail[:70]}")

print("=" * 70)
print("PHASE 13: REMAINING SUBSYSTEMS INTEGRATION TEST")
print("=" * 70)

# ============================================================
# 1. PDF HANDLER
# ============================================================
print("\n--- 1. PDF Handler ---")
try:
    from jarvis.core.pdf_handler import PDFHandler
    check("PDFHandler imports", True)
    pdf = PDFHandler()
    check("PDFHandler init", pdf is not None)
    check("Has read_pdf", hasattr(pdf, 'read_pdf') or hasattr(pdf, 'extract_text'))
    check("Has summarize", hasattr(pdf, 'summarize') or hasattr(pdf, 'summarize_pdf'))
    check("Has list_pdfs", hasattr(pdf, 'list_pdfs') or hasattr(pdf, 'list_recent'))
except Exception as e:
    check("PDFHandler", False, str(e))

# ============================================================
# 2. MUSIC HANDLER  
# ============================================================
print("\n--- 2. Music Handler ---")
try:
    from jarvis.core.music_handler import MusicHandler
    check("MusicHandler imports", True)
    mh = MusicHandler()
    check("MusicHandler init", mh is not None)
    check("Has play", hasattr(mh, 'play') or hasattr(mh, 'play_music'))
    check("Has pause", hasattr(mh, 'pause') or hasattr(mh, 'toggle_pause'))
    check("Has next_track", hasattr(mh, 'next_track'))
    check("Has previous_track", hasattr(mh, 'previous_track'))
    check("Media keys available", hasattr(mh, 'media_keys_available'))
except Exception as e:
    check("MusicHandler", False, str(e))

# ============================================================
# 3. CALENDAR INTEGRATION
# ============================================================
print("\n--- 3. Calendar Integration ---")
try:
    from jarvis.core.calendar_integration import CalendarIntegration
    check("CalendarIntegration imports", True)
    cal = CalendarIntegration()
    check("CalendarIntegration init", cal is not None)
    check("Has get_today_events", hasattr(cal, 'get_today_events') or hasattr(cal, 'get_events_today'))
    check("Has add_event", hasattr(cal, 'add_event') or hasattr(cal, 'create_event'))
    check("Has get_upcoming", hasattr(cal, 'get_upcoming') or hasattr(cal, 'get_upcoming_events'))
except Exception as e:
    check("CalendarIntegration", False, str(e))

# ============================================================
# 4. WHATSAPP HANDLER  
# ============================================================
print("\n--- 4. WhatsApp Handler ---")
try:
    from jarvis.core.whatsapp_handler import WhatsAppHandler
    check("WhatsAppHandler imports", True)
    wa = WhatsAppHandler()
    check("WhatsAppHandler init", wa is not None)
    check("Has send_message", hasattr(wa, 'send_message'))
    check("Has search_contact", hasattr(wa, 'search_contact') or hasattr(wa, 'find_contact'))
    check("Has open_chat", hasattr(wa, 'open_chat') or hasattr(wa, 'open_whatsapp'))
except Exception as e:
    check("WhatsAppHandler", False, str(e))

# ============================================================
# 5. HABIT TRACKER
# ============================================================
print("\n--- 5. Habit Tracker ---")
try:
    from jarvis.core.habit_tracker import HabitTracker
    check("HabitTracker imports", True)
    ht = HabitTracker()
    check("HabitTracker init", ht is not None)
    check("Has add_habit", hasattr(ht, 'add_habit') or hasattr(ht, 'create_habit'))
    check("Has log_habit", hasattr(ht, 'log_habit') or hasattr(ht, 'mark_complete'))
    check("Has get_summary", hasattr(ht, 'get_summary') or hasattr(ht, 'get_daily_summary'))
except Exception as e:
    check("HabitTracker", False, str(e))

# ============================================================
# 6. TASK MANAGER
# ============================================================
print("\n--- 6. Task Manager ---")
try:
    from jarvis.core.task_manager import TaskManager
    check("TaskManager imports", True)
    tm = TaskManager()
    check("TaskManager init", tm is not None)
    check("Has add_task", hasattr(tm, 'add_task') or hasattr(tm, 'create_task'))
    check("Has list_tasks", hasattr(tm, 'list_tasks') or hasattr(tm, 'get_tasks'))
    check("Has complete_task", hasattr(tm, 'complete_task') or hasattr(tm, 'mark_complete'))
except Exception as e:
    check("TaskManager", False, str(e))

# ============================================================
# 7. WELLNESS MONITOR
# ============================================================
print("\n--- 7. Wellness Monitor ---")
try:
    from jarvis.core.wellness_monitor import WellnessMonitor
    check("WellnessMonitor imports", True)
    wm = WellnessMonitor()
    check("WellnessMonitor init", wm is not None)
    check("Has check_wellness", hasattr(wm, 'check_wellness'))
    check("Has get_summary", hasattr(wm, 'get_wellness_summary') or hasattr(wm, 'get_summary'))
    check("Has reset_session", hasattr(wm, 'reset_session'))
except Exception as e:
    check("WellnessMonitor", False, str(e))

# ============================================================
# 8. PROACTIVE ASSISTANT
# ============================================================
print("\n--- 8. Proactive Assistant ---")
try:
    from jarvis.core.proactive_assistant import ProactiveAssistant
    check("ProactiveAssistant imports", True)
    pa = ProactiveAssistant()
    check("ProactiveAssistant init", pa is not None)
    check("Has get_suggestions", hasattr(pa, 'get_suggestions') or hasattr(pa, 'suggest'))
    check("Has learn_pattern", hasattr(pa, 'learn_pattern') or hasattr(pa, 'record_action'))
except Exception as e:
    check("ProactiveAssistant", False, str(e))

# ============================================================
# 9. YOUTUBE DOWNLOADER
# ============================================================
print("\n--- 9. YouTube Downloader ---")
try:
    from jarvis.core.youtube_downloader import YouTubeDownloader
    check("YouTubeDownloader imports", True)
    yt = YouTubeDownloader()
    check("YouTubeDownloader init", yt is not None)
    check("Has download", hasattr(yt, 'download') or hasattr(yt, 'download_video'))
    check("Has search", hasattr(yt, 'search') or hasattr(yt, 'search_youtube'))
except Exception as e:
    check("YouTubeDownloader", False, str(e))

# ============================================================
# 10. WEBSOCKET DISPATCH FOR REMAINING COMMANDS  
# ============================================================
print("\n--- 10. WebSocket Dispatch for Remaining Features ---")
try:
    from jarvis.gui.websocket_server import JARVISWebSocketServer
    server = JARVISWebSocketServer()
    
    # Verify all subsystems on server
    checks = [
        ("pdf_handler", server.pdf_handler if hasattr(server, 'pdf_handler') else getattr(server, 'jarvis', None) and getattr(server.jarvis, 'pdf_handler', None)),
        ("habit_tracker", getattr(server, 'habit_tracker', None)),
        ("task_manager_obj", getattr(server, 'task_manager_obj', None)),
        ("wellness_monitor", getattr(server, 'wellness_monitor', None)),
        ("youtube_downloader", getattr(server, 'youtube_downloader', None)),
        ("hotkey_system", getattr(server, 'hotkey_system', None)),
        ("calendar", getattr(server, 'calendar', None)),
        ("proactive_assistant", getattr(server, 'proactive_assistant', None)),
    ]
    
    for name, obj in checks:
        check(f"Server {name}", obj is not None, 
              f"type={type(obj).__name__}" if obj else "NONE")
    
    # Test dispatches
    class MockWS:
        sent = []
        open = True
        async def send(self, data): self.sent.append(json.loads(data))
    
    mock_ws = MockWS()
    
    async def test_remaining_commands():
        # PDF
        r = await server.process_command("read pdf", mock_ws)
        check("Read PDF cmd", r is not None, r[:70] if r else "None")
        
        # Music
        r = await server.process_command("play music", mock_ws)
        check("Play music cmd", r is not None, r[:70] if r else "None")
        
        r = await server.process_command("next song", mock_ws)
        check("Next song cmd", r is not None, r[:70] if r else "None")
        
        # Calendar
        r = await server.process_command("what are my events today", mock_ws)
        check("Today events cmd", r is not None, r[:70] if r else "None")
        
        # Habit
        r = await server.process_command("add habit drink water", mock_ws)
        check("Add habit cmd", r is not None, r[:70] if r else "None")
        
        # Task
        r = await server.process_command("add task finish project report", mock_ws)
        check("Add task cmd", r is not None, r[:70] if r else "None")
        
        r = await server.process_command("list my tasks", mock_ws)
        check("List tasks cmd", r is not None, r[:70] if r else "None")
        
        # Wellness
        r = await server.process_command("wellness check", mock_ws)
        check("Wellness check cmd", r is not None, r[:70] if r else "None")
        
        r = await server.process_command("wellness summary", mock_ws)
        check("Wellness summary cmd", r is not None, r[:70] if r else "None")
        
        # YouTube
        r = await server.process_command("download youtube video", mock_ws)
        check("YouTube download cmd", r is not None, r[:70] if r else "None")
    
    asyncio.run(test_remaining_commands())
    
except Exception as e:
    import traceback
    check("WebSocket remaining dispatch", False, str(e))
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

sys.exit(1 if FAILED > 0 else 0)
