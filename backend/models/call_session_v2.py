from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

class CallStatus(str, Enum):
    RINGING = "ringing"
    ACCEPTED = "accepted"
    ENDED = "ended"
    MISSED = "missed"
    REJECTED = "rejected"

class CallSessionV2(Document):
    id: str = Field(...)
    caller_id: str = Field(..., index=True)
    receiver_id: str = Field(..., index=True)
    status: CallStatus = Field(default=CallStatus.RINGING)
    
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: int = Field(default=0)
    
    credits_per_minute: int = Field(default=10)
    credits_spent: int = Field(default=0)
    credits_transaction_id: Optional[str] = None
    
    signaling_data: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "call_sessions_v2"
        indexes = ["caller_id", "receiver_id", "status", "created_at"]
    
    def calculate_cost(self) -> int:
        if self.duration_seconds > 0:
            minutes = (self.duration_seconds + 59) // 60
            return minutes * self.credits_per_minute
        return 0
