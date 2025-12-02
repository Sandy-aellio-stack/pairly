# This file is kept for backwards compatibility
# The actual server is now in main.py
# Import and expose the main app

from backend.main import app

__all__ = ["app"]