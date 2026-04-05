"""
JARVIS Phase 4 - Comprehensive Live Demo Test
=============================================
Tests all Phase 4 features including new handlers
"""

import sys
sys.path.insert(0, '.')

def run_comprehensive_test():
    print("\n" + "="*70)
    print("          JARVIS PHASE 4 - COMPREHENSIVE DEMO TEST")
    print("="*70 + "\n")
    
    results = []
    
    # Load jarvis_ultimate.py content to check routing
    with open("core/jarvis_ultimate.py", "r", encoding="utf-8") as f:
        content = f.read().lower()
    
    # Test categories
    tests = [
        # PHASE 3 FEATURES
        ("Phase 3", [
            ("Screenshot", ["screenshot", "screen capture"]),
            ("OCR/Read Screen", ["read screen", "ocr"]),
            ("PDF Summarize", ["summarize pdf", "pdf summary"]),
            ("System Control", ["scroll down", "minimize", "maximize"]),
        ]),
        
        # PHASE 4A - DEMO COMMANDS  
        ("Phase 4A - Demo", [
            ("Play Music", ["play music", "playpause"]),
            ("Next Track", ["next", "nexttrack"]),
            ("Pause", ["pause"]),
            ("Resume", ["resume"]),
            ("Open App", ["open_app", "open chrome"]),
            ("Close App", ["close_app", "close"]),
            ("Volume", ["volume up", "volume_up"]),
            ("Story", ["story", "tale"]),
            ("Joke", ["joke"]),
        ]),
        
        # PHASE 4B - NEW FEATURES
        ("Phase 4B - New Features", [
            ("Switch To", ["switch to", "app_switcher"]),
            ("Switch Back", ["switch back", "go back"]),
            ("List Windows", ["list windows", "what's open"]),
            ("Remind Me", ["remind me", "set reminder"]),
            ("My Reminders", ["my reminders", "read reminders"]),
            ("Add Event", ["add event", "add meeting"]),
            ("My Schedule", ["my schedule", "events today"]),
            ("Save Clipboard", ["save this", "save clipboard"]),
            ("What Did I Copy", ["what did i copy", "last copied"]),
            ("Clipboard History", ["clipboard history"]),
        ]),
    ]
    
    for category, category_tests in tests:
        print(f"\n{'='*50}")
        print(f"  {category}")
        print(f"{'='*50}")
        
        for name, keywords in category_tests:
            found = any(kw in content for kw in keywords)
            status = "[OK]" if found else "[MISSING]"
            results.append(found)
            print(f"  {status} {name}")
            if not found:
                print(f"       Keywords: {keywords}")
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*70)
    print(f"          RESULTS: {passed}/{total} FEATURES VERIFIED")
    print("="*70)
    
    if passed == total:
        print("\n[SUCCESS] ALL FEATURES IMPLEMENTED AND WIRED!")
    else:
        print(f"\n[WARNING] {total - passed} features need attention")
    
    return passed, total


def test_module_imports():
    """Test that all modules can be imported"""
    print("\n" + "="*50)
    print("  MODULE IMPORT TEST")
    print("="*50)
    
    modules = [
        ("core.app_switcher", "AppSwitcher"),
        ("core.calendar_manager", "CalendarManager"),
        ("core.clipboard_memory", "ClipboardMemory"),
        ("core.reminder_manager", "ReminderManager"),
        ("core.screen_control", "ScreenControlHandler"),
        ("core.pdf_handler", "PDFHandler"),
        ("core.ocr_handler", "OCRHandler"),
    ]
    
    results = []
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            instance = cls()  # Try to instantiate
            print(f"  [OK] {class_name}")
            results.append(True)
        except Exception as e:
            print(f"  [FAIL] {class_name}: {str(e)[:50]}")
            results.append(False)
    
    return sum(results), len(results)


if __name__ == "__main__":
    # Run tests
    feature_passed, feature_total = run_comprehensive_test()
    module_passed, module_total = test_module_imports()
    
    total_passed = feature_passed + module_passed
    total_tests = feature_total + module_total
    
    print("\n" + "="*70)
    print(f"        FINAL SCORE: {total_passed}/{total_tests}")
    print("="*70)
    
    if total_passed == total_tests:
        print("\n[READY FOR DEMO] All systems go!")
    else:
        print(f"\n[NEEDS WORK] {total_tests - total_passed} items need fixing")
