from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone

class Notification(Document):
    user_id: str
    title: str
    body: str
    meta: dict = Field(default_factory=dict)
    read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notifications"
        indexes = [
            [("user_id", 1), ("read", 1), ("created_at", -1)]
        ]