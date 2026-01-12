from beanie import Document, Indexed
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Intent(str, Enum):
    DATING = "dating"
    SERIOUS = "serious"
    CASUAL = "casual"
    FRIENDSHIP = "friendship"


class Address(BaseModel):
    """Private address - NEVER exposed in APIs"""
    address_line: str
    city: str
    state: str
    country: str
    pincode: str


class Preferences(BaseModel):
    interested_in: Gender
    min_age: int = Field(ge=18, le=100, default=18)
    max_age: int = Field(ge=18, le=100, default=50)
    max_distance_km: int = Field(ge=1, le=500, default=50)


class NotificationSettings(BaseModel):
    messages: bool = True
    matches: bool = True
    calls: bool = True  # Call notifications (always recommended on)
    nearby: bool = False
    marketing: bool = False


class PrivacySettings(BaseModel):
    show_online: bool = True
    show_last_seen: bool = True
    show_distance: bool = True


class SafetySettings(BaseModel):
    block_screenshots: bool = False
    require_verified_matches: bool = False
    hide_from_search: bool = False


class UserSettings(BaseModel):
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    dark_mode: bool = False
    language: str = "en"


class GeoLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class TBUser(Document):
    """TrueBond User Model"""
    # Public/Profile fields
    name: str = Field(min_length=2, max_length=50)
    age: int = Field(ge=18, le=100)
    gender: Gender
    bio: Optional[str] = Field(default=None, max_length=500)
    profile_pictures: List[str] = Field(default_factory=list)
    preferences: Preferences
    intent: Intent = Intent.DATING
    
    # Private/Auth fields - NEVER expose in profile APIs
    email: Indexed(EmailStr, unique=True)
    mobile_number: Indexed(str, unique=True)
    password_hash: str
    address: Address  # Private - never exposed
    
    # Location
    location: Optional[GeoLocation] = None
    location_updated_at: Optional[datetime] = None
    
    # System fields
    credits_balance: int = Field(default=10)  # 10 free credits on signup
    is_active: bool = True
    is_verified: bool = False
    is_online: bool = False
    
    # User settings (notifications, privacy, safety)
    settings: UserSettings = Field(default_factory=UserSettings)
    
    # FCM Push Notification tokens (multiple devices per user)
    fcm_tokens: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('age')
    @classmethod
    def validate_age(cls, v):
        if v < 18:
            raise ValueError('Must be 18 or older to register')
        return v

    class Settings:
        name = "tb_users"
        indexes = [
            # Unique indexes
            [("email", 1)],
            [("mobile_number", 1)],
            # Geospatial index for location-based queries
            [("location", "2dsphere")],
            # Status and filtering indexes
            [("is_active", 1)],
            [("created_at", -1)],
            # Search/discovery indexes
            [("gender", 1), ("age", 1)],
            [("is_online", 1), ("location_updated_at", -1)],
        ]


# Response models - exclude sensitive data
class UserPublicProfile(BaseModel):
    """Public profile - NO address, email, mobile"""
    id: str
    name: str
    age: int
    gender: Gender
    bio: Optional[str]
    profile_pictures: List[str]
    preferences: Preferences
    intent: Intent
    is_online: bool
    distance_km: Optional[float] = None

    class Config:
        from_attributes = True


class UserOwnProfile(BaseModel):
    """Own profile - includes credits, excludes address"""
    id: str
    name: str
    age: int
    gender: Gender
    bio: Optional[str]
    profile_pictures: List[str]
    preferences: Preferences
    intent: Intent
    email: str
    mobile_number: str
    credits_balance: int
    is_verified: bool
    is_online: bool
    created_at: datetime

    class Config:
        from_attributes = True
