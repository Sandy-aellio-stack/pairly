# This file is kept for backwards compatibility
# The actual server is now in main.py
# Import and expose the main app

import sys
from pathlib import Path

# Add parent directory to path for imports (so backend package is accessible)
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Load .env file before importing main app
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from backend.main import app

__all__ = ["app"]