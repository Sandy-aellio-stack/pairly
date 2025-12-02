from beanie import Document, PydanticObjectId, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional, List

class GeoJSONPoint:
    type: str = "Point"
    coordinates: List[float]  # [lng, lat]

class Profile(Document):
    user_id: Indexed(PydanticObjectId, unique=True)
    display_name: str
    bio: Optional[str] = None
    age: int
    profile_picture_url: Optional[str] = None
    gallery_urls: List[str] = Field(default_factory=list)
    price_per_message: int = 0  # in credits
    location: Optional[dict] = None  # GeoJSON Point format
    is_online: bool = False
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    total_earnings: int = 0
    view_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "profiles"
        indexes = [
            [("location", "2dsphere")],
        ]