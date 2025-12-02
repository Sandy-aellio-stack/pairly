from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import Optional

class Session(Document):
    session_id: str
    user_id: PydanticObjectId
    device_info: str = ""
    ip: str = ""
    fingerprint_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    revoked: bool = False
    refresh_token_id: str
    
    class Settings:
        name = "sessions"
        indexes = [
            [("user_id", 1)],
            [("session_id", 1)],
            [("refresh_token_id", 1)],
            [("revoked", 1)],
            [("fingerprint_hash", 1)],
            [("last_active_at", -1)]
        ]