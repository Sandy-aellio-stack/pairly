"""User Preferences Model for Matchmaking."""

from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"


class RelationshipGoal(str, Enum):
    CASUAL = "casual"
    SERIOUS = "serious"
    FRIENDSHIP = "friendship"
    UNSURE = "unsure"


class UserPreferences(Document):
    """Matchmaking preferences for a user."""
    
    user_id: PydanticObjectId
    
    # Demographic preferences
    min_age: int = 18
    max_age: int = 99
    preferred_genders: List[Gender] = Field(default_factory=list)
    max_distance_km: int = 50  # Distance filter
    
    # Lifestyle preferences
    interests: List[str] = Field(default_factory=list)  # e.g., ["hiking", "movies"]
    lifestyle_tags: List[str] = Field(default_factory=list)  # e.g., ["vegan", "active"]
    relationship_goals: List[RelationshipGoal] = Field(default_factory=list)
    
    # Location (for distance calculation)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_city: Optional[str] = None
    
    # Behavioral signals
    total_likes: int = 0
    total_skips: int = 0
    total_messages_sent: int = 0
    total_calls_made: int = 0
    engagement_score: float = 0.0  # Computed metric
    
    # Last activity
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_preferences"
        indexes = [
            [("user_id", 1)],
            [("latitude", 1), ("longitude", 1)],
            [("last_active_at", -1)]
        ]
