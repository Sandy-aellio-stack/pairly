from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional

class Presence(Document):
    user_id: str = Indexed(unique=True)
    status: str = Field("offline", description="online|away|offline")
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_info: Optional[dict] = None  # browser, device, ip
    ttl_expires_at: Optional[datetime] = None

    class Settings:
        name = "presence"
        indexes = [
            # Unique user presence
            [("user_id", 1)],
            # Status with last seen
            [("status", 1), ("last_seen", -1)],
        ]
