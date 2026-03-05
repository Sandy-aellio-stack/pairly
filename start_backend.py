#!/usr/bin/env python3
"""
Simple backend starter script
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Load environment variables from backend/.env file
from dotenv import load_dotenv
# Try loading from backend directory first, then root
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fallback to root .env
    load_dotenv()

print("Environment variables loaded")

try:
    import uvicorn
    from backend.main import socket_app
    
    # We depend on main.py to log MongoDB and Redis connection status
    # because they happen during lifespan startup.
    
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
except ImportError as e:
    print(f"Error: Missing dependencies - {e}")
    print("\nPlease install dependencies:")
    print("  cd backend && pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting backend: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
