from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime

class Notification(Document):
    user_id: PydanticObjectId
    type: str
    message: str
    metadata: dict = {}
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "notifications"
        indexes = [
            [("user_id", 1), ("is_read", 1), ("created_at", -1)]
        ]