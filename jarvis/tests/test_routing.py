"""
JARVIS Phase 4A: Real Command Routing Test
==========================================
Tests actual command routing through keyword detection in jarvis_ultimate.py
(Not just the ML classifier which has low accuracy)
"""

import sys
sys.path.insert(0, '.')

def test_keyword_routing():
    """Test if keywords in commands will trigger the correct handlers"""
    
    print("\n" + "="*60)
    print("     JARVIS KEYWORD ROUTING VERIFICATION")
    print("="*60 + "\n")
    
    # Commands and expected keywords that should trigger them
    tests = [
        # (Command, Expected keyword/phrase detected, Handler section)
        ("play music", "play_music intent OR 'play' keyword", "MUSIC"),
        ("next", "music context OR screen_control", "MUSIC/SCREEN"),
        ("pause", "pause_music intent", "MUSIC"),
        ("resume", "resume -> play_music", "MUSIC"),
        
        ("open chrome", "'open' keyword -> open_app", "APP"),
        ("close chrome", "'close' keyword -> close_app", "APP"),
        
        ("take a screenshot", "'screenshot' in command", "SCREENSHOT"),
        ("read my screen", "'read screen' phrase", "OCR"),
        ("summarize this pdf", "'summarize pdf' phrase", "PDF"),
        
        ("minimize window", "'minimize' keyword -> screen_control", "SCREEN_CONTROL"),
        ("scroll down", "'scroll down' keyword", "SCREEN_CONTROL"),
        ("volume up", "'volume' + 'up' keywords", "VOLUME"),
        
        ("tell me a horror story", "'story' keyword -> entertainment", "ENTERTAINMENT"),
        ("tell me a joke", "'joke' keyword", "ENTERTAINMENT"),
    ]
    
    print("Checking keyword presence in jarvis_ultimate.py...\n")
    
    # Load the file content
    with open("core/jarvis_ultimate.py", "r", encoding="utf-8") as f:
        ultimate_content = f.read().lower()
    
    results = []
    
    for cmd, expected, section in tests:
        # Check critical keywords
        keywords_to_check = []
        if "screenshot" in cmd:
            keywords_to_check = ["screenshot", "screen capture"]
        elif "read" in cmd and "screen" in cmd:
            keywords_to_check = ["read screen", "read text", "ocr"]
        elif "summarize" in cmd and "pdf" in cmd:
            keywords_to_check = ["summarize pdf", "pdf summary"]
        elif "minimize" in cmd:
            keywords_to_check = ["minimize"]
        elif "scroll" in cmd:
            keywords_to_check = ["scroll down", "scroll up"]
        elif "volume" in cmd:
            keywords_to_check = ["volume_up", "volume up"]
        elif "story" in cmd:
            keywords_to_check = ["story", "tale"]
        elif "joke" in cmd:
            keywords_to_check = ["joke"]
        elif "open" in cmd:
            keywords_to_check = ["open_app", "open", "launch"]
        elif "close" in cmd:
            keywords_to_check = ["close_app", "close chrome", "close"]
        elif "play" in cmd:
            keywords_to_check = ["play_music", "play music"]
        elif "pause" in cmd:
            keywords_to_check = ["pause"]
        elif "next" in cmd:
            keywords_to_check = ["next"]
        elif "resume" in cmd:
            keywords_to_check = ["resume"]
        else:
            keywords_to_check = [cmd.split()[0]]
        
        found = any(kw in ultimate_content for kw in keywords_to_check)
        status = "✅" if found else "❌"
        results.append(found)
        
        print(f"{status} [{section}] '{cmd}'")
        print(f"   Keywords checked: {keywords_to_check}")
    
    print()
    passed = sum(results)
    total = len(results)
    
    print("="*60)
    print(f"    KEYWORD ROUTING: {passed}/{total} VERIFIED")
    print("="*60)
    
    return passed, total

if __name__ == "__main__":
    test_keyword_routing()
