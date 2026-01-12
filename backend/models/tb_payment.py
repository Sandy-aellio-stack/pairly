from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    RAZORPAY = "razorpay"


class TBPayment(Document):
    """Payment record for credit purchases"""
    user_id: Indexed(str)
    amount_inr: int
    credits_purchased: int
    provider: PaymentProvider = PaymentProvider.STRIPE
    provider_order_id: str
    provider_payment_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Webhook tracking for idempotency
    webhook_event_id: Optional[str] = None

    class Settings:
        name = "tb_payments"
        indexes = [
            # User payment history
            [("user_id", 1), ("created_at", -1)],
            # Provider order lookup (unique)
            [("provider_order_id", 1)],
            # Provider payment lookup
            [("provider_payment_id", 1)],
            # Status filtering
            [("status", 1), ("created_at", -1)],
        ]


# Credit packages - ordered by highest discount first (best value first)
# Premium: 1000 coins for ₹800 = ₹0.80/coin (20% discount)
# Popular: 500 coins for ₹450 = ₹0.90/coin (10% discount)
# Starter: 100 coins for ₹100 = ₹1.00/coin (0% discount)
CREDIT_PACKAGES = [
    {"id": "premium", "credits": 1000, "amount_inr": 800, "label": "Premium", "discount": 20, "popular": True},
    {"id": "popular", "credits": 500, "amount_inr": 450, "label": "Popular", "discount": 10, "popular": False},
    {"id": "starter", "credits": 100, "amount_inr": 100, "label": "Starter", "discount": 0, "popular": False},
]
