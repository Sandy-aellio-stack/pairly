from fastapi import APIRouter, Depends, Query
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_location_service import LocationService, LocationUpdateRequest

router = APIRouter(prefix="/api/location", tags=["TrueBond Location"])


@router.post("/update")
async def update_location(data: LocationUpdateRequest, user: TBUser = Depends(get_current_user)):
    """Update user's current location"""
    return await LocationService.update_location(
        user_id=str(user.id),
        lat=data.latitude,
        lng=data.longitude
    )


@router.get("/nearby")
async def get_nearby_users(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: int = Query(50, ge=1, le=500, description="Search radius in km"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    user: TBUser = Depends(get_current_user)
):
    """
    Get nearby users based on location and preferences.
    - Filters by user's gender preference
    - Filters by age range preference
    - Respects max distance preference
    - Excludes current user
    - NEVER returns address, email, or mobile
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
        "search_params": {
            "lat": lat,
            "lng": lng,
            "radius_km": radius_km
        }
    }
