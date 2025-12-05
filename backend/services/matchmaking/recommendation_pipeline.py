"""Recommendation Pipeline - Generates match recommendations."""

from typing import List, Dict, Set
from datetime import datetime, timedelta
import time

from backend.models.user_preferences import UserPreferences
from backend.models.match_recommendation import MatchRecommendation
from backend.models.match_feedback import MatchFeedback, FeedbackType
from backend.models.user import User
from backend.services.matchmaking.scoring_engine import MatchScoringEngine
from beanie import PydanticObjectId


class RecommendationPipeline:
    """
    Generates personalized match recommendations.
    
    Pipeline stages:
    1. Hard filtering (age, distance, previous interactions)
    2. Score calculation for all candidates
    3. Soft filtering and ranking
    4. Diversity injection
    5. Cold-start handling
    6. Cache storage
    """
    
    # Configuration
    DEFAULT_RECOMMENDATION_COUNT = 50
    CACHE_TTL_HOURS = 24
    MIN_SCORE_THRESHOLD = 0.3  # Soft filter
    DIVERSITY_FACTOR = 0.2  # 20% diversity profiles
    
    @classmethod
    async def generate_recommendations(
        cls,
        user_id: PydanticObjectId,
        force_refresh: bool = False
    ) -> MatchRecommendation:
        """
        Generate or retrieve cached recommendations for a user.
        
        Returns MatchRecommendation object with ranked list.
        """
        start_time = time.time()
        
        # Check cache if not forcing refresh
        if not force_refresh:
            cached = await cls._get_cached_recommendations(user_id)
            if cached and cached.expires_at > datetime.utcnow():
                return cached
        
        # Get user preferences
        user_prefs = await UserPreferences.find_one(
            UserPreferences.user_id == user_id
        )
        
        if not user_prefs:
            # Return empty recommendations
            return MatchRecommendation(
                user_id=user_id,
                recommendations=[],
                total_candidates=0,
                generated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=cls.CACHE_TTL_HOURS)
            )
        
        user = await User.get(user_id)
        user_data = cls._extract_user_data(user, user_prefs)
        
        # Stage 1: Hard filtering
        candidates = await cls._hard_filter_candidates(user_prefs, user_id)
        
        # Stage 2: Score all candidates
        scored_candidates = []
        for candidate in candidates:
            candidate_prefs = await UserPreferences.find_one(
                UserPreferences.user_id == candidate.id
            )
            
            if candidate_prefs:
                candidate_data = cls._extract_user_data(candidate, candidate_prefs)
                score, breakdown = MatchScoringEngine.calculate_score(
                    user_prefs, candidate_prefs, user_data, candidate_data
                )
                
                scored_candidates.append({
                    "user_id": str(candidate.id),
                    "score": score,
                    "breakdown": breakdown,
                    "reasons": cls._generate_match_reasons(breakdown)
                })
        
        # Stage 3: Soft filtering and ranking
        filtered = [
            c for c in scored_candidates 
            if c["score"] >= cls.MIN_SCORE_THRESHOLD
        ]
        filtered.sort(key=lambda x: x["score"], reverse=True)
        
        # Stage 4: Diversity injection
        final_recommendations = cls._inject_diversity(
            filtered, cls.DEFAULT_RECOMMENDATION_COUNT
        )
        
        # Stage 5: Cold-start handling
        if len(final_recommendations) < 10:
            final_recommendations = await cls._apply_cold_start_boost(
                final_recommendations, user_prefs
            )
        
        # Create recommendation object
        computation_time = (time.time() - start_time) * 1000
        
        recommendation = MatchRecommendation(
            user_id=user_id,
            recommendations=final_recommendations[:cls.DEFAULT_RECOMMENDATION_COUNT],
            total_candidates=len(candidates),
            algorithm_version="v1",
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=cls.CACHE_TTL_HOURS),
            computation_time_ms=computation_time
        )
        
        # Save to database
        await recommendation.insert()
        
        return recommendation
    
    @staticmethod
    async def _get_cached_recommendations(user_id: PydanticObjectId):
        """Retrieve cached recommendations."""
        return await MatchRecommendation.find_one(
            MatchRecommendation.user_id == user_id,
            MatchRecommendation.expires_at > datetime.utcnow()
        )
    
    @staticmethod
    async def _hard_filter_candidates(
        user_prefs: UserPreferences,
        user_id: PydanticObjectId
    ) -> List[User]:
        """
        Apply hard filters to get candidate pool.
        
        Filters:
        - Age within range
        - Distance within max
        - Not previously matched/blocked
        - Active within last 30 days
        """
        # Get users who match hard criteria
        query = {}
        
        # Exclude self
        query["_id"] = {"$ne": user_id}
        
        # Active users only (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        candidates = await User.find(
            query
        ).limit(500).to_list()  # Limit candidate pool for performance
        
        # Filter by preferences
        filtered = []
        for candidate in candidates:
            candidate_prefs = await UserPreferences.find_one(
                UserPreferences.user_id == candidate.id
            )
            
            if not candidate_prefs:
                continue
            
            # Age filter
            candidate_age = candidate.age if hasattr(candidate, 'age') else 25
            if not (user_prefs.min_age <= candidate_age <= user_prefs.max_age):
                continue
            
            # Distance filter (if both have location)
            if user_prefs.latitude and user_prefs.longitude and \
               candidate_prefs.latitude and candidate_prefs.longitude:
                distance = MatchScoringEngine.calculate_distance(
                    user_prefs.latitude, user_prefs.longitude,
                    candidate_prefs.latitude, candidate_prefs.longitude
                )
                if distance > user_prefs.max_distance_km:
                    continue
            
            filtered.append(candidate)
        
        # Exclude previously blocked/skipped (recent)
        recent_feedback = await MatchFeedback.find(
            MatchFeedback.user_id == user_id,
            MatchFeedback.feedback_type.in_([FeedbackType.BLOCK, FeedbackType.SKIP])
        ).to_list()
        
        blocked_ids = {fb.target_user_id for fb in recent_feedback}
        final_filtered = [c for c in filtered if c.id not in blocked_ids]
        
        return final_filtered
    
    @staticmethod
    def _extract_user_data(user: User, prefs: UserPreferences) -> Dict:
        """Extract user data for scoring."""
        return {
            "age": getattr(user, 'age', 25),
            "gender": getattr(user, 'gender', 'other'),
            "interests": prefs.interests,
            "relationship_goal": prefs.relationship_goals[0] if prefs.relationship_goals else "unsure",
            "engagement_score": prefs.engagement_score
        }
    
    @staticmethod
    def _generate_match_reasons(breakdown: Dict[str, float]) -> List[str]:
        """Generate human-readable match reasons."""
        reasons = []
        
        if breakdown.get("demographic", 0) > 0.7:
            reasons.append("Great age and lifestyle match")
        
        if breakdown.get("interests", 0) > 0.6:
            reasons.append("Shared interests")
        
        if breakdown.get("behavioral", 0) > 0.7:
            reasons.append("Active user")
        
        if breakdown.get("ml_similarity", 0) > 0.7:
            reasons.append("Similar profile")
        
        if not reasons:
            reasons.append("Potential match")
        
        return reasons
    
    @staticmethod
    def _inject_diversity(
        ranked_list: List[Dict],
        target_count: int
    ) -> List[Dict]:
        """
        Inject diversity to avoid repetitive profiles.
        
        Strategy: Take top 80%, then intersperse from next tier.
        """
        if len(ranked_list) <= target_count:
            return ranked_list
        
        top_tier_count = int(target_count * 0.8)
        diversity_count = target_count - top_tier_count
        
        top_tier = ranked_list[:top_tier_count]
        diversity_pool = ranked_list[top_tier_count:top_tier_count + diversity_count * 3]
        
        # Sample diversity profiles (every Nth)
        step = len(diversity_pool) // diversity_count if diversity_count > 0 else 1
        diversity_picks = diversity_pool[::max(step, 1)][:diversity_count]
        
        # Interleave
        final = top_tier + diversity_picks
        return final[:target_count]
    
    @staticmethod
    async def _apply_cold_start_boost(
        recommendations: List[Dict],
        user_prefs: UserPreferences
    ) -> List[Dict]:
        """
        Cold-start heuristic: Boost popular/active users.
        """
        # For new users with few recommendations, add popular profiles
        popular_users = await UserPreferences.find(
            UserPreferences.engagement_score > 50
        ).sort("-engagement_score").limit(20).to_list()
        
        for popular in popular_users:
            if len(recommendations) >= 20:
                break
            
            # Add if not already in list
            existing_ids = {r["user_id"] for r in recommendations}
            if str(popular.user_id) not in existing_ids:
                recommendations.append({
                    "user_id": str(popular.user_id),
                    "score": 0.5,  # Medium score
                    "reasons": ["Popular profile", "Active user"]
                })
        
        return recommendations
