from beanie import Document, PydanticObjectId, Indexed
from pydantic import Field
from datetime import datetime

class Message(Document):
    from_user_id: PydanticObjectId
    to_user_id: PydanticObjectId
    content: str
    credits_charged: int
    client_message_id: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "messages"
        indexes = [
            [("from_user_id", 1), ("created_at", -1)],
            [("to_user_id", 1), ("created_at", -1)],
            [("client_message_id", 1)]
        ]
