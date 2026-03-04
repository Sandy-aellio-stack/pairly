#!/usr/bin/env python3
"""Test backend MongoDB connection"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
load_dotenv(env_path)

print("="*50)
print("Testing MongoDB Connection")
print("="*50)
print(f"MONGO_URL: {os.getenv('MONGO_URL', 'not set')}")

import asyncio
from backend.tb_database import init_db

async def test():
    client = await init_db()
    if client:
        print("\n✓ MongoDB connected successfully!")
        return True
    else:
        print("\n✗ MongoDB connection failed!")
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
