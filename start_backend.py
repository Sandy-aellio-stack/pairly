#!/usr/bin/env python3
"""
Simple backend starter script
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

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
    sys.exit(1)
