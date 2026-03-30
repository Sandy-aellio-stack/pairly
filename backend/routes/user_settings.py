from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from beanie import PydanticObjectId
from backend.models.user_settings import UserSettings
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    notifications_messages: Optional[bool] = None
    notifications_matches: Optional[bool] = None
    notifications_nearby_users: Optional[bool] = None
    
    privacy_show_online_status: Optional[bool] = None
    privacy_show_last_seen: Optional[bool] = None
    privacy_show_distance: Optional[bool] = None
    
    safety_block_screenshots: Optional[bool] = None
    safety_verified_matches_only: Optional[bool] = None
    safety_hide_from_search: Optional[bool] = None

@router.get("")
async def get_settings(current_user: TBUser = Depends(get_current_user)):
    """Fetch user settings, create defaults if not exist"""
    try:
        settings = await UserSettings.find_one({"user_id": current_user.id})
        
        if not settings:
            # Create with defaults
            settings = UserSettings(
                user_id=current_user.id
            )
            await settings.insert()
            # Link back to user if using legacy model (optional)
            # current_user.settings_id = settings.id
            # await current_user.save()
        
        return {"success": True, "settings": settings.dict()}
    except Exception as e:
        print(f"Error fetching settings: {str(e)}")
        return {"success": False, "message": str(e)}

@router.post("")
async def update_settings(
    update_data: SettingsUpdate,
    current_user: TBUser = Depends(get_current_user)
):
    """Update user settings (partial update)"""
    return await _process_settings_update(update_data, current_user)

@router.put("/notifications")
async def update_notifications(
    update_data: Dict[str, bool],
    current_user: TBUser = Depends(get_current_user)
):
    """Granular update for notifications"""
    # Map incoming keys to model field names
    mapped_data = {}
    for k, v in update_data.items():
        mapped_data[f"notifications_{k}"] = v
    return await _process_settings_update(SettingsUpdate(**mapped_data), current_user)

@router.put("/privacy")
async def update_privacy(
    update_data: Dict[str, bool],
    current_user: TBUser = Depends(get_current_user)
):
    """Granular update for privacy"""
    mapped_data = {}
    for k, v in update_data.items():
        if k == "show_online": mapped_data["privacy_show_online_status"] = v
        else: mapped_data[f"privacy_{k}"] = v
    return await _process_settings_update(SettingsUpdate(**mapped_data), current_user)

@router.put("/safety")
async def update_safety(
    update_data: Dict[str, bool],
    current_user: TBUser = Depends(get_current_user)
):
    """Granular update for safety"""
    mapped_data = {}
    for k, v in update_data.items():
        if k == "verified_matches_only": mapped_data["safety_verified_matches_only"] = v
        else: mapped_data[f"safety_{k}"] = v
    return await _process_settings_update(SettingsUpdate(**mapped_data), current_user)

async def _process_settings_update(update_data: SettingsUpdate, current_user: TBUser):
    """Shared logic for updating settings"""
    try:
        settings = await UserSettings.find_one({"user_id": current_user.id})
        
        if not settings:
            # Create if not exists
            settings = UserSettings(user_id=current_user.id)
            await settings.insert()
        
        # Map flattened to nested
        data_dict = update_data.dict(exclude_unset=True)
        
        # Notifications
        for k, v in data_dict.items():
            if k.startswith("notifications_"):
                key = k.replace("notifications_", "")
                # Map to correct model fields
                if key == "messages": key = "new_messages"
                elif key == "matches": key = "new_matches"
                elif key == "nearby": key = "nearby_users"
                
                settings.notifications[key] = v
        
        # Privacy
        if "privacy_show_online_status" in data_dict:
            settings.privacy["show_online_status"] = data_dict["privacy_show_online_status"]
        if "privacy_show_last_seen" in data_dict:
            settings.privacy["show_last_seen"] = data_dict["privacy_show_last_seen"]
        if "privacy_show_distance" in data_dict:
            settings.privacy["show_distance"] = data_dict["privacy_show_distance"]
        
        # Safety
        if "safety_block_screenshots" in data_dict:
            settings.safety["block_screenshots"] = data_dict["safety_block_screenshots"]
        if "safety_verified_matches_only" in data_dict:
            settings.safety["verified_matches_only"] = data_dict["safety_verified_matches_only"]
        if "safety_hide_from_search" in data_dict:
            settings.safety["hide_from_search"] = data_dict["safety_hide_from_search"]
        
        # Save changes!
        await settings.save()
        
        return {"success": True, "settings": settings.dict()}
    except Exception as e:
        import logging
        logging.getLogger("settings").error(f"Error updating settings: {str(e)}")
        return {"success": False, "message": str(e)}

