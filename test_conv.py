import asyncio
import os
import sys
from pathlib import Path

# Setup sys.path
sys.path.append('c:\\Git\\pairly')

# Set env vars manually to avoid dotenv parsing errors
os.environ["MONGO_URL"] = "mongodb+srv://adminluveloop_db_user:50FS3kwzBKnVYPl@truebond.3uvme2o.mongodb.net/truebond?retryWrites=true&w=majority&authSource=admin"

from backend.tb_database import init_db, close_db
from backend.services.tb_message_service import MessageService
from backend.models.tb_user import TBUser
import time

async def main():
    print("Initializing DB...")
    client = await init_db()
    if not client:
        print("Failed to init db")
        return
        
    print("DB Initialized")
    
    test_user = await TBUser.find_one()
    if not test_user:
        print("No users found")
        await close_db(client)
        return
        
    print(f"Testing with user: {test_user.id} ({test_user.name})")
    
    start = time.time()
    try:
        convs = await MessageService.get_conversations(str(test_user.id))
        print(f"Success! Found {len(convs)} conversations.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
    finally:
        print(f"Time taken: {time.time() - start:.2f}s")
        await close_db(client)

if __name__ == "__main__":
    asyncio.run(main())
