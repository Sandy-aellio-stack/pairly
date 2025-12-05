"""Profile Embedder - Converts profiles to similarity vectors."""

from typing import List, Dict
import hashlib


class ProfileEmbedder:
    """
    Stub embedder for profile similarity.
    
    In production, this would use a trained ML model.
    For now, uses simple heuristics.
    """
    
    @staticmethod
    def embed_profile(user_data: Dict) -> List[float]:
        """
        Convert user profile to embedding vector.
        
        Current implementation: Simple feature encoding
        - Interests: One-hot style encoding
        - Age: Normalized value
        - Activity: Engagement metrics
        
        Returns 128-dimensional vector.
        """
        embedding = [0.0] * 128
        
        # Encode interests (positions 0-63)
        interests = user_data.get("interests", [])
        for i, interest in enumerate(interests[:63]):
            # Simple hash-based position
            pos = hash(interest) % 64
            embedding[pos] = 1.0
        
        # Encode age (position 64)
        age = user_data.get("age", 25)
        embedding[64] = (age - 18) / 82  # Normalize to 0-1
        
        # Encode relationship goal (positions 65-68)
        goal = user_data.get("relationship_goal", "unsure")
        goal_map = {"casual": 65, "serious": 66, "friendship": 67, "unsure": 68}
        if goal in goal_map:
            embedding[goal_map[goal]] = 1.0
        
        # Encode engagement (position 69)
        engagement = user_data.get("engagement_score", 0.0)
        embedding[69] = min(engagement / 100, 1.0)  # Normalize
        
        # Remaining positions for future features
        
        return embedding
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    @classmethod
    def calculate_similarity(cls, user1_data: Dict, user2_data: Dict) -> float:
        """Calculate similarity between two users."""
        vec1 = cls.embed_profile(user1_data)
        vec2 = cls.embed_profile(user2_data)
        return cls.cosine_similarity(vec1, vec2)
