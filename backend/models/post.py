"""Post model for creator content.

Usage:
    - Creators can post text + media (images/videos)
    - Visibility: public or subscribers-only
    - Media validated: max 10 items, size limits enforced
    - Indexes optimized for feed queries

Circular Import Pattern:
    Uses TYPE_CHECKING and Link["Profile"] to avoid circular dependency with profile.py
"""
from __future__ import annotations

from beanie import Document, PydanticObjectId, Link
from pydantic import Field, field_validator
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.profile import Profile


class Visibility(str, Enum):
    PUBLIC = "public"
    SUBSCRIBERS = "subscribers"


class Post(Document):
    """Creator post with text and media content."""
    
    creator: Link["Profile"]
    text: str = Field(max_length=5000)
    media: List[Dict[str, Any]] = Field(default_factory=list)
    visibility: Visibility = Visibility.PUBLIC
    is_archived: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('media')
    @classmethod
    def validate_media(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate media list."""
        if len(v) > 10:
            raise ValueError('Maximum 10 media items allowed')
        
        for item in v:
            # Validate required keys
            if 'type' not in item or 'url' not in item:
                raise ValueError('Media item must have type and url')
            
            # Validate type
            if item['type'] not in ['image', 'video']:
                raise ValueError('Media type must be image or video')
            
            # Validate size if present in meta
            if 'meta' in item and 'size_bytes' in item['meta']:
                size_bytes = item['meta']['size_bytes']
                if item['type'] == 'video' and size_bytes > 100_000_000:  # 100MB
                    raise ValueError('Video size cannot exceed 100MB')
                elif item['type'] == 'image' and size_bytes > 10_000_000:  # 10MB
                    raise ValueError('Image size cannot exceed 10MB')
        
        return v
    
    class Settings:
        name = "posts"
        indexes = [
            [("creator", 1), ("created_at", -1)],  # Creator timeline
            [("visibility", 1), ("created_at", -1)],  # Public feed
            [("is_archived", 1), ("created_at", -1)],  # Active posts
        ]
