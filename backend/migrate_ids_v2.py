import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from bson import ObjectId
from dotenv import load_dotenv
from pathlib import Path
import re

async def migrate_ids():
    # Load .env
    env_path = Path(".env")
    if not env_path.exists():
        env_path = Path(__file__).parent / ".env"
    
    load_dotenv(dotenv_path=env_path)
    
    mongo_url = os.getenv("MONGO_URL") or "mongodb://localhost:27017"
    db_name = "truebond" 
    match = re.search(r"/([^/?]+)(\?|$)", mongo_url)
    if match:
        db_name = match.group(1)
            
    print(f"Connecting to: {mongo_url.split('@')[-1] if '@' in mongo_url else mongo_url}")
    print(f"Migrating 'user_blocks' and 'tb_reports' in DB '{db_name}'...")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Migrate user_blocks
    print("Migrating user_blocks...")
    blocks_cursor = db.user_blocks.find({})
    block_count = 0
    async for block in blocks_cursor:
        updates = {}
        if isinstance(block.get("blocker_id"), str) and len(block["blocker_id"]) == 24:
            updates["blocker_id"] = ObjectId(block["blocker_id"])
        if isinstance(block.get("blocked_id"), str) and len(block["blocked_id"]) == 24:
            updates["blocked_id"] = ObjectId(block["blocked_id"])
        
        if updates:
            await db.user_blocks.update_one({"_id": block["_id"]}, {"$set": updates})
            block_count += 1
    print(f"Migrated {block_count} user_blocks.")

    # Migrate tb_reports
    print("Migrating tb_reports...")
    reports_cursor = db.tb_reports.find({})
    report_count = 0
    async for report in reports_cursor:
        updates = {}
        if isinstance(report.get("reported_user_id"), str) and len(report["reported_user_id"]) == 24:
            updates["reported_user_id"] = ObjectId(report["reported_user_id"])
        if isinstance(report.get("reported_by_user_id"), str) and len(report["reported_by_user_id"]) == 24:
            updates["reported_by_user_id"] = ObjectId(report["reported_by_user_id"])
        
        if updates:
            await db.tb_reports.update_one({"_id": report["_id"]}, {"$set": updates})
            report_count += 1
    print(f"Migrated {report_count} tb_reports.")

    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate_ids())
