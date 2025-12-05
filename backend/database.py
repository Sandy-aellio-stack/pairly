from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.models.user import User
from backend.models.session import Session
from backend.models.device_fingerprint import DeviceFingerprint
from backend.models.fraud_alert import FraudAlert
from backend.models.failed_login import FailedLogin
from backend.models.audit_log import AuditLog
from backend.models.notification import Notification
from backend.models.otp import OTP
from backend.models.profile import Profile
from backend.models.message import Message
from backend.models.credits_transaction import CreditsTransaction
from backend.models.payout import Payout
from backend.models.post import Post
from backend.models.subscription import SubscriptionTier, UserSubscription
from backend.config import settings


async def init_db():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    # Extract database name from URI or use default
    database = client.get_database("pairly")

    await init_beanie(
        database=database,
        document_models=[
            User,
            Session,
            DeviceFingerprint,
            FraudAlert,
            FailedLogin,
            AuditLog,
            Notification,
            OTP,
            Profile,
            Message,
            CreditsTransaction,
            Payout,
            Post,
            SubscriptionTier,
            UserSubscription
        ]
    )