from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.models.tb_user import TBUser, UserSettings, NotificationSettings, PrivacySettings, SafetySettings
from backend.routes.tb_auth import get_current_user
import logging

router = APIRouter(prefix="/api/settings", tags=["settings"])
logger = logging.getLogger("settings")

class SettingsUpdate(BaseModel):
    notifications: Optional[Dict[str, bool]] = None
    privacy: Optional[Dict[str, bool]] = None
    safety: Optional[Dict[str, bool]] = None
    dark_mode: Optional[bool] = None
    language: Optional[str] = None

@router.get("")
async def get_settings(current_user: TBUser = Depends(get_current_user)):
    """
    Fetch user settings directly from the TBUser document.
    """
    try:
        # User document always has settings due to default_factory
        return {
            "success": True,
            "settings": current_user.settings.dict()
        }
    except Exception as e:
        logger.error(f"Error fetching settings for {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch settings")

@router.put("")
@router.post("")
async def update_settings(
    update_data: SettingsUpdate,
    current_user: TBUser = Depends(get_current_user)
):
    """
    Unified settings update (partial).
    Updates notifications, privacy, safety, and general settings.
    """
    try:
        # Handle Notifications
        if update_data.notifications:
            for k, v in update_data.notifications.items():
                if hasattr(current_user.settings.notifications, k):
                    setattr(current_user.settings.notifications, k, v)
        
        # Handle Privacy
        if update_data.privacy:
            for k, v in update_data.privacy.items():
                if hasattr(current_user.settings.privacy, k):
                    setattr(current_user.settings.privacy, k, v)
        
        # Handle Safety
        if update_data.safety:
            for k, v in update_data.safety.items():
                if hasattr(current_user.settings.safety, k):
                    setattr(current_user.settings.safety, k, v)

        # Handle General
        if update_data.dark_mode is not None:
            current_user.settings.dark_mode = update_data.dark_mode
        if update_data.language:
            current_user.settings.language = update_data.language

        # Save the user document with updated settings
        await current_user.save()
        
        logger.info(f"Settings updated for user {current_user.id}")
        return {
            "success": True,
            "message": "Settings updated successfully",
            "settings": current_user.settings.dict()
        }
    except Exception as e:
        logger.error(f"Error updating settings for {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.put("/{category}")
async def update_settings_category(
    category: str,
    update_data: Dict[str, Any],
    current_user: TBUser = Depends(get_current_user)
):
    """
    Update a specific category of settings (e.g., /api/settings/notifications).
    """
    if category not in ["notifications", "privacy", "safety"]:
        raise HTTPException(status_code=400, detail="Invalid settings category")
    
    try:
        target = getattr(current_user.settings, category)
        for k, v in update_data.items():
            if hasattr(target, k):
                setattr(target, k, v)
        
        await current_user.save()
        return {
            "success": True, 
            "message": f"{category.capitalize()} settings updated",
            "settings": current_user.settings.dict()
        }
    except Exception as e:
        logger.error(f"Error updating {category} settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update {category} settings")
