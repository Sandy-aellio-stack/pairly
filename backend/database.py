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
from backend.config import settings


async def init_db():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = client.get_default_database()

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
            OTP
        ]
    )