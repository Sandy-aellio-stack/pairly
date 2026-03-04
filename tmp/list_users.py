import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.models.tb_user import TBUser, Address, Preferences

async def main():
    mongo_url = "mongodb+srv://adminluveloop_db_user:50FS3kwzBKnVYPl@truebond.3uvme2o.mongodb.net/truebond?retryWrites=true&w=majority&authSource=admin"
    client = AsyncIOMotorClient(mongo_url)
    db_name = "truebond"
    
    await init_beanie(database=client[db_name], document_models=[TBUser])
    users = await TBUser.find_all().to_list()
    print(f"Found {len(users)} users:")
    for u in users:
        print(f"- Email: {u.email}, Mobile: {u.mobile_number}")

if __name__ == "__main__":
    asyncio.run(main())
