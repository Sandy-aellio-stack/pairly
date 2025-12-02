from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import Optional

class AuditLog(Document):
    actor_user_id: Optional[PydanticObjectId] = None
    actor_ip: Optional[str] = None
    action: str
    details: dict = {}
    severity: str = "info"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "audit_logs"
        indexes = [
            [("actor_user_id", 1)],
            [("created_at", -1)],
            [("action", 1)]
        ]