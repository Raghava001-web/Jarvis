"""
JARVIS Full Interface Launcher
Runs both voice assistant and GUI together
"""

import sys
import threading
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "jarvis"))

def run_gui():
    """Run the GUI in main thread"""
    from jarvis.gui.main_gui import create_combined_interface
    create_combined_interface()

def run_voice_assistant():
    """Run voice assistant in background"""
    try:
        from jarvis.core.jarvis_ultimate import JARVISUltimate
        jarvis = JARVISUltimate()
        jarvis.run()
    except Exception as e:
        print(f"Voice assistant error: {e}")

if __name__ == "__main__":
    print("="*50)
    print("    JARVIS - Full Interface")
    print("="*50)
    print("\nStarting JARVIS with GUI...")
    print("Controls: ESC=Exit, C=Chat, SPACE=Cycle State")
    print("="*50 + "\n")
    
    # Start voice assistant in background thread
    voice_thread = threading.Thread(target=run_voice_assistant, daemon=True)
    voice_thread.start()
    
    # Give voice assistant time to initialize
    time.sleep(2)
    
    # Run GUI in main thread (pygame requires main thread)
    run_gui()
