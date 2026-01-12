"""
FCM Device Token Model
Stores FCM tokens for push notifications.
Supports multiple devices per user.
"""
from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
import uuid


class FCMDeviceToken(Document):
    """
    FCM device token for push notifications.
    
    One user can have multiple device tokens (multiple devices).
    Tokens are updated when user logs in or refreshes.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    user_id: Indexed(str)
    token: Indexed(str, unique=True)  # FCM registration token
    
    # Device info for management
    device_type: str = "unknown"  # ios, android, web
    device_name: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None

    class Settings:
        name = "fcm_device_tokens"
        indexes = [
            # User's devices
            [("user_id", 1), ("is_active", 1)],
            # Token lookup
            [("token", 1)],
            # Cleanup stale tokens
            [("updated_at", 1)],
        ]
