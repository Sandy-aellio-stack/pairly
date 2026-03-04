"""
User Block Model
Tracks blocked users for privacy and safety.
"""
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
import uuid


class UserBlock(Document):
    """
    Tracks when a user blocks another user.
    """
    blocker_id: Indexed(PydanticObjectId)  # User who initiated the block
    blocked_id: Indexed(PydanticObjectId)  # User who was blocked
    
    reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "user_blocks"
        indexes = [
            # Efficient lookups for block checks
            [("blocker_id", 1), ("blocked_id", 1)],
            # Reverse lookup (who blocked me)
            [("blocked_id", 1)],
        ]
