"""Match Recommendation Model - Pre-computed recommendations."""

from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import List, Dict, Any


class MatchRecommendation(Document):
    """Pre-computed match recommendations for a user."""
    
    user_id: PydanticObjectId
    
    # Recommended users (sorted by score)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    # Format: [{"user_id": str, "score": float, "reasons": [str]}]
    
    # Metadata
    total_candidates: int = 0
    algorithm_version: str = "v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=datetime.utcnow)  # Cache TTL
    
    # Performance metrics
    computation_time_ms: float = 0.0
    
    class Settings:
        name = "match_recommendations"
        indexes = [
            [("user_id", 1)],
            [("expires_at", 1)]  # TTL index
        ]
