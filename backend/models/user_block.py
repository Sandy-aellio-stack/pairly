"""
User Block Model
Tracks blocked users for privacy and safety.
"""
from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
import uuid


class UserBlock(Document):
    """
    Tracks when a user blocks another user.
    
    When blocked:
    - Users cannot view each other's profiles
    - Users cannot send messages to each other
    - Users won't appear in each other's nearby/discovery
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    blocker_id: Indexed(str)  # User who initiated the block
    blocked_id: Indexed(str)  # User who was blocked
    
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
