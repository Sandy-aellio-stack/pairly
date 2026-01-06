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

    class Settings:
        name = "tb_payments"
        indexes = [
            "user_id",
            "provider_order_id",
            "status",
            [("created_at", -1)]
        ]


# Credit packages - matching landing page pricing
CREDIT_PACKAGES = [
    {"id": "starter", "credits": 100, "amount_inr": 100, "label": "Starter"},
    {"id": "popular", "credits": 500, "amount_inr": 450, "label": "Popular"},
    {"id": "premium", "credits": 1000, "amount_inr": 800, "label": "Premium"},
]
