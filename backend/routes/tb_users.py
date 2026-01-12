from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List
import base64
import uuid
from datetime import datetime, timezone

from backend.models.tb_user import TBUser, Gender, Intent, Preferences, UserSettings, NotificationSettings, PrivacySettings, SafetySettings
from backend.models.tb_report import TBReport, ReportStatus
from backend.routes.tb_auth import get_current_user
from backend.services.tb_location_service import PrivacyLocation

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


class BlockUserRequest(BaseModel):
    reason: Optional[str] = None


class ReportUserRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)
    report_type: str = "profile"


@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str, current_user: TBUser = Depends(get_current_user)):
    """
    Get a user's public profile.
    
    Privacy & Safety:
    - Only returns public fields (NO email, phone, address, exact location)
    - Blocked users cannot view each other
    - Users hidden from search cannot be viewed
    - Distance shown with privacy bucketing
    - Respects user's privacy settings
    """
    # Cannot view own profile via this endpoint
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Use /api/users/me for own profile")
    
    # Find target user
    user = await TBUser.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if target user is hidden from search/discovery
    if hasattr(user, 'settings') and user.settings:
        if user.settings.safety.hide_from_search:
            raise HTTPException(status_code=404, detail="User not found")
    
    # Check if either user has blocked the other
    is_blocked = await _check_blocked(str(current_user.id), user_id)
    if is_blocked:
        raise HTTPException(status_code=403, detail="Cannot view this profile")
    
    # Get privacy settings
    privacy = user.settings.privacy if hasattr(user, 'settings') and user.settings else PrivacySettings()
    
    # Build response with privacy controls
    response = {
        "id": str(user.id),
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "bio": user.bio,
        "profile_pictures": user.profile_pictures or [],
        "intent": user.intent,
        "is_verified": user.is_verified,
    }
    
    # Online status (respect privacy)
    if privacy.show_online:
        response["is_online"] = user.is_online
    else:
        response["is_online"] = None
    
    # Last seen (respect privacy)
    if privacy.show_last_seen and hasattr(user, 'location_updated_at') and user.location_updated_at:
        response["last_active"] = _format_last_active(user.location_updated_at)
    else:
        response["last_active"] = None
    
    # Distance (respect privacy + calculate if possible)
    if privacy.show_distance and current_user.location and user.location:
        current_coords = current_user.location.coordinates
        target_coords = user.location.coordinates
        
        distance_km = PrivacyLocation.calculate_distance(
            current_coords[1], current_coords[0],  # [lng, lat] -> lat, lng
            target_coords[1], target_coords[0]
        ) if hasattr(PrivacyLocation, 'calculate_distance') else None
        
        if distance_km is not None:
            from backend.services.tb_location_service import LocationService
            response["distance_km"] = PrivacyLocation.bucket_distance(distance_km)
            response["distance_display"] = PrivacyLocation.format_distance_display(distance_km)
    else:
        response["distance_km"] = None
        response["distance_display"] = "Distance hidden"
    
    # Location freshness (without revealing when)
    if hasattr(user, 'location_updated_at') and user.location_updated_at:
        response["location_fresh"] = PrivacyLocation.is_location_fresh(user.location_updated_at)
    else:
        response["location_fresh"] = False
    
    return response


@router.get("/me")
async def get_own_profile(current_user: TBUser = Depends(get_current_user)):
    """
    Get current user's own profile (includes credits, settings).
    """
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "age": current_user.age,
        "gender": current_user.gender,
        "bio": current_user.bio,
        "profile_pictures": current_user.profile_pictures or [],
        "intent": current_user.intent,
        "email": current_user.email,
        "mobile_number": current_user.mobile_number,
        "preferences": current_user.preferences.model_dump(),
        "settings": current_user.settings.model_dump() if current_user.settings else {},
        "credits_balance": current_user.credits_balance,
        "is_verified": current_user.is_verified,
        "is_online": current_user.is_online,
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/block/{user_id}")
async def block_user(user_id: str, data: BlockUserRequest = None, current_user: TBUser = Depends(get_current_user)):
    """
    Block a user. Blocked users:
    - Cannot view each other's profiles
    - Cannot send messages to each other
    - Won't appear in each other's nearby/discovery
    """
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    target = await TBUser.get(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store block in a separate collection for scalability
    from backend.models.user_block import UserBlock
    
    # Check if already blocked
    existing = await UserBlock.find_one({
        "blocker_id": str(current_user.id),
        "blocked_id": user_id
    })
    
    if existing:
        return {"message": "User already blocked", "blocked": True}
    
    # Create block record
    block = UserBlock(
        blocker_id=str(current_user.id),
        blocked_id=user_id,
        reason=data.reason if data else None
    )
    await block.insert()
    
    return {"message": "User blocked", "blocked": True}


@router.delete("/block/{user_id}")
async def unblock_user(user_id: str, current_user: TBUser = Depends(get_current_user)):
    """Unblock a user"""
    from backend.models.user_block import UserBlock
    
    result = await UserBlock.find_one({
        "blocker_id": str(current_user.id),
        "blocked_id": user_id
    })
    
    if result:
        await result.delete()
        return {"message": "User unblocked", "blocked": False}
    
    return {"message": "User was not blocked", "blocked": False}


@router.get("/blocked")
async def get_blocked_users(current_user: TBUser = Depends(get_current_user)):
    """Get list of users blocked by current user"""
    from backend.models.user_block import UserBlock
    
    blocks = await UserBlock.find({"blocker_id": str(current_user.id)}).to_list()
    
    blocked_users = []
    for block in blocks:
        user = await TBUser.get(block.blocked_id)
        if user:
            blocked_users.append({
                "id": str(user.id),
                "name": user.name,
                "profile_picture": user.profile_pictures[0] if user.profile_pictures else None,
                "blocked_at": block.created_at.isoformat()
            })
    
    return {"blocked_users": blocked_users, "count": len(blocked_users)}


@router.post("/report/{user_id}")
async def report_user(user_id: str, data: ReportUserRequest, current_user: TBUser = Depends(get_current_user)):
    """
    Report a user for inappropriate content/behavior.
    Reports are reviewed by moderators.
    """
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    target = await TBUser.get(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    from backend.models.tb_report import TBReport, ReportType
    
    report = TBReport(
        report_type=ReportType.PROFILE,
        reported_user_id=user_id,
        reported_by_user_id=str(current_user.id),
        reason=data.reason
    )
    await report.insert()
    
    return {"message": "Report submitted", "report_id": str(report.id)}


async def _check_blocked(user_id1: str, user_id2: str) -> bool:
    """Check if either user has blocked the other"""
    try:
        from backend.models.user_block import UserBlock
        
        # Check if user1 blocked user2 OR user2 blocked user1
        block = await UserBlock.find_one({
            "$or": [
                {"blocker_id": user_id1, "blocked_id": user_id2},
                {"blocker_id": user_id2, "blocked_id": user_id1}
            ]
        })
        
        return block is not None
    except Exception:
        # If UserBlock model doesn't exist yet, no blocks
        return False


def _format_last_active(dt: datetime) -> str:
    """Format last active time with privacy"""
    if not dt:
        return None
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if diff.total_seconds() < 300:
        return "Active now"
    elif diff.total_seconds() < 3600:
        return "Active recently"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"Active {hours}h ago"
    else:
        days = int(diff.total_seconds() / 86400)
        if days == 1:
            return "Active yesterday"
        return f"Active {days}d ago"


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


# ========== FCM TOKEN MANAGEMENT ENDPOINTS ==========

class RegisterFCMTokenRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=500)


class DeleteFCMTokenRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=500)


@router.post("/fcm-token")
async def register_fcm_token(data: RegisterFCMTokenRequest, user: TBUser = Depends(get_current_user)):
    """
    Register an FCM device token for push notifications.
    
    - Supports multiple devices per user
    - Replaces duplicate tokens automatically
    - Max 5 tokens per user (oldest removed if exceeded)
    
    Call this:
    - After user grants notification permission
    - On app launch if permission already granted
    - When FCM token is refreshed
    """
    # Initialize fcm_tokens if not exists
    if not hasattr(user, 'fcm_tokens') or user.fcm_tokens is None:
        user.fcm_tokens = []
    
    token = data.token.strip()
    
    # Don't add duplicate tokens
    if token in user.fcm_tokens:
        return {"message": "Token already registered", "registered": True}
    
    # Add new token
    user.fcm_tokens.append(token)
    
    # Keep only the last 5 tokens (remove oldest if exceeded)
    if len(user.fcm_tokens) > 5:
        user.fcm_tokens = user.fcm_tokens[-5:]
    
    await user.save()
    
    return {"message": "FCM token registered", "registered": True, "device_count": len(user.fcm_tokens)}


@router.delete("/fcm-token")
async def unregister_fcm_token(data: DeleteFCMTokenRequest, user: TBUser = Depends(get_current_user)):
    """
    Unregister an FCM device token.
    
    Call this:
    - On user logout
    - When user disables notifications
    - On app uninstall (if detectable)
    """
    if not hasattr(user, 'fcm_tokens') or user.fcm_tokens is None:
        return {"message": "No tokens registered", "removed": False}
    
    token = data.token.strip()
    
    if token in user.fcm_tokens:
        user.fcm_tokens.remove(token)
        await user.save()
        return {"message": "FCM token removed", "removed": True, "device_count": len(user.fcm_tokens)}
    
    return {"message": "Token not found", "removed": False}


@router.delete("/fcm-tokens/all")
async def unregister_all_fcm_tokens(user: TBUser = Depends(get_current_user)):
    """
    Unregister all FCM tokens for the user.
    
    Use this for:
    - Complete logout from all devices
    - Disabling all push notifications
    """
    if not hasattr(user, 'fcm_tokens') or not user.fcm_tokens:
        return {"message": "No tokens to remove", "removed": 0}
    
    removed_count = len(user.fcm_tokens)
    user.fcm_tokens = []
    await user.save()
    
    return {"message": "All FCM tokens removed", "removed": removed_count}
