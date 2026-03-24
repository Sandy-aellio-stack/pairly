import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_db():
    mongodb_url = "mongodb+srv://adminluveloop_db_user:50FS3kwzBKnVYPl@truebond.3uvme2o.mongodb.net/truebond?retryWrites=true&w=majority&authSource=admin"
    print(f"Connecting to DB...")
    client = AsyncIOMotorClient(mongodb_url)
    db = client.get_default_database()
    
    print("--- Conversations Sample ---")
    convs = await db.tb_conversations.find().limit(5).to_list(None)
    for c in convs:
        print(f"ID: {c['_id']} ({type(c['_id'])})")
        participants = c.get('participants', [])
        print(f"Participants: {participants}")
        if participants:
             print(f"  First Participant Type: {type(participants[0])}")
        print(f"Last Message: {c.get('last_message')} ({type(c.get('last_message'))})")
        print(f"Last Message At: {c.get('last_message_at')} ({type(c.get('last_message_at'))})")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_db())
