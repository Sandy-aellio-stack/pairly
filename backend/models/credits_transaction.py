from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from enum import Enum
from typing import Optional


class TransactionType(str, Enum):
    # Credits added
    PURCHASE = "purchase"  # User purchased credits
    ADMIN_GRANT = "admin_grant"  # Admin manually added credits
    REFUND = "refund"  # Refund from failed/disputed transaction
    BONUS = "bonus"  # Promotional bonus
    
    # Credits spent
    MESSAGE = "message"  # Spent on messaging
    CALL = "call"  # Spent on calling
    TIP = "tip"  # Tipped a creator
    UNLOCK = "unlock"  # Unlocked premium content
    SUBSCRIPTION = "subscription"  # Subscription payment
    
    # Credits removed
    ADMIN_DEDUCT = "admin_deduct"  # Admin penalty
    EXPIRED = "expired"  # Credits expired


class TransactionStatus(str, Enum):
    PENDING = "pending"  # Transaction initiated but not confirmed
    COMPLETED = "completed"  # Transaction successful
    FAILED = "failed"  # Transaction failed
    REVERSED = "reversed"  # Transaction was reversed/refunded


class CreditsTransaction(Document):
    """Credit ledger - immutable record of all credit movements."""
    
    user_id: PydanticObjectId
    amount: int  # positive for credits added, negative for credits spent
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.COMPLETED
    balance_before: int  # Balance before this transaction
    balance_after: int  # Balance after this transaction
    description: str
    
    # Idempotency
    idempotency_key: Optional[str] = None  # Unique key to prevent duplicate transactions
    
    # Related entities
    related_user_id: Optional[PydanticObjectId] = None  # e.g., creator receiving tip
    related_entity_type: Optional[str] = None  # "message", "post", "call", etc.
    related_entity_id: Optional[str] = None
    
    # Payment info (for purchases)
    payment_provider: Optional[str] = None  # "stripe", "razorpay"
    payment_id: Optional[str] = None  # Provider's transaction ID
    payment_amount_cents: Optional[int] = None  # Amount paid in cents
    payment_currency: Optional[str] = None  # "USD", "INR"
    
    # Metadata
    metadata: Optional[dict] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "credits_transactions"
        indexes = [
            [("user_id", 1), ("created_at", -1)],  # User transaction history
            [("idempotency_key", 1)],  # Idempotency checks
            [("payment_id", 1)],  # Payment lookups
            [("status", 1), ("created_at", -1)],  # Pending transactions
        ]
