from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class SubscriptionProvider(str, Enum):
    STRIPE = "stripe"
    RAZORPAY = "razorpay"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"

class UserSubscription(Document):
    user_id: Indexed(str)
    tier_id: Indexed(str)
    provider_subscription_id: Indexed(str)
    provider: SubscriptionProvider
    status: SubscriptionStatus = SubscriptionStatus.TRIALING
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    last_payment_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    class Settings:
        name = "user_subscriptions"
        indexes = [
            "user_id",
            "tier_id",
            "provider_subscription_id",
            ["user_id", "tier_id"],
            ["status", "current_period_end"]
        ]

class PaymentMethod(Document):
    user_id: Indexed(str)
    provider: SubscriptionProvider
    provider_payment_method_id: str
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    is_default: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    class Settings:
        name = "payment_methods"
        indexes = [
            "user_id",
            "provider_payment_method_id"
        ]
