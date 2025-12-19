from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from backend.models.app_settings import AppSettings
from backend.routes.tb_admin_auth import get_current_admin

router = APIRouter(prefix="/api/admin/settings", tags=["TrueBond Admin Settings"])


class PackageUpdate(BaseModel):
    id: str
    name: str
    coins: int
    price_inr: int
    discount: int = 0
    popular: bool = False


class SettingsUpdate(BaseModel):
    # Pricing
    message_cost: Optional[int] = None
    audio_call_cost_per_min: Optional[int] = None
    video_call_cost_per_min: Optional[int] = None
    signup_bonus: Optional[int] = None
    
    # Packages
    packages: Optional[List[PackageUpdate]] = None
    
    # Matching
    default_search_radius: Optional[int] = None
    max_search_radius: Optional[int] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    
    # Safety
    auto_moderation: Optional[bool] = None
    profanity_filter: Optional[bool] = None
    photo_verification: Optional[bool] = None
    
    # App status
    maintenance_mode: Optional[bool] = None


@router.get("")
async def get_settings(
    admin: dict = Depends(get_current_admin)
):
    """Get current app settings"""
    settings = await AppSettings.get_settings()
    
    return {
        # General
        "appName": "TrueBond",
        "tagline": "Real connections, meaningful bonds",
        "maintenanceMode": settings.maintenance_mode,
        
        # Matching
        "defaultSearchRadius": settings.default_search_radius,
        "maxSearchRadius": settings.max_search_radius,
        "minAge": settings.min_age,
        "maxAge": settings.max_age,
        
        # Credits
        "signupBonus": settings.signup_bonus,
        "messageCost": settings.message_cost,
        "audioCallCost": settings.audio_call_cost_per_min,
        "videoCallCost": settings.video_call_cost_per_min,
        
        # Packages
        "packages": settings.packages,
        
        # Safety
        "autoModeration": settings.auto_moderation,
        "profanityFilter": settings.profanity_filter,
        "photoVerification": settings.photo_verification
    }


@router.put("")
async def update_settings(
    updates: SettingsUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update app settings"""
    # Only super_admin can update settings
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admins can update settings")
    
    settings = await AppSettings.get_settings()
    
    # Update provided fields
    update_data = updates.model_dump(exclude_none=True)
    
    if "packages" in update_data:
        settings.packages = [p.model_dump() if hasattr(p, 'model_dump') else p for p in update_data["packages"]]
        del update_data["packages"]
    
    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    settings.updated_at = datetime.now(timezone.utc)
    settings.updated_by = admin["email"]
    await settings.save()
    
    return {"success": True, "message": "Settings updated successfully"}


@router.get("/pricing")
async def get_pricing():
    """Public endpoint to get pricing info (for frontend)"""
    settings = await AppSettings.get_settings()
    
    return {
        "messageCost": settings.message_cost,
        "audioCallCostPerMin": settings.audio_call_cost_per_min,
        "videoCallCostPerMin": settings.video_call_cost_per_min,
        "signupBonus": settings.signup_bonus,
        "packages": settings.packages
    }
