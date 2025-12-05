"""Subscription tier and state models.

Usage:
    - SubscriptionTier: Creator-defined pricing tiers
    - SubscriptionState: User's active subscription status
    - Supports both Stripe and Razorpay
    - Dual-mode with credits system (feature flag controlled)
"""
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class BillingInterval(str, Enum):
    MONTH = "month"
    YEAR = "year"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class SubscriptionTier(Document):
    """Creator-defined subscription tier."""
    
    creator_id: PydanticObjectId
    tier_id: str  # Unique identifier for this tier
    name: str  # e.g., "Silver", "Gold", "Platinum"
    price_cents: int  # Price in cents (e.g., 999 = $9.99)
    currency: str = "usd"  # ISO currency code
    interval: BillingInterval = BillingInterval.MONTH
    benefits: List[str] = Field(default_factory=list)  # List of perks
    
    # Payment provider IDs
    stripe_product_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
    razorpay_plan_id: Optional[str] = None
    
    # Status
    active: bool = True
    is_default: bool = False  # Highlight as recommended tier
    max_subscribers: Optional[int] = None  # Optional cap
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "subscription_tiers"
        indexes = [
            [("creator_id", 1), ("active", 1)],
            [("tier_id", 1)],
        ]


class SubscriptionState(BaseModel):
    """User's subscription state (Pydantic model for embedding/API responses)."""
    
    user_id: PydanticObjectId
    subscription_tier_id: PydanticObjectId
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    current_period_end: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    
    # Payment provider references
    stripe_subscription_id: Optional[str] = None
    razorpay_subscription_id: Optional[str] = None


class UserSubscription(Document):
    """User's active subscription to a creator (Document for persistence)."""
    
    user_id: PydanticObjectId
    creator_id: PydanticObjectId
    subscription_tier_id: PydanticObjectId
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    current_period_start: datetime
    current_period_end: datetime
    
    # Payment provider references
    stripe_subscription_id: Optional[str] = None
    razorpay_subscription_id: Optional[str] = None
    
    # Cancellation
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_subscriptions"
        indexes = [
            [("user_id", 1), ("status", 1)],
            [("creator_id", 1), ("status", 1)],
            [("stripe_subscription_id", 1)],
            [("razorpay_subscription_id", 1)],
        ]
