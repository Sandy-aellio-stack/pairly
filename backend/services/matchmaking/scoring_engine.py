"""Match Scoring Engine - Calculates compatibility scores."""

from typing import Dict, List, Tuple
import math
from datetime import datetime

from backend.models.user_preferences import UserPreferences
from backend.services.matchmaking.profile_embedder import ProfileEmbedder


class MatchScoringEngine:
    """
    Calculates match scores between users.
    
    Scoring formula:
    Total Score = (w1 * demographic_score) + 
                  (w2 * interest_score) + 
                  (w3 * behavioral_score) + 
                  (w4 * ml_score)
    
    Weights (configurable):
    - w1 (demographic): 0.25
    - w2 (interests): 0.30
    - w3 (behavioral): 0.20
    - w4 (ML similarity): 0.25
    """
    
    # Default weights (can be overridden)
    WEIGHTS = {
        "demographic": 0.25,
        "interests": 0.30,
        "behavioral": 0.20,
        "ml_similarity": 0.25
    }
    
    @classmethod
    def calculate_score(
        cls,
        user_prefs: UserPreferences,
        candidate_prefs: UserPreferences,
        user_data: Dict,
        candidate_data: Dict
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate match score between two users.
        
        Returns:
            (total_score, score_breakdown)
        """
        # Calculate component scores
        demographic_score = cls._demographic_compatibility(
            user_prefs, candidate_prefs, user_data, candidate_data
        )
        
        interest_score = cls._interest_overlap(
            user_prefs.interests, candidate_prefs.interests
        )
        
        behavioral_score = cls._behavioral_compatibility(
            user_prefs, candidate_prefs
        )
        
        ml_score = ProfileEmbedder.calculate_similarity(
            user_data, candidate_data
        )
        
        # Weighted sum
        total_score = (
            cls.WEIGHTS["demographic"] * demographic_score +
            cls.WEIGHTS["interests"] * interest_score +
            cls.WEIGHTS["behavioral"] * behavioral_score +
            cls.WEIGHTS["ml_similarity"] * ml_score
        )
        
        breakdown = {
            "demographic": demographic_score,
            "interests": interest_score,
            "behavioral": behavioral_score,
            "ml_similarity": ml_score,
            "total": total_score
        }
        
        return total_score, breakdown
    
    @staticmethod
    def _demographic_compatibility(
        user_prefs: UserPreferences,
        candidate_prefs: UserPreferences,
        user_data: Dict,
        candidate_data: Dict
    ) -> float:
        """Score demographic compatibility (0-1)."""
        score = 0.0
        
        # Age compatibility (0-0.4)
        user_age = user_data.get("age", 25)
        candidate_age = candidate_data.get("age", 25)
        
        if user_prefs.min_age <= candidate_age <= user_prefs.max_age:
            age_diff = abs(user_age - candidate_age)
            age_score = max(0, 1 - (age_diff / 20))  # Penalty for large gaps
            score += age_score * 0.4
        
        # Gender preference compatibility (0-0.3)
        candidate_gender = candidate_data.get("gender")
        if not user_prefs.preferred_genders or candidate_gender in user_prefs.preferred_genders:
            score += 0.3
        
        # Relationship goal alignment (0-0.3)
        user_goals = set(user_prefs.relationship_goals)
        candidate_goals = set(candidate_prefs.relationship_goals)
        if user_goals & candidate_goals:  # Any overlap
            score += 0.3
        
        return min(score, 1.0)
    
    @staticmethod
    def _interest_overlap(user_interests: List[str], candidate_interests: List[str]) -> float:
        """Score interest overlap (0-1)."""
        if not user_interests or not candidate_interests:
            return 0.5  # Neutral if no data
        
        user_set = set(user_interests)
        candidate_set = set(candidate_interests)
        
        if not user_set or not candidate_set:
            return 0.5
        
        # Jaccard similarity
        intersection = len(user_set & candidate_set)
        union = len(user_set | candidate_set)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def _behavioral_compatibility(
        user_prefs: UserPreferences,
        candidate_prefs: UserPreferences
    ) -> float:
        """Score based on behavioral patterns (0-1)."""
        score = 0.0
        
        # Activity level alignment (0-0.5)
        user_engagement = user_prefs.engagement_score
        candidate_engagement = candidate_prefs.engagement_score
        
        if user_engagement > 0 and candidate_engagement > 0:
            engagement_ratio = min(user_engagement, candidate_engagement) / max(user_engagement, candidate_engagement)
            score += engagement_ratio * 0.5
        else:
            score += 0.25  # Neutral for new users
        
        # Recent activity bonus (0-0.5)
        now = datetime.utcnow()
        hours_since_active = (now - candidate_prefs.last_active_at).total_seconds() / 3600
        
        if hours_since_active < 24:
            score += 0.5
        elif hours_since_active < 72:
            score += 0.3
        elif hours_since_active < 168:
            score += 0.1
        
        return min(score, 1.0)
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates (Haversine formula) in km."""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
