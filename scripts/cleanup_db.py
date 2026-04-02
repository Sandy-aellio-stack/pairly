import asyncio
import os
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.models.tb_user import TBUser
from backend.tb_database import init_db

async def cleanup():
    print("🚀 Starting database cleanup...")
    
    # Initialize DB connection
    await init_db()
    
    # 1. Delete users with 'test' in email (regex)
    import re
    test_email_regex = re.compile(r"test", re.IGNORECASE)
    
    test_users = await TBUser.find({"email": test_email_regex}).to_list()
    test_user_ids = [str(u.id) for u in test_users]
    
    if test_users:
        print(f"🗑️ Found {len(test_users)} users with 'test' in email: {test_user_ids}")
        delete_result = await TBUser.find({"email": test_email_regex}).delete()
        print(f"✅ Deleted {delete_result.deleted_count} test users.")
    else:
        print("ℹ️ No users with 'test' in email found.")

    # 2. Delete specific "Test User" name
    name_test_users = await TBUser.find({"name": "Test User"}).delete()
    if name_test_users.deleted_count > 0:
        print(f"✅ Deleted {name_test_users.deleted_count} users named 'Test User'.")

    # 3. Optional: Delete users with 'is_test: true' if the field exists dynamically
    # (Beanie/Pydantic might not show it in the model but it could be in DB)
    raw_collection = TBUser.get_motor_collection()
    test_field_result = await raw_collection.delete_many({"is_test": True})
    if test_field_result.deleted_count > 0:
        print(f"✅ Deleted {test_field_result.deleted_count} users with is_test=True.")

    print("🏁 Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(cleanup())
