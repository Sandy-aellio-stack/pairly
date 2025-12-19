from datetime import datetime, timezone
from typing import Optional, List
from beanie import Document
from pydantic import Field, EmailStr
from enum import Enum
import uuid
import bcrypt


class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"


class AdminUser(Document):
    """Admin user for dashboard access"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    name: str
    role: AdminRole = AdminRole.ADMIN
    
    is_active: bool = True
    permissions: List[str] = Field(default_factory=list)
    
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

    class Settings:
        name = "admin_users"

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
