import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["ENVIRONMENT"] = "development"
os.environ["JWT_SECRET"] = os.getenv("JWT_SECRET", "test_secret")
os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")

from backend.tb_database import init_db
from backend.services.tb_message_service import MessageService, SendMessageRequest
from backend.models.tb_user import TBUser

async def run():
    print("Initializing DB...")
    await init_db()
    
    users = await TBUser.find().limit(2).to_list()
    if len(users) < 2:
        print("Need 2 users to test")
        return
        
    sender = users[0]
    receiver = users[1]
    
    print(f"Sender: {sender.id}, Receiver: {receiver.id}")
    
    try:
        req = SendMessageRequest(
            receiver_id=str(receiver.id),
            content="Hello world test",
            message_type="text"
        )
        print("Sending message...")
        result = await MessageService.send_message(str(sender.id), req)
        print("SUCCESS!", result)
    except Exception as e:
        import traceback
        print("CAUGHT EXCEPTION!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
