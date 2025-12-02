from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime

class OTP(Document):
    user_id: PydanticObjectId
    code: str
    method: str
    verified: bool = False
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "otps"
        indexes = [
            [("user_id", 1)],
            [("expires_at", 1)]
        ]