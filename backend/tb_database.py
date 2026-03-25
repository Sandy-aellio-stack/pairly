from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
import certifi

# Luveloop Models
from backend.models.tb_user import TBUser
from backend.models.tb_credit import TBCreditTransaction
from backend.models.tb_message import TBMessage, TBConversation
from backend.models.tb_payment import TBPayment
from backend.models.tb_otp import TBOTP
from backend.models.app_settings import AppSettings
from backend.models.tb_report import TBReport
from backend.models.user_block import UserBlock
from backend.models.tb_notification import TBNotification
from backend.models.webhook_event import WebhookEvent, WebhookDLQ
from backend.models.user import User as LegacyUser
from backend.models.tb_pending_session import PendingSession
from backend.models.call_session_v2 import CallSessionV2
from backend.models.notification import Notification

from backend.config import settings

MONGO_URL = settings.MONGODB_URI

# Parse MongoDB URL to add authSource if missing
def _prepare_mongo_url(url: str) -> str:
    """Add authSource to MongoDB URL if not present"""
    if "authSource" not in url:
        # Add authSource=admin for Atlas connections
        if "mongodb.net" in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}authSource=admin"
    return url

async def init_db():
    """Initialize MongoDB connection with Beanie ODM"""
    import logging
    global MONGO_URL

    if not MONGO_URL:
        logging.warning("MONGO_URL is not set — database operations will be unavailable. Set the MONGO_URL secret to enable full functionality.")
        return None

    MONGO_URL = _prepare_mongo_url(MONGO_URL)
    
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
        # Handle MongoDB Atlas URLs that may not have db name before query params
        db_name = "truebond"
        if "/" in MONGO_URL:
            path_part = MONGO_URL.split("?")[0]  # Remove query params first
            last_segment = path_part.split("/")[-1]
            if last_segment and last_segment != "":
                db_name = last_segment
        
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
                UserBlock,
                TBNotification,
                WebhookEvent,
                WebhookDLQ,
                LegacyUser,
                PendingSession,
                CallSessionV2,
                Notification,
            ]
        )
        
        import logging
        logging.info("MongoDB connected successfully")
        return client
    except Exception as e:
        import logging
        import traceback
        logging.error(f"CRITICAL: MongoDB connection failed: {e}")
        logging.error(f"Connection URL (masked): {MONGO_URL[:30]}...")
        traceback.print_exc()
        raise RuntimeError(f"Could not connect to MongoDB: {e}")

async def close_db(client):
    """Close MongoDB connection"""
    if client:
        client.close()
        print("MongoDB connection closed")


# Global client reference for direct database access
_mongo_client = None


async def get_database():
    """Get MongoDB database instance for direct access"""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = await init_db()
    return _mongo_client["truebond"]
