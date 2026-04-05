"""
Quick JARVIS Launcher - Simple script to run JARVIS with HUD
"""

import sys
from pathlib import Path

# Add jarvis directory to path
jarvis_dir = Path(__file__).parent / "jarvis"
sys.path.insert(0, str(jarvis_dir))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("       Starting J.A.R.V.I.S. with Advanced Interface")
    print("="*60 + "\n")
    
    try:
        from jarvis.jarvis_unified import main
        main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nTrying alternative launch...")
        
        try:
            from jarvis.gui.advanced_hud import run_hud
            run_hud()
        except Exception as e2:
            print(f"Could not start HUD: {e2}")
            print("\nPlease run from the jarvis directory:")
            print("  cd jarvis")
            print("  python jarvis_unified.py")
