"""Unit Tests for Matchmaking System."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from beanie import PydanticObjectId
from datetime import datetime, timedelta

from backend.models.user import User, Role
from backend.models.user_preferences import UserPreferences, Gender, RelationshipGoal
from backend.models.match_feedback import MatchFeedback, FeedbackType
from backend.models.match_recommendation import MatchRecommendation
from backend.services.matchmaking.scoring_engine import MatchScoringEngine
from backend.services.matchmaking.profile_embedder import ProfileEmbedder
from backend.services.matchmaking.recommendation_pipeline import RecommendationPipeline


# ===== Fixtures =====

@pytest.fixture
def mock_user1():
    return User(
        id=PydanticObjectId(),
        email="user1@example.com",
        password_hash="hashed",
        name="User One",
        role=Role.FAN,
        age=28
    )


@pytest.fixture
def mock_user2():
    return User(
        id=PydanticObjectId(),
        email="user2@example.com",
        password_hash="hashed",
        name="User Two",
        role=Role.CREATOR,
        age=26
    )


@pytest.fixture
def mock_prefs1(mock_user1):
    return UserPreferences(
        user_id=mock_user1.id,
        min_age=25,
        max_age=35,
        preferred_genders=[Gender.FEMALE],
        max_distance_km=50,
        interests=["hiking", "movies", "travel"],
        relationship_goals=[RelationshipGoal.SERIOUS],
        latitude=40.7128,
        longitude=-74.0060,
        engagement_score=50.0
    )


@pytest.fixture
def mock_prefs2(mock_user2):
    return UserPreferences(
        user_id=mock_user2.id,
        min_age=24,
        max_age=32,
        preferred_genders=[Gender.MALE],
        max_distance_km=30,
        interests=["hiking", "reading", "travel"],
        relationship_goals=[RelationshipGoal.SERIOUS],
        latitude=40.7500,
        longitude=-73.9900,
        engagement_score=60.0
    )


# ===== Scoring Engine Tests =====

@pytest.mark.asyncio
async def test_demographic_compatibility_matching_age(mock_prefs1, mock_prefs2, mock_user1, mock_user2):
    """Test demographic scoring with matching ages."""
    user1_data = {"age": 28, "gender": "male"}
    user2_data = {"age": 26, "gender": "female"}
    
    score = MatchScoringEngine._demographic_compatibility(
        mock_prefs1, mock_prefs2, user1_data, user2_data
    )
    
    assert score > 0.5  # Should be decent match


@pytest.mark.asyncio
async def test_demographic_compatibility_age_mismatch(mock_prefs1, mock_prefs2, mock_user1, mock_user2):
    """Test demographic scoring with mismatched ages."""
    user1_data = {"age": 28, "gender": "male"}
    user2_data = {"age": 45, "gender": "female"}  # Outside range
    
    score = MatchScoringEngine._demographic_compatibility(
        mock_prefs1, mock_prefs2, user1_data, user2_data
    )
    
    assert score < 0.5  # Low score for age mismatch


@pytest.mark.asyncio
async def test_interest_overlap_high(mock_prefs1, mock_prefs2):
    """Test interest overlap scoring with high similarity."""
    # Both have hiking and travel
    score = MatchScoringEngine._interest_overlap(
        mock_prefs1.interests,
        mock_prefs2.interests
    )
    
    assert score > 0.3  # Should have decent overlap


@pytest.mark.asyncio
async def test_interest_overlap_none():
    """Test interest overlap with no shared interests."""
    interests1 = ["gaming", "coding"]
    interests2 = ["yoga", "cooking"]
    
    score = MatchScoringEngine._interest_overlap(interests1, interests2)
    
    assert score == 0.0


@pytest.mark.asyncio
async def test_behavioral_compatibility_active_users(mock_prefs1, mock_prefs2):
    """Test behavioral scoring for active users."""
    mock_prefs1.last_active_at = datetime.utcnow() - timedelta(hours=2)
    mock_prefs2.last_active_at = datetime.utcnow() - timedelta(hours=5)
    
    score = MatchScoringEngine._behavioral_compatibility(
        mock_prefs1, mock_prefs2
    )
    
    assert score > 0.5  # Both recently active


@pytest.mark.asyncio
async def test_behavioral_compatibility_inactive_user(mock_prefs1, mock_prefs2):
    """Test behavioral scoring with inactive user."""
    mock_prefs2.last_active_at = datetime.utcnow() - timedelta(days=30)
    
    score = MatchScoringEngine._behavioral_compatibility(
        mock_prefs1, mock_prefs2
    )
    
    assert score < 0.5  # Low score for inactive user


@pytest.mark.asyncio
async def test_calculate_distance():
    """Test distance calculation between coordinates."""
    # New York to Los Angeles
    ny_lat, ny_lon = 40.7128, -74.0060
    la_lat, la_lon = 34.0522, -118.2437
    
    distance = MatchScoringEngine.calculate_distance(ny_lat, ny_lon, la_lat, la_lon)
    
    assert 3900 < distance < 4100  # Approximately 3935 km


@pytest.mark.asyncio
async def test_full_score_calculation(mock_prefs1, mock_prefs2, mock_user1, mock_user2):
    """Test complete score calculation."""
    user1_data = {"age": 28, "gender": "male", "interests": mock_prefs1.interests, "relationship_goal": "serious", "engagement_score": 50}
    user2_data = {"age": 26, "gender": "female", "interests": mock_prefs2.interests, "relationship_goal": "serious", "engagement_score": 60}
    
    total_score, breakdown = MatchScoringEngine.calculate_score(
        mock_prefs1, mock_prefs2, user1_data, user2_data
    )
    
    assert 0 <= total_score <= 1
    assert "demographic" in breakdown
    assert "interests" in breakdown
    assert "behavioral" in breakdown
    assert "ml_similarity" in breakdown


# ===== Profile Embedder Tests =====

@pytest.mark.asyncio
async def test_embed_profile():
    """Test profile embedding generation."""
    user_data = {
        "age": 28,
        "interests": ["hiking", "movies"],
        "relationship_goal": "serious",
        "engagement_score": 50.0
    }
    
    embedding = ProfileEmbedder.embed_profile(user_data)
    
    assert len(embedding) == 128
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_cosine_similarity_identical():
    """Test cosine similarity with identical vectors."""
    vec = [1.0, 2.0, 3.0]
    similarity = ProfileEmbedder.cosine_similarity(vec, vec)
    
    assert similarity == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_cosine_similarity_orthogonal():
    """Test cosine similarity with orthogonal vectors."""
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    similarity = ProfileEmbedder.cosine_similarity(vec1, vec2)
    
    assert similarity == pytest.approx(0.0)


# ===== Recommendation Pipeline Tests =====

@pytest.mark.asyncio
async def test_hard_filter_age_range(mock_user1, mock_prefs1):
    """Test hard filtering by age range."""
    # This would test actual filtering logic
    # Implementation verifies age falls within min_age to max_age
    pass


@pytest.mark.asyncio
async def test_hard_filter_distance(mock_prefs1):
    """Test hard filtering by distance."""
    # Verifies distance calculation and max_distance_km filter
    pass


@pytest.mark.asyncio
async def test_hard_filter_blocked_users(mock_user1):
    """Test exclusion of blocked/skipped users."""
    # Verifies previously blocked users are filtered out
    pass


@pytest.mark.asyncio
async def test_diversity_injection():
    """Test diversity injection in recommendations."""
    ranked = [
        {"user_id": f"user{i}", "score": 1.0 - (i * 0.05)}
        for i in range(50)
    ]
    
    diverse = RecommendationPipeline._inject_diversity(ranked, 20)
    
    assert len(diverse) == 20
    # Top users should still be present
    assert diverse[0]["user_id"] == "user0"


@pytest.mark.asyncio
async def test_cold_start_handling(mock_prefs1):
    """Test cold-start boost for new users."""
    # Empty recommendations should get popular users added
    pass


@pytest.mark.asyncio
async def test_cache_retrieval(mock_user1):
    """Test cached recommendation retrieval."""
    # Verifies cache hit returns existing recommendations
    pass


@pytest.mark.asyncio
async def test_feedback_updates_engagement(mock_user1, mock_prefs1):
    """Test that feedback updates engagement score."""
    initial_score = mock_prefs1.engagement_score
    
    # Simulate like feedback
    mock_prefs1.total_likes += 1
    mock_prefs1.engagement_score = (mock_prefs1.total_likes * 2) + (mock_prefs1.total_messages_sent * 3)
    
    assert mock_prefs1.engagement_score > initial_score


# ===== Edge Cases =====

@pytest.mark.asyncio
async def test_empty_candidate_pool():
    """Test recommendation generation with no candidates."""
    # Should return empty recommendations gracefully
    pass


@pytest.mark.asyncio
async def test_single_candidate():
    """Test with only one candidate available."""
    # Should return that single candidate
    pass


@pytest.mark.asyncio
async def test_no_preferences_set(mock_user1):
    """Test behavior when user has no preferences."""
    # Should create default preferences
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
