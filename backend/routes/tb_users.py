from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List
import base64
import uuid
from datetime import datetime

from backend.models.tb_user import TBUser, Gender, Intent, Preferences, UserSettings, NotificationSettings, PrivacySettings, SafetySettings
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


@router.post("/upload-photo")
async def upload_photo(file: UploadFile = File(...), user: TBUser = Depends(get_current_user)):
    """Upload a profile photo"""
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read file content
    content = await file.read()
    
    # Validate file size (max 5MB)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be less than 5MB")
    
    # Convert to base64 data URL
    base64_content = base64.b64encode(content).decode('utf-8')
    data_url = f"data:{file.content_type};base64,{base64_content}"
    
    # Add to user's profile pictures (keep only last 5)
    if user.profile_pictures is None:
        user.profile_pictures = []
    
    # Add new photo at the beginning
    user.profile_pictures.insert(0, data_url)
    
    # Keep only 5 photos max
    user.profile_pictures = user.profile_pictures[:5]
    
    await user.save()
    
    return {
        "message": "Photo uploaded successfully",
        "profile_pictures": user.profile_pictures
    }


# ========== USER SETTINGS ENDPOINTS ==========

class UpdateSettingsRequest(BaseModel):
    notifications: Optional[dict] = None
    privacy: Optional[dict] = None
    safety: Optional[dict] = None
    dark_mode: Optional[bool] = None
    language: Optional[str] = None


@router.get("/settings")
async def get_user_settings(user: TBUser = Depends(get_current_user)):
    """Get current user's settings (notifications, privacy, safety)"""
    # Ensure settings exist (for older users without settings)
    if not hasattr(user, 'settings') or user.settings is None:
        user.settings = UserSettings()
        await user.save()
    
    return {
        "settings": user.settings.model_dump()
    }


@router.put("/settings")
async def update_user_settings(data: UpdateSettingsRequest, user: TBUser = Depends(get_current_user)):
    """Update user's settings (notifications, privacy, safety)"""
    # Ensure settings exist
    if not hasattr(user, 'settings') or user.settings is None:
        user.settings = UserSettings()
    
    # Update notifications
    if data.notifications is not None:
        for key, value in data.notifications.items():
            if hasattr(user.settings.notifications, key):
                setattr(user.settings.notifications, key, value)
    
    # Update privacy
    if data.privacy is not None:
        for key, value in data.privacy.items():
            if hasattr(user.settings.privacy, key):
                setattr(user.settings.privacy, key, value)
    
    # Update safety
    if data.safety is not None:
        for key, value in data.safety.items():
            if hasattr(user.settings.safety, key):
                setattr(user.settings.safety, key, value)
    
    # Update other settings
    if data.dark_mode is not None:
        user.settings.dark_mode = data.dark_mode
    if data.language is not None:
        user.settings.language = data.language
    
    await user.save()
    
    return {
        "message": "Settings updated",
        "settings": user.settings.model_dump()
    }
