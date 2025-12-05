"""Call Session Model - WebRTC call records and state management."""

from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from enum import Enum
from typing import Optional


class CallStatus(str, Enum):
    INITIATING = "initiating"  # Call offer sent
    RINGING = "ringing"  # Receiver notified
    ACCEPTED = "accepted"  # Receiver accepted
    ACTIVE = "active"  # Call in progress
    ENDED = "ended"  # Normal end
    REJECTED = "rejected"  # Receiver rejected
    CANCELLED = "cancelled"  # Caller cancelled
    FAILED = "failed"  # Technical failure
    INSUFFICIENT_CREDITS = "insufficient_credits"  # Auto-ended due to no credits


class CallSession(Document):
    """Record of a WebRTC call session."""
    
    # Participants
    caller_id: PydanticObjectId
    receiver_id: PydanticObjectId
    
    # Call state
    status: CallStatus = CallStatus.INITIATING
    
    # Timestamps
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None  # When media started flowing
    ended_at: Optional[datetime] = None
    
    # Duration and billing
    duration_seconds: int = 0  # Total call duration
    billed_seconds: int = 0  # Seconds billed so far
    cost_per_minute: int = 5  # Credits per minute
    total_cost: int = 0  # Total credits charged
    
    # Signaling
    offer_sdp: Optional[str] = None
    answer_sdp: Optional[str] = None
    ice_candidates: list = Field(default_factory=list)  # ICE candidates exchanged
    
    # Metadata
    end_reason: Optional[str] = None  # Why call ended
    quality_rating: Optional[int] = None  # User quality rating (1-5)
    flagged_for_moderation: bool = False
    moderation_notes: Optional[str] = None
    
    # Technical info
    caller_ip: Optional[str] = None
    receiver_ip: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "call_sessions"
        indexes = [
            [("caller_id", 1), ("created_at", -1)],  # Caller history
            [("receiver_id", 1), ("created_at", -1)],  # Receiver history
            [("status", 1), ("started_at", 1)],  # Active calls
            [("flagged_for_moderation", 1)],  # Moderation queue
        ]
