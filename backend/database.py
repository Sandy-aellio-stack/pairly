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
from backend.models.subscription import SubscriptionTier, UserSubscription as LegacyUserSubscription
from backend.models.payment_subscription import UserSubscription, PaymentMethod
from backend.routes.compliance import Report
from backend.models.call_session import CallSession
from backend.models.user_preferences import UserPreferences
from backend.models.match_feedback import MatchFeedback
from backend.models.match_recommendation import MatchRecommendation
from backend.models.admin_audit_log import AdminAuditLog
from backend.models.admin_session import AdminSession
from backend.models.analytics_snapshot import AnalyticsSnapshot
from backend.models.payment_intent import PaymentIntent
from backend.models.webhook_event import WebhookEvent, WebhookDLQ
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
            LegacyUserSubscription,
            UserSubscription,
            PaymentMethod,
            Report,
            CallSession,
            UserPreferences,
            MatchFeedback,
            MatchRecommendation,
            AdminAuditLog,
            AdminSession,
            AnalyticsSnapshot,
            PaymentIntent  # Phase 8.1: Payment Intent model
        ]
    )