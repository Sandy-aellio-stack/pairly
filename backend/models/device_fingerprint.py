from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import Optional, List

class DeviceFingerprint(Document):
    user_id: Optional[PydanticObjectId] = None
    session_id: Optional[str] = None
    ip: str
    user_agent: str
    accept_lang: Optional[str] = None
    device_info: dict = {}
    fingerprint_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    risk_history: List[dict] = []
    usage_count: int = 1
    
    class Settings:
        name = "device_fingerprints"
        indexes = [
            [("fingerprint_hash", 1)],
            [("ip", 1)],
            [("user_id", 1)],
            [("last_seen", -1)],
            [("created_at", -1)]
        ]