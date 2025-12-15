from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from backend.models.tb_user import TBUser, Gender, Intent, Preferences
from backend.routes.tb_auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["TrueBond Users"])


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    intent: Optional[Intent] = None
    profile_pictures: Optional[List[str]] = None


class UpdatePreferencesRequest(BaseModel):
    interested_in: Optional[Gender] = None
    min_age: Optional[int] = Field(None, ge=18, le=100)
    max_age: Optional[int] = Field(None, ge=18, le=100)
    max_distance_km: Optional[int] = Field(None, ge=1, le=500)


@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str, current_user: TBUser = Depends(get_current_user)):
    """Get a user's public profile - NO address, email, mobile exposed"""
    user = await TBUser.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "bio": user.bio,
        "profile_pictures": user.profile_pictures,
        "intent": user.intent,
        "is_online": user.is_online,
        "is_verified": user.is_verified
    }


@router.put("/profile")
async def update_profile(data: UpdateProfileRequest, user: TBUser = Depends(get_current_user)):
    """Update current user's profile"""
    if data.name is not None:
        user.name = data.name
    if data.bio is not None:
        user.bio = data.bio
    if data.intent is not None:
        user.intent = data.intent
    if data.profile_pictures is not None:
        user.profile_pictures = data.profile_pictures
    
    await user.save()
    
    return {
        "message": "Profile updated",
        "profile": {
            "name": user.name,
            "bio": user.bio,
            "intent": user.intent,
            "profile_pictures": user.profile_pictures
        }
    }


@router.put("/preferences")
async def update_preferences(data: UpdatePreferencesRequest, user: TBUser = Depends(get_current_user)):
    """Update user's matching preferences"""
    if data.interested_in is not None:
        user.preferences.interested_in = data.interested_in
    if data.min_age is not None:
        user.preferences.min_age = data.min_age
    if data.max_age is not None:
        user.preferences.max_age = data.max_age
    if data.max_distance_km is not None:
        user.preferences.max_distance_km = data.max_distance_km
    
    await user.save()
    
    return {
        "message": "Preferences updated",
        "preferences": user.preferences.model_dump()
    }


@router.get("/credits")
async def get_credits(user: TBUser = Depends(get_current_user)):
    """Get current user's credit balance"""
    return {
        "credits_balance": user.credits_balance
    }


@router.delete("/account")
async def deactivate_account(user: TBUser = Depends(get_current_user)):
    """Deactivate current user's account"""
    user.is_active = False
    user.is_online = False
    await user.save()
    
    return {"message": "Account deactivated"}
