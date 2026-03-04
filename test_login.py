#!/usr/bin/env python3
"""Test login flow"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv('backend/.env')

print("="*50)
print("Testing Login Flow")
print("="*50)

from backend.tb_database import init_db
from backend.models.user import User as LegacyUser

async def test_legacy_user_lookup():
    """Check if user exists in legacy collection"""
    # Initialize DB first
    client = await init_db()
    if not client:
        print("ERROR: Could not connect to MongoDB")
        return False
        
    try:
        user = await LegacyUser.find_one({"email": "santhoshsandy9840@gmail.com"})
        if user:
            print(f"Legacy user found: {user.name}")
            print(f"Email: {user.email}")
            print(f"Credits: {user.credits_balance}")
            print(f"Password hash: {user.password_hash[:30]}...")
            return True
        else:
            print("Legacy user NOT found in 'users' collection")
            # Check tb_users
            from backend.models.tb_user import TBUser
            tb_user = await TBUser.find_one({"email": "santhoshsandy9840@gmail.com"})
            if tb_user:
                print(f"User found in tb_users: {tb_user.name}")
                print(f"Credits: {tb_user.credits_balance}")
                return True
            else:
                print("User NOT found in tb_users either")
                return False
    except Exception as e:
        print(f"Error looking up user: {e}")
        return False

# Check if user exists in legacy collection
result = asyncio.run(test_legacy_user_lookup())
print("="*50)
