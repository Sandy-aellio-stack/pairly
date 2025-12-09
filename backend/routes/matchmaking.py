"""Matchmaking API Routes."""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from beanie import PydanticObjectId

from backend.models.user import User, Role
from backend.models.user_preferences import UserPreferences, Gender, RelationshipGoal
from backend.models.match_feedback import MatchFeedback, FeedbackType
from backend.models.match_recommendation import MatchRecommendation
from backend.routes.auth import get_current_user
from backend.services.matchmaking.recommendation_pipeline import RecommendationPipeline
from backend.services.matchmaking.recommendation_worker import refresh_user_recommendations

router = APIRouter(prefix="/api/matchmaking", tags=["matchmaking"])


# ===== Preference Management =====

class UpdatePreferencesRequest(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    preferred_genders: Optional[List[Gender]] = None
    max_distance_km: Optional[int] = None
    interests: Optional[List[str]] = None
    lifestyle_tags: Optional[List[str]] = None
    relationship_goals: Optional[List[RelationshipGoal]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_city: Optional[str] = None


@router.get("/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    """Get user's matchmaking preferences."""
    prefs = await UserPreferences.find_one(UserPreferences.user_id == user.id)
    
    if not prefs:
        # Create default preferences
        prefs = UserPreferences(user_id=user.id)
        await prefs.insert()
    
    return {
        "user_id": str(user.id),
        "min_age": prefs.min_age,
        "max_age": prefs.max_age,
        "preferred_genders": prefs.preferred_genders,
        "max_distance_km": prefs.max_distance_km,
        "interests": prefs.interests,
        "lifestyle_tags": prefs.lifestyle_tags,
        "relationship_goals": prefs.relationship_goals,
        "location_city": prefs.location_city,
        "engagement_score": prefs.engagement_score
    }


@router.put("/preferences")
async def update_preferences(
    req: UpdatePreferencesRequest,
    user: User = Depends(get_current_user)
):
    """Update matchmaking preferences."""
    prefs = await UserPreferences.find_one(UserPreferences.user_id == user.id)
    
    if not prefs:
        prefs = UserPreferences(user_id=user.id)
    
    # Update fields
    if req.min_age is not None:
        prefs.min_age = req.min_age
    if req.max_age is not None:
        prefs.max_age = req.max_age
    if req.preferred_genders is not None:
        prefs.preferred_genders = req.preferred_genders
    if req.max_distance_km is not None:
        prefs.max_distance_km = req.max_distance_km
    if req.interests is not None:
        prefs.interests = req.interests
    if req.lifestyle_tags is not None:
        prefs.lifestyle_tags = req.lifestyle_tags
    if req.relationship_goals is not None:
        prefs.relationship_goals = req.relationship_goals
    if req.latitude is not None:
        prefs.latitude = req.latitude
    if req.longitude is not None:
        prefs.longitude = req.longitude
    if req.location_city is not None:
        prefs.location_city = req.location_city
    
    prefs.updated_at = datetime.now(timezone.utc)
    
    if prefs.id:
        await prefs.save()
    else:
        await prefs.insert()
    
    # Trigger recommendation refresh asynchronously (graceful degradation)
    try:
        refresh_user_recommendations.delay(str(user.id))
    except Exception as e:
        # Log but don't fail if Celery/Redis unavailable
        print(f"Warning: Could not queue recommendation refresh: {e}")
    
    return {"success": True, "message": "Preferences updated"}


# ===== Recommendations =====

@router.get("/recommendations")
async def get_recommendations(
    limit: int = Query(20, le=50),
    skip: int = Query(0, ge=0),
    force_refresh: bool = Query(False),
    user: User = Depends(get_current_user)
):
    """Get match recommendations for user."""
    recommendations = await RecommendationPipeline.generate_recommendations(
        user_id=user.id,
        force_refresh=force_refresh
    )
    
    # Paginate
    paginated = recommendations.recommendations[skip:skip + limit]
    
    return {
        "recommendations": paginated,
        "total": len(recommendations.recommendations),
        "limit": limit,
        "skip": skip,
        "generated_at": recommendations.generated_at.isoformat(),
        "algorithm_version": recommendations.algorithm_version,
        "computation_time_ms": recommendations.computation_time_ms
    }


# ===== Feedback =====

class SubmitFeedbackRequest(BaseModel):
    target_user_id: str
    feedback_type: FeedbackType
    match_score: Optional[float] = 0.0
    position: Optional[int] = 0


@router.post("/feedback")
async def submit_feedback(
    req: SubmitFeedbackRequest,
    user: User = Depends(get_current_user)
):
    """Submit feedback on a recommended profile."""
    target_oid = PydanticObjectId(req.target_user_id)
    
    # Create feedback record
    feedback = MatchFeedback(
        user_id=user.id,
        target_user_id=target_oid,
        feedback_type=req.feedback_type,
        match_score=req.match_score,
        position_in_list=req.position
    )
    await feedback.insert()
    
    # Update user preferences engagement
    prefs = await UserPreferences.find_one(UserPreferences.user_id == user.id)
    if prefs:
        if req.feedback_type == FeedbackType.LIKE:
            prefs.total_likes += 1
        elif req.feedback_type == FeedbackType.SKIP:
            prefs.total_skips += 1
        
        # Update engagement score (simple formula)
        prefs.engagement_score = (prefs.total_likes * 2) + (prefs.total_messages_sent * 3)
        prefs.last_active_at = datetime.now(timezone.utc)
        await prefs.save()
    
    return {
        "success": True,
        "feedback_id": str(feedback.id),
        "feedback_type": req.feedback_type
    }


@router.get("/feedback/stats")
async def get_feedback_stats(user: User = Depends(get_current_user)):
    """Get user's feedback statistics."""
    prefs = await UserPreferences.find_one(UserPreferences.user_id == user.id)
    
    if not prefs:
        return {
            "total_likes": 0,
            "total_skips": 0,
            "engagement_score": 0
        }
    
    return {
        "total_likes": prefs.total_likes,
        "total_skips": prefs.total_skips,
        "engagement_score": prefs.engagement_score,
        "total_messages_sent": prefs.total_messages_sent,
        "total_calls_made": prefs.total_calls_made
    }


# ===== Admin Endpoints =====

class RecomputeRequest(BaseModel):
    user_ids: Optional[List[str]] = None  # If None, recompute for all


@router.post("/admin/recompute")
async def admin_recompute_recommendations(
    req: RecomputeRequest,
    admin: User = Depends(get_current_user)
):
    """Admin: Force recompute recommendations for users."""
    if admin.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    try:
        if req.user_ids:
            # Recompute for specific users
            for user_id in req.user_ids:
                refresh_user_recommendations.delay(user_id)
            
            return {
                "success": True,
                "message": f"Queued recomputation for {len(req.user_ids)} users"
            }
        else:
            # Trigger batch recomputation
            from backend.services.matchmaking.recommendation_worker import generate_batch_recommendations
            generate_batch_recommendations.delay()
            
            return {
                "success": True,
                "message": "Queued batch recomputation for all users"
            }
    except Exception as e:
        # Graceful fallback if Celery unavailable
        return {
            "success": False,
            "message": f"Background worker unavailable: {str(e)}. Recommendations will be generated on-demand."
        }


@router.get("/admin/debug/{user_id}")
async def admin_debug_recommendations(
    user_id: str,
    admin: User = Depends(get_current_user)
):
    """Admin: Debug view of recommendation generation for a user."""
    if admin.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    user_oid = PydanticObjectId(user_id)
    
    # Get preferences
    prefs = await UserPreferences.find_one(UserPreferences.user_id == user_oid)
    if not prefs:
        raise HTTPException(404, "User preferences not found")
    
    # Get cached recommendations
    cached = await MatchRecommendation.find_one(
        MatchRecommendation.user_id == user_oid
    )
    
    # Get recent feedback
    feedback = await MatchFeedback.find(
        MatchFeedback.user_id == user_oid
    ).sort("-timestamp").limit(20).to_list()
    
    return {
        "user_id": user_id,
        "preferences": {
            "age_range": f"{prefs.min_age}-{prefs.max_age}",
            "max_distance_km": prefs.max_distance_km,
            "interests": prefs.interests,
            "relationship_goals": prefs.relationship_goals,
            "engagement_score": prefs.engagement_score
        },
        "cached_recommendations": {
            "count": len(cached.recommendations) if cached else 0,
            "generated_at": cached.generated_at.isoformat() if cached else None,
            "expires_at": cached.expires_at.isoformat() if cached else None,
            "computation_time_ms": cached.computation_time_ms if cached else None
        },
        "recent_feedback": [
            {
                "target_user_id": str(fb.target_user_id),
                "feedback_type": fb.feedback_type,
                "timestamp": fb.timestamp.isoformat()
            }
            for fb in feedback
        ]
    }


from datetime import datetime, timezone
