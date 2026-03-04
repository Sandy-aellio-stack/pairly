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

print("="*50)
print("Environment variables loaded:")
print(f"  ENVIRONMENT: {os.getenv('ENVIRONMENT', 'not set')}")
print(f"  MONGO_URL: {os.getenv('MONGO_URL', 'not set')[:50]}...")
print(f"  REDIS_URL: {os.getenv('REDIS_URL', 'not set')[:50]}...")
print("="*50)

try:
    import uvicorn
    from backend.main import socket_app

    print("Starting TrueBond Backend...")
    print("Backend will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/api/health")
    print("\nPress Ctrl+C to stop")

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
