from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

class PresenceStatus(str, Enum):
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"

class PresenceV2(Document):
    user_id: str = Field(...)
    status: PresenceStatus = Field(default=PresenceStatus.OFFLINE)
    
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    device_info: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "presence_v2"
        indexes = [
            "user_id",
            "status",
            "last_activity",
            [("user_id", 1)],  # Unique constraint
            [("status", 1), ("last_activity", -1)]
        ]
