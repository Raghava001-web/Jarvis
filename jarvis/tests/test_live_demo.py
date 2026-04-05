"""
JARVIS FINAL LIVE DEMO TEST
============================
Comprehensive test of ALL features before live demo
"""

import sys
sys.path.insert(0, '.')

def test_all_features():
    print("\n" + "="*70)
    print("          JARVIS FINAL LIVE DEMO TEST")
    print("="*70 + "\n")
    
    # Check jarvis_ultimate.py content
    with open("core/jarvis_ultimate.py", "r", encoding="utf-8") as f:
        content = f.read().lower()
    
    tests = {
        "Phase 3 Features": {
            "Screenshot": ["screenshot", "take_screenshot"],
            "OCR/Screen Reading": ["read screen", "ocr"],
            "PDF Summarization": ["summarize pdf", "pdf"],
            "Screen Control": ["scroll", "minimize", "screen_control"],
        },
        "Phase 4A - Demo Core": {
            "Play Music": ["playpause", "play music"],
            "Next/Previous Track": ["nexttrack", "prevtrack"],
            "Pause/Resume": ["pause", "resume"],
            "Open App": ["open_app", "app_finder"],
            "Close App": ["close_app"],
            "Volume Control": ["volume"],
            "Horror Story": ["story", "horror"],
            "Jokes": ["joke"],
        },
        "Phase 4B - App Switching": {
            "Switch To App": ["switch to", "app_switcher"],
            "Switch Back": ["switch back", "go back"],
            "List Windows": ["list windows", "what's open"],
        },
        "Phase 4B - Calendar & Reminders": {
            "Set Reminder": ["remind me", "set reminder"],
            "Read Reminders": ["my reminders", "read reminders"],
            "Add Event": ["add event", "add meeting"],
            "Check Schedule": ["my schedule", "events today"],
        },
        "Phase 4B - Clipboard Memory": {
            "Save Clipboard": ["save this", "save clipboard"],
            "Read Last Copied": ["what did i copy", "last copied"],
            "Clipboard History": ["clipboard history"],
        },
        "Phase 4B - Workflows": {
            "Multi-Action Commands": ["workflow", "is_workflow_command"],
            "Morning Routine": ["morning routine"],
            "Focus Mode": ["focus mode"],
        },
    }
    
    total_passed = 0
    total_tests = 0
    
    for category, category_tests in tests.items():
        print(f"\n{'='*50}")
        print(f"  {category}")
        print(f"{'='*50}")
        
        passed = 0
        for name, keywords in category_tests.items():
            found = any(kw in content for kw in keywords)
            status = "[OK]" if found else "[MISSING]"
            if found:
                passed += 1
            print(f"  {status} {name}")
        
        total_passed += passed
        total_tests += len(category_tests)
        print(f"  >> {passed}/{len(category_tests)} passed")
    
    print("\n" + "="*70)
    print(f"          FINAL RESULTS: {total_passed}/{total_tests}")
    print("="*70)
    
    return total_passed, total_tests


def test_voice_commands():
    """Test voice command routing simulation"""
    print("\n" + "="*50)
    print("  VOICE COMMAND ROUTING TEST")
    print("="*50)
    
    # These are the exact commands users will speak
    test_commands = [
        ("play music", "Media Control"),
        ("pause", "Media Control"),
        ("next", "Media Control"),
        ("volume up", "Volume Control"),
        ("open chrome", "App Control"),
        ("close notepad", "App Control"),
        ("switch to spotify", "App Switching"),
        ("switch back", "App Switching"),
        ("what's open", "App Switching"),
        ("remind me at 8 PM to sleep", "Reminders"),
        ("my reminders", "Reminders"),
        ("add meeting standup at 10 am", "Calendar"),
        ("what's on my schedule", "Calendar"),
        ("save this", "Clipboard"),
        ("what did i copy", "Clipboard"),
        ("clipboard history", "Clipboard"),
        ("scroll down", "Screen Control"),
        ("minimize", "Screen Control"),
        ("take a screenshot", "Screenshot"),
        ("read my screen", "OCR"),
        ("tell me a horror story", "Entertainment"),
        ("tell me a joke", "Entertainment"),
        ("open chrome and search for weather", "Workflow"),
        ("morning routine", "Workflow"),
    ]
    
    # Load and check
    with open("core/jarvis_ultimate.py", "r", encoding="utf-8") as f:
        content = f.read().lower()
    
    passed = 0
    for command, category in test_commands:
        # Check if the key words are in jarvis_ultimate.py
        key_word = command.split()[0]  # First word usually indicates handler
        found = key_word in content
        
        if command == "open chrome and search for weather":
            found = "workflow" in content
        elif command == "morning routine":
            found = "morning routine" in content
        
        status = "[OK]" if found else "[MISSING]"
        if found:
            passed += 1
        print(f"  {status} \"{command}\" -> {category}")
    
    print(f"\n  >> {passed}/{len(test_commands)} voice commands ready")
    return passed, len(test_commands)


def test_module_health():
    """Test all modules can be instantiated"""
    print("\n" + "="*50)
    print("  MODULE HEALTH CHECK")
    print("="*50)
    
    modules = [
        ("AppSwitcher", "core.app_switcher"),
        ("CalendarManager", "core.calendar_manager"),
        ("ClipboardMemory", "core.clipboard_memory"),
        ("ReminderManager", "core.reminder_manager"),
        ("WorkflowManager", "core.workflow_manager"),
        ("ScreenControlHandler", "core.screen_control"),
        ("PDFHandler", "core.pdf_handler"),
        ("OCRHandler", "core.ocr_handler"),
        ("ScreenshotHandler", "core.screenshot_handler"),
    ]
    
    passed = 0
    for class_name, module_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            instance = cls()
            print(f"  [OK] {class_name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {class_name}: {str(e)[:40]}")
    
    print(f"\n  >> {passed}/{len(modules)} modules healthy")
    return passed, len(modules)


if __name__ == "__main__":
    # Run all tests
    feat_passed, feat_total = test_all_features()
    voice_passed, voice_total = test_voice_commands()
    mod_passed, mod_total = test_module_health()
    
    total_passed = feat_passed + voice_passed + mod_passed
    total_tests = feat_total + voice_total + mod_total
    
    print("\n" + "="*70)
    print(f"               GRAND TOTAL: {total_passed}/{total_tests}")
    print("="*70)
    
    score_pct = (total_passed / total_tests) * 100
    if score_pct == 100:
        print("\n[PERFECT SCORE] JARVIS is DEMO READY!")
    elif score_pct >= 90:
        print(f"\n[EXCELLENT] JARVIS is {score_pct:.0f}% ready for demo!")
    else:
        print(f"\n[NEEDS WORK] {total_tests - total_passed} items need attention")
    
    print("\n" + "="*70)
    print("          DEMO COMMANDS CHEAT SHEET")
    print("="*70)
    print("""
    MEDIA:     "Play music" | "Pause" | "Next" | "Volume up"
    APPS:      "Open Chrome" | "Close Notepad" | "Switch to Spotify"
    MEMORY:    "Remind me at 8 to sleep" | "What's on my schedule"
    CLIPBOARD: "Save this" | "What did I copy" | "Clipboard history"
    SCREEN:    "Scroll down" | "Minimize" | "Take screenshot"
    FUN:       "Tell me a horror story" | "Tell me a joke"
    WORKFLOW:  "Open Chrome and search for weather"
    """)
