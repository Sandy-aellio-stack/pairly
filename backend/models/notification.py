from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
from typing import Literal

NotificationType = Literal["message_received", "match_created", "nearby_user_detected", "general"]

class Notification(Document):
    user_id: str
    title: str
    body: str
    type: str = "general"
    meta: dict = Field(default_factory=dict)
    read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notifications"
        indexes = [
            [("user_id", 1), ("read", 1), ("created_at", -1)]
        ]
