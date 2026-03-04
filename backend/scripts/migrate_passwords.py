import asyncio
import os
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def migrate_passwords():
    mongo_url = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI")
    if not mongo_url:
        print("ERROR: MONGO_URL or MONGODB_URI not found in environment")
        return

    client = AsyncIOMotorClient(mongo_url)
    # Extract db name
    db_name = "truebond"
    if "/" in mongo_url:
        path_part = mongo_url.split("?")[0]
        last_segment = path_part.split("/")[-1]
        if last_segment:
            db_name = last_segment
    
    db = client[db_name]
    collection = db.tb_users
    
    print(f"Connected to database: {db_name}")
    
    cursor = collection.find({})
    users = await cursor.to_list(length=None)
    
    print(f"Found {len(users)} users in {collection.name}")
    
    fixed_count = 0
    invalid_count = 0
    consistent_count = 0
    
    for user in users:
        user_id = user.get("_id")
        email = user.get("email")
        pwd_hash = user.get("password_hash")
        
        if not pwd_hash:
            print(f"User {email} has no password hash!")
            invalid_count += 1
            continue
            
        # Check if it's a valid bcrypt hash
        is_valid = False
        try:
            # passlib identifies bcrypt hashes starting with $2a$, $2b$, or $2y$
            if pwd_hash.startswith(("$2a$", "$2b$", "$2y$")) and len(pwd_hash) >= 59:
                is_valid = True
                consistent_count += 1
            else:
                print(f"Invalid hash format for user {email}: {pwd_hash[:10]}...")
                invalid_count += 1
                
                # If it looks like plain text (not starting with $ and short), maybe we can't fix it automatically 
                # unless we know it's plain text.
                # BUT the user said "Identify users with invalid or plain-text passwords."
                # If it IS plain text, we SHOULD re-hash it.
                
                if not pwd_hash.startswith("$") and len(pwd_hash) < 50:
                    print(f"  -> Detected possible plain-text password for {email}. Re-hashing...")
                    new_hash = pwd_context.hash(pwd_hash)
                    await collection.update_one({"_id": user_id}, {"$set": {"password_hash": new_hash}})
                    fixed_count += 1
                else:
                    print(f"  -> Hash format unknown for {email}. Cannot automatically fix without plain text.")
                    
        except Exception as e:
            print(f"Error processing user {email}: {e}")
            invalid_count += 1
            
    print("\nMigration Summary:")
    print(f"Total users scanned: {len(users)}")
    print(f"Consistent hashes ($2b$/$2a$): {consistent_count}")
    print(f"Invalid/Non-standard hashes: {invalid_count}")
    print(f"Successfully re-hashed (plain-text): {fixed_count}")
    print("\nNOTE: Users with non-standard hashes that were NOT plain-text will still need a password reset or legacy migration.")

if __name__ == "__main__":
    asyncio.run(migrate_passwords())
