from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from pymongo import IndexModel, ASCENDING
from typing import Optional

class FailedLogin(Document):
    user_id: Optional[PydanticObjectId] = None
    ip: Optional[str] = None
    count: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "failed_logins"
        indexes = [
            IndexModel([("created_at", ASCENDING)], expireAfterSeconds=3600),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("ip", ASCENDING)])
        ]