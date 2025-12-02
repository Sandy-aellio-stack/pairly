from beanie import Document, PydanticObjectId, Indexed
from pydantic import Field, EmailStr
from datetime import datetime
from enum import Enum
from typing import Optional

class Role(str, Enum):
    FAN = "fan"
    CREATOR = "creator"
    ADMIN = "admin"

class TwoFAMethod(str, Enum):
    EMAIL = "email"
    TOTP = "totp"

class User(Document):
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    name: str
    role: Role
    credits_balance: int = 0
    is_suspended: bool = False
    twofa_enabled: bool = False
    twofa_method: Optional[TwoFAMethod] = None
    twofa_secret: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            [("email", 1)]
        ]