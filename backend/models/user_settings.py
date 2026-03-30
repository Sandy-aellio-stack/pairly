from beanie import Document, PydanticObjectId, Indexed, before_event
from pydantic import Field
from datetime import datetime
from typing import Dict, Any
from backend.models.user import User

class UserSettings(Document):
    """
    User application settings for notifications, privacy, safety.
    One document per user.
    """
    user_id: Indexed(PydanticObjectId, unique=True)
    
    # Notifications - defaults from task/UI
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "new_messages": True,
            "new_matches": True,
            "nearby_users": False
        }
    )
    
    # Privacy settings
    privacy: Dict[str, bool] = Field(
        default_factory=lambda: {
            "show_online_status": True,
            "show_last_seen": True,
            "show_distance": True
        }
    )
    
    # Safety settings
    safety: Dict[str, bool] = Field(
        default_factory=lambda: {
            "block_screenshots": False,
            "verified_matches_only": False,
            "hide_from_search": False
        }
    )
    
    # General
    dark_mode: bool = False
    language: str = Field(default="en")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @before_event
    def set_updated_at(self):
        self.updated_at = datetime.utcnow()
    
    class Settings:
        name = "user_settings"
        indexes = [
            [("user_id", 1)],
            [("updated_at", -1)],
        ]

