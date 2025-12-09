from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
from enum import Enum


class PaymentProvider(str, Enum):
    """Supported payment providers"""
    STRIPE = "stripe"
    RAZORPAY = "razorpay"


class PaymentIntentStatus(str, Enum):
    """Payment intent lifecycle states"""
    PENDING = "pending"  # Intent created, awaiting payment
    PROCESSING = "processing"  # Payment being processed
    SUCCEEDED = "succeeded"  # Payment succeeded, credits added
    FAILED = "failed"  # Payment failed
    CANCELED = "canceled"  # Intent canceled before payment
    REQUIRES_ACTION = "requires_action"  # Requires user action (3DS, etc.)


class PaymentIntentMetadata(BaseModel):
    """Structured metadata for payment intents"""
    package_id: str
    credits_amount: int
    price_cents: int
    user_email: str
    fingerprint_id: Optional[str] = None
    risk_score: Optional[float] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


class PaymentIntent(Document):
    """Payment Intent model - tracks payment lifecycle"""
    
    # Core fields
    id: str = Field(...)  # Our internal ID (e.g., "pi_abc123")
    user_id: str = Field(..., index=True)  # User making the payment
    
    # Provider details
    provider: PaymentProvider = Field(...)
    provider_intent_id: Optional[str] = None  # External provider's ID (e.g., Stripe payment intent ID)
    provider_client_secret: Optional[str] = None  # For client-side confirmation
    
    # Payment details
    amount_cents: int = Field(..., ge=0)  # Amount in smallest currency unit
    currency: str = Field(default="INR")  # Currency code
    credits_amount: int = Field(..., ge=0)  # Credits to be added on success
    
    # Status tracking
    status: PaymentIntentStatus = Field(default=PaymentIntentStatus.PENDING)
    status_history: list[Dict[str, Any]] = Field(default_factory=list)  # Audit trail
    
    # Metadata
    metadata: PaymentIntentMetadata = Field(...)
    
    # Fraud & security
    idempotency_key: str = Field(..., index=True, unique=True)  # Prevent duplicate payments
    fingerprint_id: Optional[str] = None
    risk_score: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None  # When payment succeeded/failed
    
    # Provider response data (for debugging)
    provider_response: Optional[Dict[str, Any]] = None
    
    # Credits fulfillment
    credits_added: bool = Field(default=False)  # Track if credits were added
    credits_transaction_id: Optional[str] = None  # Link to CreditsTransaction
    
    class Settings:
        name = "payment_intents"
        indexes = [
            "user_id",
            "idempotency_key",
            "provider",
            "status",
            "created_at",
        ]
    
    def add_status_change(self, new_status: PaymentIntentStatus, reason: Optional[str] = None):
        """Record status change in history"""
        self.status_history.append({
            "from_status": self.status,
            "to_status": new_status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_completed(self, success: bool, reason: Optional[str] = None):
        """Mark payment as completed (success or failure)"""
        new_status = PaymentIntentStatus.SUCCEEDED if success else PaymentIntentStatus.FAILED
        self.add_status_change(new_status, reason)
        self.completed_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider,
            "provider_client_secret": self.provider_client_secret,
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "credits_amount": self.credits_amount,
            "status": self.status,
            "metadata": self.metadata.model_dump(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
