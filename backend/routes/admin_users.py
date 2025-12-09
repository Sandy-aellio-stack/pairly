from fastapi import APIRouter, Depends, Query, Request
from typing import Optional
import logging
from datetime import datetime, timezone
from backend.models.user import User
from backend.models.profile import Profile
from backend.models.credits_transaction import CreditsTransaction
from backend.services.admin_rbac import get_admin_user, AdminRBACService
from backend.services.admin_logging import AdminLoggingService
from beanie import PydanticObjectId

logger = logging.getLogger('routes.admin_users')
router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])

@router.get("/search")
async def search_users(
    request: Request,
    query: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    admin_user: User = Depends(AdminRBACService.require_permission("users.view"))
):
    """Search users by email, username, or ID"""
    try:
        # Try to search by ID first
        try:
            user_by_id = await User.get(PydanticObjectId(query))
            if user_by_id:
                return {"users": [{
                    "id": str(user_by_id.id),
                    "email": user_by_id.email,
                    "name": user_by_id.name,
                    "role": user_by_id.role,
                    "is_suspended": user_by_id.is_suspended,
                    "created_at": user_by_id.created_at.isoformat()
                }], "total": 1}
        except:
            pass
        
        # Search by email or name
        users = await User.find(
            {"$or": [
                {"email": {"$regex": query, "$options": "i"}},
                {"name": {"$regex": query, "$options": "i"}}
            ]}
        ).limit(limit).to_list()
        
        return {
            "users": [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "name": u.name,
                    "role": u.role,
                    "is_suspended": u.is_suspended,
                    "created_at": u.created_at.isoformat()
                }
                for u in users
            ],
            "total": len(users)
        }
        
    except Exception as e:
        logger.error(f"Error searching users: {e}", exc_info=True)
        return {"error": str(e)}

@router.get("/{user_id}")
async def get_user_details(
    user_id: str,
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("users.view"))
):
    """Get detailed user information"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"error": "User not found"}
    
    profile = await Profile.find_one(Profile.user_id == user.id)
    recent_transactions = await CreditsTransaction.find(
        CreditsTransaction.user_id == user.id
    ).sort("-created_at").limit(10).to_list()
    
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_suspended": user.is_suspended,
            "credits_balance": user.credits_balance,
            "twofa_enabled": user.twofa_enabled,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        },
        "profile": {
            "display_name": profile.display_name if profile else None,
            "bio": profile.bio if profile else None,
            "total_earnings": profile.total_earnings if profile else 0
        } if profile else None,
        "recent_transactions": [
            {
                "amount": t.amount,
                "type": t.transaction_type,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in recent_transactions
        ]
    }

@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    request: Request,
    reason: str = Query(...),
    admin_user: User = Depends(AdminRBACService.require_permission("users.suspend"))
):
    """Suspend a user account"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"error": "User not found"}
    
    old_state = {"is_suspended": user.is_suspended}
    user.is_suspended = True
    await user.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="user_suspended",
        target_type="user",
        target_id=user_id,
        before_state=old_state,
        after_state={"is_suspended": True},
        reason=reason,
        ip_address=request.client.host if request.client else None,
        severity="warning"
    )
    
    return {"success": True, "user_id": user_id, "suspended": True}

@router.post("/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("users.suspend"))
):
    """Reactivate a suspended user"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"error": "User not found"}
    
    old_state = {"is_suspended": user.is_suspended}
    user.is_suspended = False
    await user.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="user_reactivated",
        target_type="user",
        target_id=user_id,
        before_state=old_state,
        after_state={"is_suspended": False},
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True, "user_id": user_id, "suspended": False}

@router.post("/{user_id}/reset-2fa")
async def reset_user_2fa(
    user_id: str,
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("users.edit"))
):
    """Reset user's 2FA"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"error": "User not found"}
    
    old_state = {"twofa_enabled": user.twofa_enabled}
    user.twofa_enabled = False
    user.twofa_secret = None
    await user.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="user_2fa_reset",
        target_type="user",
        target_id=user_id,
        before_state=old_state,
        after_state={"twofa_enabled": False},
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True, "user_id": user_id, "2fa_reset": True}

@router.get("/{user_id}/logs")
async def get_user_logs(
    user_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    admin_user: User = Depends(AdminRBACService.require_permission("users.view"))
):
    """Get user's activity logs"""
    from backend.services.admin_logging import AdminLoggingService
    
    logs, total = await AdminLoggingService.get_audit_logs(
        target_id=user_id,
        limit=limit
    )
    
    return {
        "logs": [
            {
                "action": log.action,
                "admin_email": log.admin_email,
                "reason": log.reason,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "total": total
    }