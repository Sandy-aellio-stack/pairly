from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    FLAGGED = "flagged"
    BLOCKED = "blocked"

class MessageV2(Document):
    id: str = Field(...)
    sender_id: str = Field(..., index=True)
    receiver_id: str = Field(..., index=True)
    content: str = Field(...)
    message_type: MessageType = Field(default=MessageType.TEXT)
    status: MessageStatus = Field(default=MessageStatus.SENT)
    moderation_status: ModerationStatus = Field(default=ModerationStatus.APPROVED)
    
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    credits_cost: int = Field(default=1)
    credits_transaction_id: Optional[str] = None
    
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "messages_v2"
        indexes = [
            "sender_id",
            "receiver_id",
            "created_at",
            "status",
            "moderation_status",
            [("sender_id", 1), ("receiver_id", 1), ("created_at", -1)],
            [("receiver_id", 1), ("status", 1)]
        ]
    
    def mark_delivered(self):
        """Mark message as delivered"""
        if self.status == MessageStatus.SENT:
            self.status = MessageStatus.DELIVERED
            self.delivered_at = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)
    
    def mark_read(self):
        """Mark message as read"""
        if self.status in [MessageStatus.SENT, MessageStatus.DELIVERED]:
            self.status = MessageStatus.READ
            self.read_at = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)
    
    def soft_delete(self):
        """Soft delete message"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
