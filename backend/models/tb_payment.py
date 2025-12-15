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
    RAZORPAY = "razorpay"
    STRIPE = "stripe"


class TBPayment(Document):
    """Payment record for credit purchases"""
    user_id: Indexed(str)
    amount_inr: int  # Amount in INR (paise for Razorpay)
    credits_purchased: int
    provider: PaymentProvider = PaymentProvider.RAZORPAY
    provider_order_id: str  # Razorpay order_id
    provider_payment_id: Optional[str] = None  # Razorpay payment_id
    provider_signature: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "tb_payments"


# Credit packages
CREDIT_PACKAGES = [
    {"id": "pack_100", "credits": 50, "amount_inr": 100, "label": "₹100 - 50 Credits"},
    {"id": "pack_250", "credits": 150, "amount_inr": 250, "label": "₹250 - 150 Credits"},
    {"id": "pack_500", "credits": 350, "amount_inr": 500, "label": "₹500 - 350 Credits"},
    {"id": "pack_1000", "credits": 800, "amount_inr": 1000, "label": "₹1000 - 800 Credits"},
]
