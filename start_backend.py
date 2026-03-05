#!/usr/bin/env python3
"""
TrueBond Backend Starter Script
Optimized for PM2 and local development.
"""
import sys
import os

# Ensure the project root is in the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(ROOT_DIR, 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

print("Environment variables loaded")

try:
    import uvicorn
    # Use the import string format for uvicorn to support reload/workers and PM2 better
    # backend.main:socket_app refers to the socket_app object in backend/main.py
    
    uvicorn.run(
        "backend.main:socket_app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
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
