from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List
import base64
import uuid
from datetime import datetime, timezone
from bson import ObjectId

from backend.models.tb_user import TBUser, Gender, Intent, Preferences, UserSettings, NotificationSettings, PrivacySettings, SafetySettings
from backend.models.tb_report import TBReport, ReportStatus
from backend.routes.tb_auth import get_current_user
from backend.services.tb_location_service import PrivacyLocation

router = APIRouter(prefix="/api/users", tags=["Users"])


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


# NOTE: More specific routes must come BEFORE generic /{user_id} route
# FastAPI matches routes in order of definition

@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    """
    Get a user's public profile.
    This route MUST come before /{user_id} to avoid conflicts.
    """
    from backend.utils.objectid_utils import validate_object_id
    user_oid = validate_object_id(user_id)
    user = await TBUser.get(user_oid)
            
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Format location if exists
    location_data = None
    if user.location and user.location.coordinates:
        location_data = {
            "lat": user.location.coordinates[1],
            "lng": user.location.coordinates[0]
        }

    # Return public profile data
    return { 
        "id": str(user.id), 
        "name": user.name, 
        "age": user.age,
        "gender": user.gender,
        "bio": user.bio,
        "profile_picture": user.profile_pictures[0] if user.profile_pictures else None,
        "profile_pictures": user.profile_pictures or [],
        "intent": user.intent,
        "is_verified": getattr(user, "is_verified", False),
        "is_online": user.is_online,
        "status": "suspended" if user.is_suspended else "active",
        "credits": user.credits_balance,
        "location": location_data
    }


@router.get("/dashboard-stats")
async def get_dashboard_stats(current_user: TBUser = Depends(get_current_user)):
    """
    Get dashboard statistics for the current user.
    """
    try:
        from backend.models.tb_message import TBMessage
        messages_sent = await TBMessage.find(TBMessage.sender_id == str(current_user.id)).count()
    except Exception:
        messages_sent = 0

    return {
        "messages_sent": messages_sent,
        "matches": 0,
        "coins": current_user.credits_balance,
        "profile_views": 0,
    }


@router.get("/nearby")
async def get_nearby_users_simple(
    limit: int = 20,
    current_user: TBUser = Depends(get_current_user)
):
    """
    Get nearby/active users for the home page feed.
    Excludes users who hide from search, respects their privacy settings.
    """
    from beanie import PydanticObjectId

    blocked_ids = await _get_blocked_user_ids(str(current_user.id))
    blocked_ids.add(str(current_user.id))

    blocked_oids = []
    for uid in blocked_ids:
        try:
            blocked_oids.append(PydanticObjectId(uid))
        except Exception:
            pass

    query = {"is_active": True, "settings.safety.hide_from_search": {"$ne": True}}
    if blocked_oids:
        query["_id"] = {"$nin": blocked_oids}

    users = await TBUser.find(query).sort(-TBUser.created_at).limit(limit).to_list()

    result = []
    for u in users:
        privacy = u.settings.privacy if u.settings and u.settings.privacy else None
        show_online = privacy.show_online if privacy else True
        show_last_seen = privacy.show_last_seen if privacy else True
        result.append({
            "id": str(u.id),
            "name": u.name,
            "age": u.age,
            "bio": u.bio or "",
            "profile_picture": u.profile_pictures[0] if u.profile_pictures else None,
            "is_online": (getattr(u, "is_online", False) or False) if show_online else False,
            "last_seen": (u.last_seen.isoformat() if u.last_seen else None) if show_last_seen else None,
            "intent": u.intent,
            "is_verified": getattr(u, "is_verified", False),
        })

    return {"users": result, "total": len(result)}


@router.get("/suggestions")
async def get_suggestions(
    limit: int = 3,
    current_user: TBUser = Depends(get_current_user)
):
    """
    Get suggested users / today's matches.
    Excludes hidden users and respects privacy settings.
    """
    from beanie import PydanticObjectId

    blocked_ids = await _get_blocked_user_ids(str(current_user.id))
    blocked_ids.add(str(current_user.id))

    blocked_oids = []
    for uid in blocked_ids:
        try:
            blocked_oids.append(PydanticObjectId(uid))
        except Exception:
            pass

    base_query = {"is_active": True, "settings.safety.hide_from_search": {"$ne": True}}
    if blocked_oids:
        base_query["_id"] = {"$nin": blocked_oids}

    query = {**base_query, "is_online": True}
    users = await TBUser.find(query).limit(limit).to_list()

    if len(users) < limit:
        extra = await TBUser.find(base_query).limit(limit - len(users)).to_list()
        existing_ids = {str(u.id) for u in users}
        users += [u for u in extra if str(u.id) not in existing_ids]

    result = []
    for u in users:
        privacy = u.settings.privacy if u.settings and u.settings.privacy else None
        show_online = privacy.show_online if privacy else True
        show_last_seen = privacy.show_last_seen if privacy else True
        result.append({
            "id": str(u.id),
            "name": u.name,
            "age": u.age,
            "bio": u.bio or "",
            "profile_picture": u.profile_pictures[0] if u.profile_pictures else None,
            "profile_pictures": u.profile_pictures or [],
            "is_online": (getattr(u, "is_online", False) or False) if show_online else False,
            "last_seen": (u.last_seen.isoformat() if u.last_seen else None) if show_last_seen else None,
            "intent": u.intent,
            "is_verified": getattr(u, "is_verified", False),
        })

    return {"users": result}


@router.get("/streak")
async def get_login_streak(current_user: TBUser = Depends(get_current_user)):
    """
    Get the current user's login streak.
    Calculated from last_login_at field.
    """
    from datetime import timezone as tz, timedelta

    streak_days = 1
    now = datetime.now(timezone.utc)

    if current_user.last_login_at:
        last = current_user.last_login_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        days_diff = (now.date() - last.date()).days
        if days_diff == 0:
            streak_days = 1
        elif days_diff <= 1:
            streak_days = 2
        else:
            streak_days = 1

    next_reward = 5 if streak_days < 5 else 10

    return {
        "streak_days": streak_days,
        "next_reward": next_reward,
    }


@router.get("/{user_id}")
async def get_user_by_id(user_id: str):
    """
    Get a user's basic profile by ID.
    """
    from backend.utils.objectid_utils import validate_object_id
    user_oid = validate_object_id(user_id)
    user = await TBUser.get(user_oid)
            
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return { 
        "id": str(user.id), 
        "name": user.name, 
        "credits": user.credits_balance 
    }


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
        "profile_picture": current_user.profile_pictures[0] if current_user.profile_pictures else None,
        "profile_pictures": current_user.profile_pictures or [],
        "intent": current_user.intent,
        "email": current_user.email,
        "mobile_number": current_user.mobile_number,
        "preferences": current_user.preferences.model_dump(),
        "settings": current_user.settings.model_dump() if current_user.settings else {},
        "credits": current_user.credits_balance,
        "is_verified": current_user.is_verified,
        "is_online": current_user.is_online,
        "status": "suspended" if current_user.is_suspended else "active",
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/block/{user_id}")
async def block_user(user_id: str, data: BlockUserRequest = None, current_user: TBUser = Depends(get_current_user)):
    """
    Block a user with strict ID consistency.
    """
    from beanie import PydanticObjectId
    from bson.errors import InvalidId
    
    try:
        user_oid = PydanticObjectId(user_id)
    except (InvalidId, Exception) as e:
        print(f"ERROR: Invalid block user ID '{user_id}': {e}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    if current_user.id == user_oid:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    target = await TBUser.get(user_oid)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store block in a separate collection for scalability
    from backend.models.user_block import UserBlock
    
    # Check if already blocked
    existing = await UserBlock.find_one({
        "blocker_id": current_user.id,
        "blocked_id": user_oid
    })
    
    if existing:
        return {"message": "User already blocked", "blocked": True}
    
    # Create block record
    block = UserBlock(
        blocker_id=current_user.id,
        blocked_id=user_oid,
        reason=data.reason if data else None
    )
    await block.insert()
    
    return {"message": "User blocked", "blocked": True}


@router.delete("/block/{user_id}")
async def unblock_user(user_id: str, current_user: TBUser = Depends(get_current_user)):
    """Unblock a user with strict ID consistency"""
    from beanie import PydanticObjectId
    from bson.errors import InvalidId
    
    try:
        user_oid = PydanticObjectId(user_id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    from backend.models.user_block import UserBlock
    
    result = await UserBlock.find_one({
        "blocker_id": current_user.id,
        "blocked_id": user_oid
    })
    
    if result:
        await result.delete()
        return {"message": "User unblocked", "blocked": False}
    
    return {"message": "User was not blocked", "blocked": False}


@router.get("/blocked")
async def get_blocked_users(current_user: TBUser = Depends(get_current_user)):
    """Get list of users blocked by current user"""
    from backend.models.user_block import UserBlock
    
    blocks = await UserBlock.find({"blocker_id": current_user.id}).to_list()
    
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
    Report a user with strict ID consistency.
    """
    from beanie import PydanticObjectId
    from bson.errors import InvalidId
    
    try:
        user_oid = PydanticObjectId(user_id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    if current_user.id == user_oid:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    target = await TBUser.get(user_oid)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    from backend.models.tb_report import TBReport, ReportType
    
    report = TBReport(
        report_type=ReportType.PROFILE,
        reported_user_id=user_oid,
        reported_by_user_id=current_user.id,
        reason=data.reason
    )
    await report.insert()
    
    return {"message": "Report submitted", "report_id": str(report.id)}


async def _check_blocked(user_id1: str, user_id2: str) -> bool:
    """Check if either user has blocked the other"""
    from beanie import PydanticObjectId
    from bson.errors import InvalidId
    
    try:
        u1_oid = PydanticObjectId(user_id1)
        u2_oid = PydanticObjectId(user_id2)
        
        from backend.models.user_block import UserBlock
        
        # Check if user1 blocked user2 OR user2 blocked user1 using ObjectIds
        block = await UserBlock.find_one({
            "$or": [
                {"blocker_id": u1_oid, "blocked_id": u2_oid},
                {"blocker_id": u2_oid, "blocked_id": u1_oid}
            ]
        })
        
        return block is not None
    except (InvalidId, Exception) as e:
        print(f"DEBUG: Block check error (safe fallback to False): {e}")
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
    if data.name:
        user.name = data.name
    if data.bio is not None:
        user.bio = data.bio
    if data.intent:
        user.intent = data.intent
    if data.profile_pictures is not None:
        user.profile_pictures = data.profile_pictures
    
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    return {"message": "Profile updated", "user": {"id": str(user.id), "name": user.name}}


@router.put("/preferences")
async def update_preferences(data: UpdatePreferencesRequest, user: TBUser = Depends(get_current_user)):
    """Update user's matching preferences"""
    if not user.preferences:
        user.preferences = Preferences()
        
    if data.interested_in:
        user.preferences.interested_in = data.interested_in
    if data.min_age:
        user.preferences.min_age = data.min_age
    if data.max_age:
        user.preferences.max_age = data.max_age
    if data.max_distance_km:
        user.preferences.max_distance_km = data.max_distance_km
        
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    return {"message": "Preferences updated"}


@router.get("/credits")
async def get_credits(user: TBUser = Depends(get_current_user)):
    """Get current user's credit balance"""
    return {
        "credits": user.credits_balance
    }


@router.delete("/account")
async def delete_account(user: TBUser = Depends(get_current_user)):
    """Permanently delete current user's account and all associated data"""
    from backend.models.tb_message import TBMessage, TBConversation
    from backend.routes.tb_notifications import TBNotification
    user_id = str(user.id)

    try:
        await TBMessage.find({"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}).delete()
    except Exception:
        pass

    try:
        await TBConversation.find({"participants": user_id}).delete()
    except Exception:
        pass

    try:
        await TBNotification.find({"user_id": user_id}).delete()
    except Exception:
        pass

    try:
        from backend.models.call_session_v2 import CallSessionV2
        await CallSessionV2.find({"$or": [{"caller_id": user_id}, {"callee_id": user_id}]}).delete()
    except Exception:
        pass

    try:
        from backend.models.user_block import UserBlock
        from beanie import PydanticObjectId
        user_oid = PydanticObjectId(user_id)
        await UserBlock.find({"$or": [{"blocker_id": user_oid}, {"blocked_id": user_oid}]}).delete()
    except Exception:
        pass

    user.is_active = False
    user.is_online = False
    user.bio = None
    user.profile_pictures = []
    await user.save()

    return {"message": "Account deleted successfully"}


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


@router.patch("/settings")
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


# ========== USER SEARCH ENDPOINT ==========

class SearchUsersResponse(BaseModel):
    users: List[dict]
    total: int
    page: int
    limit: int
    has_more: bool


@router.get("/search")
async def search_users(
    q: str = "",
    page: int = 1,
    limit: int = 20,
    current_user: TBUser = Depends(get_current_user)
):
    """
    Search users by name, age, or gender.
    
    - Case-insensitive search
    - Excludes current user
    - Excludes blocked users
    - Paginated results
    """
    if page < 1:
        page = 1
    if limit < 1 or limit > 50:
        limit = 20
    
    skip = (page - 1) * limit
    current_user_id = str(current_user.id)
    
    # Get blocked user IDs (both directions)
    blocked_ids = await _get_blocked_user_ids(current_user_id)
    blocked_ids.add(current_user_id)  # Exclude self
    
    # Convert to ObjectIds
    blocked_object_ids = []
    for uid in blocked_ids:
        try:
            oid = await _str_to_objectid(uid)
            if oid:
                blocked_object_ids.append(oid)
        except:
            pass
    
    # Build search query
    search_query = {"is_active": True, "settings.safety.hide_from_search": {"$ne": True}}
    if blocked_object_ids:
        search_query["_id"] = {"$nin": blocked_object_ids}
    
    # Add text search if query provided
    if q and q.strip():
        search_term = q.strip()
        # Case-insensitive regex search on name
        search_query["name"] = {"$regex": search_term, "$options": "i"}
    
    # Execute search
    try:
        total = await TBUser.find(search_query).count()
        users = await TBUser.find(search_query).skip(skip).limit(limit).to_list()
        
        import logging
        logging.info(f"Search query '{q}' returned {len(users)} users")
    except Exception as e:
        import logging
        logging.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")
    
    # Format results
    user_list = []
    for user in users:
        user_list.append({
            "id": str(user.id),
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "bio": user.bio,
            "profile_picture": user.profile_pictures[0] if user.profile_pictures else None,
            "profile_pictures": user.profile_pictures or [],
            "intent": user.intent,
            "is_verified": user.is_verified if hasattr(user, 'is_verified') else False,
            "is_online": user.is_online if hasattr(user, 'is_online') else False,
            "status": "suspended" if user.is_suspended else "active"
        })
    
    return {
        "users": user_list,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": skip + len(users) < total
    }


# ========== USER FEED ENDPOINT (DASHBOARD) ==========

@router.get("/feed")
async def get_user_feed(
    page: int = 1,
    limit: int = 20,
    current_user: TBUser = Depends(get_current_user)
):
    """
    Get user feed for dashboard/home page.
    
    Returns active users from MongoDB:
    - Excludes self
    - Excludes blocked users
    - Returns ALL active users (no overly restrictive filters)
    - Sorted by recent activity
    - Paginated
    """
    if page < 1:
        page = 1
    if limit < 1 or limit > 50:
        limit = 20
    
    skip = (page - 1) * limit
    current_user_id = str(current_user.id)
    
    # Get blocked user IDs
    blocked_ids = await _get_blocked_user_ids(current_user_id)
    blocked_ids.add(current_user_id)  # Exclude self
    
    # Convert to ObjectIds
    blocked_object_ids = []
    for uid in blocked_ids:
        try:
            oid = await _str_to_objectid(uid)
            if oid:
                blocked_object_ids.append(oid)
        except:
            pass
    
    # Simple query - just active users excluding self and blocked
    feed_query = {"is_active": True}
    if blocked_object_ids:
        feed_query["_id"] = {"$nin": blocked_object_ids}
    
    # Execute query with sorting
    try:
        total = await TBUser.find(feed_query).count()
        users = await TBUser.find(feed_query).sort([
            ("created_at", -1)
        ]).skip(skip).limit(limit).to_list()
        
        import logging
        logging.info(f"Feed query returned {len(users)} users out of {total} total")
    except Exception as e:
        import logging
        logging.error(f"Feed error: {e}")
        # Fallback: try without any filter
        try:
            users = await TBUser.find_all().limit(limit).to_list()
            total = len(users)
        except:
            raise HTTPException(status_code=500, detail="Failed to load feed")
    
    # Format results
    user_list = []
    for user in users:
        user_data = {
            "id": str(user.id),
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "bio": user.bio,
            "profile_picture": user.profile_pictures[0] if user.profile_pictures else None,
            "profile_pictures": user.profile_pictures or [],
            "intent": user.intent,
            "is_verified": user.is_verified if hasattr(user, 'is_verified') else False,
            "is_online": user.is_online if hasattr(user, 'is_online') else False,
            "status": "suspended" if user.is_suspended else "active",
            "last_active": None,
            "distance_km": None,
            "distance_display": None,
        }
        
        # Add location if available
        if hasattr(user, 'location') and user.location:
            coords = user.location.coordinates if hasattr(user.location, 'coordinates') else None
            if coords and len(coords) >= 2:
                user_data["location"] = {
                    "lat": coords[1],
                    "lng": coords[0]
                }
        
        user_list.append(user_data)
    
    return {
        "users": user_list,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": skip + len(users) < total
    }


async def _get_blocked_user_ids(user_id: str) -> set:
    """Get all user IDs that are blocked (both directions)"""
    try:
        from backend.models.user_block import UserBlock
        
        # Get users I blocked
        my_blocks = await UserBlock.find({"blocker_id": user_id}).to_list()
        blocked_by_me = {b.blocked_id for b in my_blocks}
        
        # Get users who blocked me
        their_blocks = await UserBlock.find({"blocked_id": user_id}).to_list()
        blocked_me = {b.blocker_id for b in their_blocks}
        
        return blocked_by_me | blocked_me
    except Exception:
        return set()


async def _str_to_objectid(user_id: str):
    """Convert string to ObjectId for MongoDB queries"""
    try:
        from bson import ObjectId
        return ObjectId(user_id)
    except:
        return user_id
