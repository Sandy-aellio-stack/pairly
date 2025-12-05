"""Match Feedback Model - User reactions to recommendations."""

from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    LIKE = "like"
    SKIP = "skip"
    SUPER_LIKE = "super_like"
    BLOCK = "block"


class MatchFeedback(Document):
    """Record of user feedback on recommended profiles."""
    
    user_id: PydanticObjectId  # User giving feedback
    target_user_id: PydanticObjectId  # User being rated
    feedback_type: FeedbackType
    
    # Context
    match_score: float  # Score at time of recommendation
    position_in_list: int  # Position in recommendation list
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "match_feedback"
        indexes = [
            [("user_id", 1), ("timestamp", -1)],
            [("target_user_id", 1)],
            [("feedback_type", 1), ("timestamp", -1)]
        ]
