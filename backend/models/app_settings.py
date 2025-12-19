from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field
import uuid


class AppSettings(Document):
    """Global app settings - singleton document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Pricing
    message_cost: int = 1
    audio_call_cost_per_min: int = 5
    video_call_cost_per_min: int = 10
    signup_bonus: int = 10
    
    # Packages
    packages: list = Field(default_factory=lambda: [
        {"id": "starter", "name": "Starter", "coins": 100, "price_inr": 100, "discount": 0},
        {"id": "popular", "name": "Popular", "coins": 500, "price_inr": 450, "discount": 10, "popular": True},
        {"id": "premium", "name": "Premium", "coins": 1000, "price_inr": 800, "discount": 20},
    ])
    
    # Matching settings
    default_search_radius: int = 50
    max_search_radius: int = 500
    min_age: int = 18
    max_age: int = 100
    
    # Safety settings
    auto_moderation: bool = True
    profanity_filter: bool = True
    photo_verification: bool = False
    
    # App status
    maintenance_mode: bool = False
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None

    class Settings:
        name = "app_settings"

    @classmethod
    async def get_settings(cls) -> "AppSettings":
        """Get or create app settings singleton"""
        settings = await cls.find_one()
        if not settings:
            settings = cls(id="global_settings")
            await settings.insert()
        return settings
