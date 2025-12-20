from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
import certifi

# TrueBond Models
from backend.models.tb_user import TBUser
from backend.models.tb_credit import TBCreditTransaction
from backend.models.tb_message import TBMessage, TBConversation
from backend.models.tb_payment import TBPayment
from backend.models.tb_otp import TBOTP
from backend.models.app_settings import AppSettings
from backend.models.tb_report import TBReport
from backend.routes.tb_notifications import TBNotification

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/truebond")

async def init_db():
    """Initialize MongoDB connection with Beanie ODM"""
    try:
        client = AsyncIOMotorClient(
            MONGO_URL,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            tlsCAFile=certifi.where()
        )
        
        # Test connection with timeout
        await asyncio.wait_for(client.admin.command('ping'), timeout=3.0)
        
        # Get database name from URL or use default
        db_name = MONGO_URL.split("/")[-1].split("?")[0] if "/" in MONGO_URL else "truebond"
        if not db_name:
            db_name = "truebond"
        
        await init_beanie(
            database=client[db_name],
            document_models=[
                TBUser,
                TBCreditTransaction,
                TBMessage,
                TBConversation,
                TBPayment,
                TBOTP,
                AppSettings,
                TBReport,
                TBNotification
            ]
        )
        
        print(f"✅ Connected to MongoDB: {db_name}")
        return client
    except Exception as e:
        import traceback
        print(f"⚠️ MongoDB connection failed: {e}")
        print(f"⚠️ Connection URL (masked): {MONGO_URL[:30]}...")
        traceback.print_exc()
        print("⚠️ Starting without database - set MONGO_URL environment variable")
        return None

async def close_db(client):
    """Close MongoDB connection"""
    if client:
        client.close()
        print("❌ MongoDB connection closed")
