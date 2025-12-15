from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class TransactionReason(str, Enum):
    SIGNUP_BONUS = "signup_bonus"
    MESSAGE_SENT = "message_sent"
    CREDIT_PURCHASE = "credit_purchase"
    REFUND = "refund"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class TBCreditTransaction(Document):
    """Credit transaction log"""
    user_id: Indexed(str)
    amount: int  # positive for credit, negative for debit
    reason: TransactionReason
    balance_after: int
    reference_id: Optional[str] = None  # payment_id, message_id, etc.
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tb_credit_transactions"
