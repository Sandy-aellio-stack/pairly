"""
Luveloop Location API
Privacy-safe geolocation endpoints.

Privacy Guarantees:
- No exact coordinates exposed to other users
- Distances are bucketed (e.g., "< 1 km", "~5 km")
- Location precision reduced before storage
- Stale locations automatically excluded
- User privacy settings respected

Rate Limiting:
- Location updates throttled to 1 per 30 seconds
- Prevents tracking via frequent updates
"""
from fastapi import APIRouter, Depends, Query
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_location_service import LocationService, LocationUpdateRequest

router = APIRouter(prefix="/api/location", tags=["Luveloop Location"])


@router.post("/update")
async def update_location(data: LocationUpdateRequest, user: TBUser = Depends(get_current_user)):
    """
    Update user's current location.
    
    Privacy measures:
    - Coordinates precision reduced before storage (~100m accuracy)
    - Rate limited to 1 update per 30 seconds
    - Location marked with TTL for freshness tracking
    
    Returns:
    - status: "updated" or "throttled"
    - updated_at: ISO timestamp
    
    NOTE: Response does NOT include coordinates for privacy.
    """
    return await LocationService.update_location(
        user_id=str(user.id),
        lat=data.latitude,
        lng=data.longitude
    )


@router.get("/nearby")
async def get_nearby_users(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: int = Query(50, ge=1, le=500, description="Search radius in km"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    user: TBUser = Depends(get_current_user)
):
    """
    Get nearby users based on location and preferences.
    
    Privacy guarantees:
    - Distances are BUCKETED (not exact): "< 1 km", "~5 km", etc.
    - No coordinates returned for any user
    - Users can hide from search (privacy setting)
    - Users can hide their distance (privacy setting)
    - Only users with FRESH locations included (15 min TTL)
    
    Filters applied:
    - Gender preference match
    - Age range preference
    - Max distance preference
    - Active users only
    - Fresh location only (not stale)
    
    Returns:
    - users: List of nearby users with public profile data
    - count: Number of users found
    """
    users = await LocationService.get_nearby_users(
        user_id=str(user.id),
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        limit=limit
    )
    
    return {
        "users": users,
        "count": len(users),
        "privacy_note": "Distances are approximate for privacy"
    }


@router.get("/freshness")
async def check_location_freshness(user: TBUser = Depends(get_current_user)):
    """
    Check if current user's location is fresh.
    
    Location is considered fresh if updated within TTL (15 minutes).
    Stale locations are excluded from nearby searches.
    
    Use this to determine if location update is needed.
    """
    is_fresh = await LocationService.is_location_fresh_redis(str(user.id))
    
    return {
        "is_fresh": is_fresh,
        "ttl_seconds": 900,
        "recommendation": "Update location every 5-10 minutes for best results" if not is_fresh else "Location is current"
    }


@router.delete("/clear")
async def clear_location(user: TBUser = Depends(get_current_user)):
    """
    Clear user's location (go invisible on map).
    
    This marks location as stale and sets user offline.
    User will not appear in nearby searches until location is updated.
    """
    await LocationService.mark_location_stale(str(user.id))
    
    return {
        "status": "cleared",
        "message": "Your location has been cleared. You will not appear in nearby searches."
    }
