import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from bson import ObjectId
from dotenv import load_dotenv
from pathlib import Path
import re

async def check_ids():
    # Load .env from current directory or parent
    env_path = Path(".env")
    if not env_path.exists():
        env_path = Path(__file__).parent / ".env"
    
    load_dotenv(dotenv_path=env_path)
    
    mongo_url = os.getenv("MONGO_URL") or "mongodb://localhost:27017"
    
    # Simple extraction of DB name
    db_name = "truebond" 
    match = re.search(r"/([^/?]+)(\?|$)", mongo_url)
    if match:
        db_name = match.group(1)
            
    print(f"Connecting to: {mongo_url.split('@')[-1] if '@' in mongo_url else mongo_url}")
    print(f"Checking collection 'tb_users' in DB '{db_name}'...")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        cursor = db.tb_users.find({}, {"_id": 1, "name": 1, "email": 1})
        count = 0
        non_oid_count = 0
        async for doc in cursor:
            count += 1
            _id = doc["_id"]
            if not isinstance(_id, ObjectId):
                non_oid_count += 1
                print(f"WARNING: User '{doc.get('name')}' ({doc.get('email')}) has non-ObjectId _id: {_id} (type: {type(_id)})")
            # else:
            #    print(f"OK: {doc.get('name')} -> {str(_id)}")
        
        print(f"Checked {count} users. Found {non_oid_count} non-ObjectId _ids.")
    except Exception as e:
        print(f"Error checking IDs: {e}")

    print("Check complete.")

if __name__ == "__main__":
    asyncio.run(check_ids())
