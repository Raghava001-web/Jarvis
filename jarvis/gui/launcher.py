"""
JARVIS Launcher — Choose your interface mode.
Run this to start JARVIS in either Web HUD or Desktop GUI mode.
"""

import sys
import os
from pathlib import Path

# Fix imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def show_menu():
    """Show the launcher menu."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║                                                  ║")
    print("  ║        J.A.R.V.I.S. — Launch System             ║")
    print("  ║        Just A Rather Very Intelligent System      ║")
    print("  ║                                                  ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print("  ║                                                  ║")
    print("  ║   [1]  🌐  Web HUD        (Browser Interface)   ║")
    print("  ║                                                  ║")
    print("  ║   [2]  🖥️   Desktop GUI    (Python Interface)    ║")
    print("  ║                                                  ║")
    print("  ║   [3]  ❌  Exit                                  ║")
    print("  ║                                                  ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()


def launch_web_hud():
    """Launch JARVIS with the Web HUD (browser-based)."""
    print("\n  [JARVIS] Starting Web HUD mode...")
    print("  [JARVIS] Browser interface will open automatically.\n")
    from jarvis.gui.web_hud_launcher import main
    main()


def launch_desktop_gui():
    """Launch JARVIS with the Desktop GUI (Python native)."""
    print("\n  [JARVIS] Starting Desktop GUI mode...")
    print("  [JARVIS] Python interface loading...\n")
    from jarvis.gui.desktop_gui import main
    main()


def main():
    while True:
        show_menu()
        choice = input("  Select mode (1/2/3): ").strip()

        if choice == "1":
            launch_web_hud()
            break
        elif choice == "2":
            launch_desktop_gui()
            break
        elif choice == "3":
            print("\n  [JARVIS] Goodbye, sir.\n")
            sys.exit(0)
        else:
            print("\n  Invalid choice. Please enter 1, 2, or 3.")
            import time
            time.sleep(1)


if __name__ == "__main__":
    main()
