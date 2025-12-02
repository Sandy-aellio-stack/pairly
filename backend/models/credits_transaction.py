from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from enum import Enum
from typing import Optional

class TransactionType(str, Enum):
    PURCHASE = "purchase"
    DEBIT = "debit"
    CREDIT = "credit"
    REFUND = "refund"
    PAYOUT = "payout"

class CreditsTransaction(Document):
    user_id: PydanticObjectId
    amount: int  # positive for credit, negative for debit
    transaction_type: TransactionType
    balance_after: int
    description: str
    metadata: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "credits_transactions"