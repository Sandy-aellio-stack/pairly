from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from enum import Enum
from typing import Optional

class PayoutStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"

class Payout(Document):
    creator_id: PydanticObjectId
    amount_credits: int
    amount_usd: float
    status: PayoutStatus = PayoutStatus.PENDING
    payment_method: str = "bank_transfer"
    payment_details: dict = Field(default_factory=dict)
    admin_notes: Optional[str] = None
    approved_by: Optional[PydanticObjectId] = None
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "payouts"