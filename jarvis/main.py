"""
JARVIS Ultimate - Main Entry Point
Run this file to start JARVIS
"""

import sys
from core.jarvis_ultimate import JARVISUltimate


def main():
    """Main entry point"""
    try:
        jarvis = JARVISUltimate()
        jarvis.run()
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt - Shutting down")
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
