"""Payment and subscription models for hybrid payment system.

Supports both:
- Credits system (existing)
- Subscription tiers (new)

Providers:
- Stripe (global)
- Razorpay (India)
"""
from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    RAZORPAY = "razorpay"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class PaymentMethod(Document):
    """User's saved payment method."""
    
    user_id: PydanticObjectId
    provider: PaymentProvider
    provider_payment_method_id: str  # Stripe: pm_xxx, Razorpay: method_xxx
    
    # Card details (masked)
    last4: Optional[str] = None
    brand: Optional[str] = None  # visa, mastercard, etc.
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    
    is_default: bool = False
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "payment_methods"
        indexes = [
            [("user_id", 1), ("is_default", -1)],
            [("provider_payment_method_id", 1)],
        ]


class UserSubscription(Document):
    """User's active subscription to a creator tier."""
    
    user_id: PydanticObjectId
    tier_id: PydanticObjectId  # Reference to SubscriptionTier
    creator_id: PydanticObjectId  # Denormalized for queries
    
    # Provider details
    provider: PaymentProvider
    provider_subscription_id: str  # Stripe: sub_xxx, Razorpay: sub_xxx
    provider_customer_id: Optional[str] = None  # Stripe: cus_xxx
    
    # Status
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    
    # Billing period
    current_period_start: datetime
    current_period_end: datetime
    
    # Cancellation
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    
    # Payment tracking
    last_payment_at: Optional[datetime] = None
    last_payment_amount: Optional[int] = None  # in cents
    
    # Trial
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_subscriptions"
        indexes = [
            [("user_id", 1), ("status", 1)],
            [("creator_id", 1), ("status", 1)],
            [("tier_id", 1)],
            [("provider_subscription_id", 1)],
            [("provider", 1), ("provider_subscription_id", 1)],
        ]


class Payment(Document):
    """Payment transaction record."""
    
    user_id: PydanticObjectId
    
    # Payment details
    provider: PaymentProvider
    provider_payment_id: str  # Stripe: pi_xxx or in_xxx, Razorpay: pay_xxx
    amount_cents: int
    currency: str = "usd"
    
    # Type
    payment_type: str  # 'subscription', 'credits', 'payout'
    
    # Related entities
    subscription_id: Optional[PydanticObjectId] = None
    tier_id: Optional[PydanticObjectId] = None
    
    # Status
    status: str  # 'succeeded', 'failed', 'pending', 'refunded'
    
    # Timestamps
    paid_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "payments"
        indexes = [
            [("user_id", 1), ("created_at", -1)],
            [("provider_payment_id", 1)],
            [("subscription_id", 1)],
            [("payment_type", 1), ("status", 1)],
        ]


class WebhookEvent(Document):
    """Webhook event log for idempotency."""
    
    provider: PaymentProvider
    provider_event_id: str  # Unique event ID from provider
    event_type: str
    
    processed: bool = False
    processed_at: Optional[datetime] = None
    
    # Raw payload for debugging
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Error tracking
    error: Optional[str] = None
    retry_count: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "webhook_events"
        indexes = [
            [("provider", 1), ("provider_event_id", 1)],  # Unique constraint
            [("processed", 1), ("created_at", -1)],
        ]
