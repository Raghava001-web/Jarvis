"""
Quick Test: Volume Control + App Launch
Tests the fixes made earlier
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "="*50)
print("JARVIS CORE FEATURES TEST")
print("="*50)

# Test 1: Volume Control with pycaw (NEW API)
print("\n[TEST 1] Volume Control (pycaw - new API)")
try:
    from pycaw.pycaw import AudioUtilities
    from comtypes import CoInitialize
    
    CoInitialize()
    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume  # New API
    
    # Get current volume
    current = volume.GetMasterVolumeLevelScalar() * 100
    print(f"  Current volume: {current:.0f}%")
    
    # Set to 50%
    volume.SetMasterVolumeLevelScalar(0.50, None)
    new_vol = volume.GetMasterVolumeLevelScalar() * 100
    print(f"  Set to 50%: {new_vol:.0f}%")
    
    # Restore
    volume.SetMasterVolumeLevelScalar(current/100, None)
    print(f"  Restored to: {current:.0f}%")
    
    print("  [PASS] pycaw volume control working!")
except Exception as e:
    print(f"  [FAIL] pycaw error: {e}")

# Test 2: Perplexity App Path
print("\n[TEST 2] Perplexity App Path")
perplexity_path = rf'C:\Users\{os.getenv("USERNAME")}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Perplexity.lnk'
if os.path.exists(perplexity_path):
    print(f"  Path exists: {perplexity_path}")
    print("  [PASS] Perplexity shortcut found!")
else:
    print(f"  Path NOT found: {perplexity_path}")
    print("  [FAIL] Perplexity shortcut missing")

# Test 3: System Control Module
print("\n[TEST 3] System Control Module")
try:
    from core.system_control import SystemControl
    sc = SystemControl(perception=None)
    print("  SystemControl initialized")
    print(f"  Volume interface: {'Available' if sc.volume_interface else 'Not available'}")
    
    # Test actual volume set
    if sc.volume_interface:
        current = sc.volume_interface.GetMasterVolumeLevelScalar() * 100
        sc.volume_interface.SetMasterVolumeLevelScalar(0.6, None)
        test = sc.volume_interface.GetMasterVolumeLevelScalar() * 100
        sc.volume_interface.SetMasterVolumeLevelScalar(current/100, None)
        print(f"  Volume test: set to 60% ({test:.0f}%), restored to {current:.0f}%")
    
    print("  [PASS] SystemControl working")
except Exception as e:
    print(f"  [FAIL] SystemControl error: {e}")

# Test 4: Open Perplexity (actual launch)
print("\n[TEST 4] Launch Perplexity App")
response = input("  Launch Perplexity? (y/n): ").strip().lower()
if response == 'y':
    try:
        os.startfile(perplexity_path)
        print("  [PASS] Perplexity launched!")
    except Exception as e:
        print(f"  [FAIL] Launch error: {e}")
else:
    print("  [SKIP] Launch skipped")

print("\n" + "="*50)
print("TEST COMPLETE")
print("="*50)
