from beanie import Document
from datetime import datetime, timezone
from typing import Optional
from pydantic import Field

class AdminSession(Document):
    """Track admin user sessions"""
    
    admin_user_id: str
    session_id: str
    ip_address: str
    user_agent: Optional[str] = None
    login_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    logout_at: Optional[datetime] = None
    is_active: bool = True
    
    class Settings:
        name = "admin_sessions"
        indexes = [
            "admin_user_id",
            "session_id",
            "is_active",
            [("admin_user_id", 1), ("is_active", 1)]
        ]