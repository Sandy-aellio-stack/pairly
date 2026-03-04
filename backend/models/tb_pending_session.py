from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone, timedelta

class PendingSession(Document):
    """
    Tracks a login attempt from a new device that is waiting for approval
    from the user's currently active device.
    """
    user_id: str = Indexed(str)
    new_device_id: str
    old_device_id: str
    status: str = "pending"  # pending | approved | denied | expired
    otp_code: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=5))

    class Settings:
        name = "tb_pending_sessions"
        indexes = [
            [("user_id", 1)],
            [("status", 1)],
            [("created_at", -1)],
        ]

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
