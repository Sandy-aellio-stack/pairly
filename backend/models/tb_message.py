from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional


class TBMessage(Document):
    """One-to-one private message"""
    sender_id: Indexed(str)
    receiver_id: Indexed(str)
    content: str = Field(min_length=1, max_length=2000)
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tb_messages"
        indexes = [
            [("sender_id", 1), ("receiver_id", 1), ("created_at", -1)],
        ]


class TBConversation(Document):
    """Conversation summary between two users"""
    participants: list[str]  # [user_id_1, user_id_2] sorted
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    last_sender_id: Optional[str] = None
    unread_count: dict = Field(default_factory=dict)  # {user_id: count}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tb_conversations"
        indexes = [
            [("participants", 1)],
        ]
