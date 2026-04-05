# tests/conftest.py
"""
Pytest configuration for JARVIS tests.
Adds project root to path for imports.
"""

import sys
from pathlib import Path

# Add project root and jarvis folder to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "jarvis"))
sys.path.insert(0, str(project_root / "jarvis" / "core"))
