"""
TBNotification Model
User-facing in-app notifications stored in MongoDB.
This model is the canonical source — do NOT define TBNotification elsewhere.
"""
from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
import uuid


class TBNotification(Document):
    """User notification stored in tb_notifications collection."""

    # Using str id for backward compat with the legacy uuid-based records
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    user_id: str  # String for simpler querying (matches str(user.id))
    title: str
    body: str
    notification_type: str = "general"  # general | match | message | credit | system | call
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tb_notifications"
        indexes = [
            [("user_id", 1), ("is_read", 1), ("created_at", -1)],
            [("user_id", 1), ("created_at", -1)],
        ]
