from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import Optional

class FraudAlert(Document):
    user_id: Optional[PydanticObjectId] = None
    session_id: Optional[str] = None
    ip: str
    fingerprint_hash: str
    score: int
    rule_triggered: str
    metadata: dict = {}
    status: str = "pending"
    resolved_by: Optional[PydanticObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "fraud_alerts"
        indexes = [
            [("user_id", 1)],
            [("fingerprint_hash", 1)],
            [("status", 1)],
            [("score", -1)],
            [("created_at", -1)]
        ]