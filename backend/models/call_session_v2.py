from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

class CallStatus(str, Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    CONNECTED = "connected"
    ENDED = "ended"
    MISSED = "missed"
    REJECTED = "rejected"
    FAILED = "failed"

class CallSessionV2(Document):
    id: str = Field(...)
    caller_id: str = Field(...)
    receiver_id: str = Field(...)
    status: CallStatus = Field(default=CallStatus.INITIATED)
    
    # Timestamps
    initiated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ringing_at: Optional[datetime] = None
    connected_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Duration and billing
    duration_seconds: int = Field(default=0)
    credits_per_minute: int = Field(default=10)
    credits_spent: int = Field(default=0)
    credits_transaction_id: Optional[str] = None
    
    # WebRTC signaling data (mock)
    sdp_offer: Optional[str] = None
    sdp_answer: Optional[str] = None
    ice_candidates_caller: List[Dict[str, Any]] = Field(default_factory=list)
    ice_candidates_receiver: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Additional metadata
    call_quality: Optional[str] = None  # excellent/good/fair/poor
    disconnect_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "call_sessions_v2"
        indexes = [
            "caller_id",
            "receiver_id",
            "status",
            "created_at",
            [("caller_id", 1), ("status", 1)],
            [("receiver_id", 1), ("status", 1)],
            [("created_at", -1)]
        ]
    
    def calculate_cost(self) -> int:
        """Calculate cost in credits (ceiling per minute)"""
        if self.duration_seconds > 0:
            minutes = (self.duration_seconds + 59) // 60  # Ceiling
            return minutes * self.credits_per_minute
        return 0
    
    def update_status(self, new_status: CallStatus):
        """Update call status with timestamp tracking"""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        
        if new_status == CallStatus.RINGING:
            self.ringing_at = self.updated_at
        elif new_status == CallStatus.CONNECTED:
            self.connected_at = self.updated_at
        elif new_status in [CallStatus.ENDED, CallStatus.MISSED, CallStatus.REJECTED, CallStatus.FAILED]:
            self.ended_at = self.updated_at
            if self.connected_at:
                self.duration_seconds = int((self.ended_at - self.connected_at).total_seconds())
                self.credits_spent = self.calculate_cost()
