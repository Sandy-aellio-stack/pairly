#!/usr/bin/env python3
"""
Add credits to test users for messaging V2 testing
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.database import init_db
from backend.models.user import User
from backend.services.credits_service_v2 import CreditsServiceV2

async def add_credits_to_users():
    """Add credits to test users"""
    await init_db()
    
    credits_service = CreditsServiceV2()
    
    # Test user emails
    test_emails = [
        "sender@pairly.com",
        "receiver@pairly.com", 
        "admin@pairly.com"
    ]
    
    for email in test_emails:
        try:
            user = await User.find_one(User.email == email)
            if user:
                print(f"Found user: {email} (ID: {user.id})")
                
                # Check current balance
                current_balance = user.credits_balance
                print(f"  Current balance: {current_balance}")
                
                if current_balance < 20:
                    # Add credits
                    credits_to_add = 50
                    transaction_id = await credits_service.add_credits(
                        user_id=str(user.id),
                        amount=credits_to_add,
                        description="Test credits for messaging V2",
                        transaction_type="admin_grant"
                    )
                    print(f"  Added {credits_to_add} credits (Transaction: {transaction_id})")
                    
                    # Verify new balance
                    updated_user = await User.get(user.id)
                    print(f"  New balance: {updated_user.credits_balance}")
                else:
                    print(f"  User already has sufficient credits")
            else:
                print(f"User not found: {email}")
        except Exception as e:
            print(f"Error processing {email}: {e}")

if __name__ == "__main__":
    asyncio.run(add_credits_to_users())