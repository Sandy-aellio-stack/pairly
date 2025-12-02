# This file is kept for backwards compatibility
# The actual server is now in main.py
# Import and expose the main app

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app

__all__ = ["app"]