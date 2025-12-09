from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum


class WebhookEventStatus(str, Enum):
    """Webhook event processing status"""
    PENDING = "pending"  # Received but not processed
    PROCESSED = "processed"  # Successfully processed
    FAILED = "failed"  # Processing failed
    RETRYING = "retrying"  # Being retried


class WebhookEventType(str, Enum):
    """Supported webhook event types"""
    # Stripe events
    STRIPE_PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    STRIPE_PAYMENT_INTENT_FAILED = "payment_intent.failed"
    STRIPE_PAYMENT_INTENT_PROCESSING = "payment_intent.processing"
    STRIPE_CHARGE_REFUNDED = "charge.refunded"
    
    # Razorpay events
    RAZORPAY_PAYMENT_CAPTURED = "payment.captured"
    RAZORPAY_PAYMENT_FAILED = "payment.failed"
    RAZORPAY_REFUND_CREATED = "refund.created"
    
    # Generic
    UNKNOWN = "unknown"


class WebhookEvent(Document):
    """Webhook event model - tracks all incoming webhooks"""
    
    # Core fields
    id: str = Field(...)  # Our internal ID
    provider: str = Field(...)  # "stripe" or "razorpay"
    event_id: str = Field(..., index=True)  # Provider's event ID
    event_type: str = Field(...)  # Event type (e.g., "payment_intent.succeeded")
    
    # Payload
    raw_payload: Dict[str, Any] = Field(...)  # Complete webhook payload
    signature_header: Optional[str] = None  # Signature from webhook headers
    
    # Processing
    status: WebhookEventStatus = Field(default=WebhookEventStatus.PENDING)
    processed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    retry_count: int = Field(default=0)
    
    # Idempotency
    idempotency_key: str = Field(..., index=True, unique=True)  # Prevent duplicate processing
    
    # Related entities
    payment_intent_id: Optional[str] = None  # Our internal payment intent ID
    provider_payment_id: Optional[str] = None  # Provider's payment/order ID
    
    # Timestamps
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    webhook_timestamp: Optional[datetime] = None  # Timestamp from webhook payload
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "webhook_events"
        indexes = [
            "event_id",
            "idempotency_key",
            "provider",
            "event_type",
            "status",
            "payment_intent_id",
            "created_at",
        ]
    
    def mark_processed(self, payment_intent_id: Optional[str] = None):
        """Mark webhook as successfully processed"""
        self.status = WebhookEventStatus.PROCESSED
        self.processed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        if payment_intent_id:
            self.payment_intent_id = payment_intent_id
    
    def mark_failed(self, error: str):
        """Mark webhook as failed"""
        self.status = WebhookEventStatus.FAILED
        self.processing_error = error
        self.updated_at = datetime.now(timezone.utc)
    
    def increment_retry(self):
        """Increment retry counter"""
        self.retry_count += 1
        self.status = WebhookEventStatus.RETRYING
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "provider": self.provider,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "status": self.status,
            "payment_intent_id": self.payment_intent_id,
            "retry_count": self.retry_count,
            "received_at": self.received_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_error": self.processing_error,
        }


class WebhookDLQ(Document):
    """Dead Letter Queue for failed webhook events"""
    
    # Reference to original webhook event
    webhook_event_id: str = Field(..., index=True)
    event_id: str = Field(...)  # Provider's event ID
    provider: str = Field(...)
    event_type: str = Field(...)
    
    # Failure details
    error_reason: str = Field(...)
    error_details: Optional[Dict[str, Any]] = None
    
    # Retry tracking
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    last_retry_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    
    # Raw data for retry
    raw_payload: Dict[str, Any] = Field(...)
    signature_header: Optional[str] = None
    
    # Status
    resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "webhook_dlq"
        indexes = [
            "webhook_event_id",
            "event_id",
            "provider",
            "resolved",
            "created_at",
        ]
    
    def can_retry(self) -> bool:
        """Check if event can be retried"""
        return not self.resolved and self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry counter"""
        from datetime import timedelta
        self.retry_count += 1
        self.last_retry_at = datetime.now(timezone.utc)
        # Exponential backoff: 1 min, 5 min, 30 min
        backoff_minutes = [1, 5, 30][min(self.retry_count - 1, 2)]
        self.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=backoff_minutes)
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_resolved(self, notes: Optional[str] = None):
        """Mark as resolved"""
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        self.resolution_notes = notes
        self.updated_at = datetime.now(timezone.utc)
