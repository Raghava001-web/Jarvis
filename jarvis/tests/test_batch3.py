"""
BATCH 3: Thorough Error Testing
================================
Testing: music_handler.py, screenshot_handler.py, sound_effects.py
"""

import sys
import os
import traceback

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bugs_found = []


def log(msg):
    print(f"[TEST] {msg}")


def bug(component, description, severity="MEDIUM"):
    bugs_found.append({"component": component, "desc": description, "severity": severity})
    print(f"[BUG-{severity}] {component}: {description}")


def passed(test_name):
    print(f"[OK] {test_name}")


print("\n" + "=" * 70)
print("BATCH 3: DEEP ERROR TESTING")
print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: music_handler.py
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 1: music_handler.py")
print("-" * 70)

try:
    from core.music_handler import MusicHandler, MusicState, PlaybackState, Track
    passed("MusicHandler imports (+ MusicState, PlaybackState, Track)")
    
    # Test instantiation
    mh = MusicHandler()
    passed("MusicHandler instantiates")
    
    # Check actual methods (match real implementation)
    expected_methods = ['play', 'pause', 'next_track', 'previous_track', 
                        'get_state', 'get_current_track', 'handle_command']
    
    for method in expected_methods:
        if hasattr(mh, method):
            passed(f"MusicHandler has '{method}' method")
        else:
            bug("MusicHandler", f"Missing method: {method}", "MEDIUM")
    
    # Test get_state returns MusicState
    if hasattr(mh, 'get_state'):
        state = mh.get_state()
        if isinstance(state, MusicState):
            passed(f"get_state() returns MusicState")
        else:
            bug("MusicHandler", f"get_state() should return MusicState, got {type(state)}", "MEDIUM")
    
    # Test MusicState helper classes
    if hasattr(PlaybackState, 'PLAYING') and hasattr(PlaybackState, 'PAUSED'):
        passed("PlaybackState enum has PLAYING/PAUSED states")
    else:
        bug("PlaybackState", "Missing PLAYING or PAUSED states", "MEDIUM")
        
    # Test Track dataclass
    try:
        track = Track(name="Test Song", artist="Test Artist")
        passed(f"Track dataclass works: {track.name}")
    except Exception as e:
        bug("Track", f"Dataclass error: {e}", "MEDIUM")
    
except ImportError as e:
    bug("music_handler", f"Import error: {e}", "CRITICAL")
except Exception as e:
    bug("music_handler", f"Unexpected error: {e}", "CRITICAL")
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: screenshot_handler.py  
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 2: screenshot_handler.py")
print("-" * 70)

try:
    from core.screenshot_handler import ScreenshotHandler
    passed("ScreenshotHandler imports")
    
    # Test instantiation
    sh = ScreenshotHandler()
    passed("ScreenshotHandler instantiates")
    
    # Check actual methods (match real implementation)
    expected_methods = ['take_screenshot', 'take_fullscreen', 'take_region', 
                        'copy_to_clipboard', 'get_recent_screenshots', 'open_screenshot_folder']
    for method in expected_methods:
        if hasattr(sh, method):
            passed(f"ScreenshotHandler has '{method}' method")
        else:
            bug("ScreenshotHandler", f"Missing method: {method}", "MEDIUM")
    
    # Check save_dir attribute
    if hasattr(sh, 'save_dir'):
        passed(f"save_dir attribute exists: {sh.save_dir}")
    else:
        bug("ScreenshotHandler", "Missing save_dir attribute", "LOW")
    
    # Test get_recent_screenshots returns list
    if hasattr(sh, 'get_recent_screenshots'):
        recent = sh.get_recent_screenshots()
        if isinstance(recent, list):
            passed(f"get_recent_screenshots() returns list ({len(recent)} items)")
        else:
            bug("ScreenshotHandler", f"get_recent_screenshots() should return list, got {type(recent)}", "MEDIUM")
    
    # Check for available backends
    if hasattr(sh, 'pyautogui_available') or hasattr(sh, 'pil_available'):
        has_backend = getattr(sh, 'pyautogui_available', False) or getattr(sh, 'pil_available', False)
        if has_backend:
            passed(f"Screenshot backend available")
        else:
            log("Warning: No screenshot backend (pyautogui/PIL) available")
    
except ImportError as e:
    bug("screenshot_handler", f"Import error: {e}", "CRITICAL")
except Exception as e:
    bug("screenshot_handler", f"Unexpected error: {e}", "CRITICAL")
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: sound_effects.py
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("FILE 3: sound_effects.py")
print("-" * 70)

try:
    from core.sound_effects import (
        SoundEffectsLibrary, ImmersiveStoryteller, 
        StoryGenre, SoundAsset, GENRE_SOUNDS
    )
    passed("sound_effects imports work")
    
    # Test SoundEffectsLibrary
    sel = SoundEffectsLibrary()
    passed("SoundEffectsLibrary instantiates")
    
    # Check actual methods
    expected_methods = ['play_sound', 'play_music', 'stop_music', 'set_music_volume', 'play_effect']
    for method in expected_methods:
        if hasattr(sel, method):
            passed(f"SoundEffectsLibrary has '{method}' method")
        else:
            bug("SoundEffectsLibrary", f"Missing method: {method}", "MEDIUM")
    
    # Check genre support via GENRE_SOUNDS constant
    if isinstance(GENRE_SOUNDS, dict):
        genres = list(GENRE_SOUNDS.keys())
        passed(f"GENRE_SOUNDS has {len(genres)} genres: {[g.value for g in genres]}")
    else:
        bug("GENRE_SOUNDS", "Should be a dict", "LOW")
    
    # Test ImmersiveStoryteller
    ist = ImmersiveStoryteller()
    passed("ImmersiveStoryteller instantiates")
    
    expected_ist_methods = ['tell_story', 'set_genre', 'stop', 'cleanup']
    for method in expected_ist_methods:
        if hasattr(ist, method):
            passed(f"ImmersiveStoryteller has '{method}' method")
        else:
            bug("ImmersiveStoryteller", f"Missing method: {method}", "MEDIUM")
    
    # Test StoryGenre enum
    for genre in ['COMEDY', 'HORROR', 'BEDTIME', 'ADVENTURE']:
        if hasattr(StoryGenre, genre):
            passed(f"StoryGenre.{genre} exists")
        else:
            bug("StoryGenre", f"Missing genre: {genre}", "LOW")

except ImportError as e:
    bug("sound_effects", f"Import error: {e}", "CRITICAL")
except Exception as e:
    bug("sound_effects", f"Unexpected error: {e}", "CRITICAL")
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("BATCH 3 SUMMARY")
print("=" * 70)

critical = [b for b in bugs_found if b["severity"] == "CRITICAL"]
high = [b for b in bugs_found if b["severity"] == "HIGH"]
medium = [b for b in bugs_found if b["severity"] == "MEDIUM"]
low = [b for b in bugs_found if b["severity"] == "LOW"]

print(f"\nCRITICAL: {len(critical)}")
print(f"HIGH: {len(high)}")
print(f"MEDIUM: {len(medium)}")
print(f"LOW: {len(low)}")
print(f"TOTAL BUGS: {len(bugs_found)}")

if bugs_found:
    print("\nBUGS TO FIX:")
    for b in bugs_found:
        print(f"  [{b['severity']}] {b['component']}: {b['desc']}")
else:
    print("\nNo bugs found in Batch 3!")

print("\n" + "=" * 70)
