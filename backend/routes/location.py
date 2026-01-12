from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timezone
from backend.models.user import User
from backend.models.profile import Profile
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/api/legacy/location", tags=["Legacy Location"])


class LocationUpdateRequest(BaseModel):
    lat: float
    lng: float


class VisibilityRequest(BaseModel):
    is_visible_on_map: bool


@router.post("/update")
async def update_location(req: LocationUpdateRequest, user: User = Depends(get_current_user)):
    """Update user's current location"""
    profile = await Profile.find_one(Profile.user_id == user.id)
    if not profile:
        raise HTTPException(404, "Profile not found. Please create a profile first.")
    
    # GeoJSON format: [longitude, latitude]
    profile.location = {
        "type": "Point",
        "coordinates": [req.lng, req.lat]
    }
    profile.updated_at = datetime.now(timezone.utc)
    profile.last_seen = datetime.now(timezone.utc)
    await profile.save()
    
    return {
        "status": "updated",
        "location": {
            "lat": req.lat,
            "lng": req.lng
        }
    }


@router.post("/visibility")
async def update_visibility(req: VisibilityRequest, user: User = Depends(get_current_user)):
    """Toggle map visibility"""
    profile = await Profile.find_one(Profile.user_id == user.id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    
    profile.is_visible_on_map = req.is_visible_on_map
    profile.updated_at = datetime.now(timezone.utc)
    await profile.save()
    
    return {
        "status": "updated",
        "is_visible_on_map": profile.is_visible_on_map
    }


@router.get("/me")
async def get_my_location(user: User = Depends(get_current_user)):
    """Get current user's location"""
    profile = await Profile.find_one(Profile.user_id == user.id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    
    location = None
    if profile.location and "coordinates" in profile.location:
        location = {
            "lat": profile.location["coordinates"][1],
            "lng": profile.location["coordinates"][0]
        }
    
    return {
        "location": location,
        "is_visible_on_map": getattr(profile, 'is_visible_on_map', True)
    }
