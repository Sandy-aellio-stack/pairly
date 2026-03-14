from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import datetime, timezone
from beanie import PydanticObjectId

from backend.models.tb_user import TBUser
from backend.models.tb_credit import TBCreditTransaction
from backend.routes.tb_admin_auth import get_current_admin, check_super_admin
from backend.utils.objectid_utils import validate_object_id

router = APIRouter(prefix="/api/admin/users", tags=["Luveloop Admin Users"])


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(active|suspended|banned)$"),
    search: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all users with pagination and filtering"""
    query = {}
    
    # Filter by status
    if status == "active":
        query["is_active"] = True
    elif status == "suspended":
        query["is_active"] = False
    
    # Search by name or email
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count
    total = await TBUser.find(query).count()
    
    # Get paginated users
    skip = (page - 1) * limit
    users = await TBUser.find(query).skip(skip).limit(limit).to_list()
    
    return {
        "users": [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "age": u.age,
                "gender": u.gender,
                "status": "active" if u.is_active else "suspended",
                "verified": u.is_verified,
                "credits": u.credits_balance,
                "joinedDate": u.created_at.strftime("%Y-%m-%d")
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/{user_id}")
async def get_user_details(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get detailed user information"""
    user_oid = validate_object_id(user_id)
    user = await TBUser.get(user_oid)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recent transactions
    transactions = await TBCreditTransaction.find(
        TBCreditTransaction.user_id == str(user.id)
    ).sort("-created_at").limit(10).to_list()
    
    return {
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "mobile_number": user.mobile_number,
            "age": user.age,
            "gender": user.gender,
            "bio": user.bio,
            "intent": user.intent,
            "status": "active" if user.is_active else "suspended",
            "verified": user.is_verified,
            "credits": user.credits_balance,
            "joinedDate": user.created_at.strftime("%Y-%m-%d"),
            "lastLogin": user.last_login_at.strftime("%Y-%m-%d %H:%M") if user.last_login_at else None
        },
        "transactions": [
            {
                "id": str(t.id),
                "type": t.reason,
                "amount": t.amount,
                "description": t.description or t.reason,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
    }


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Suspend a user"""
    user_oid = validate_object_id(user_id)
    user = await TBUser.get(user_oid)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    
    return {"success": True, "message": f"User {user.name} has been suspended"}


@router.post("/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Reactivate a suspended user"""
    user_oid = validate_object_id(user_id)
    user = await TBUser.get(user_oid)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    
    return {"success": True, "message": f"User {user.name} has been reactivated"}


@router.post("/{user_id}/adjust-credits")
async def adjust_user_credits(
    user_id: str,
    amount: int = Query(..., description="Amount to add (positive) or subtract (negative)"),
    reason: str = Query(..., min_length=3),
    admin: dict = Depends(check_super_admin)
):
    """Adjust user's credit balance"""
    user_oid = validate_object_id(user_id)
    user = await TBUser.get(user_oid)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from backend.services.tb_credit_service import CreditService
    from backend.models.tb_credit import TransactionReason
    
    if amount > 0:
        transaction = await CreditService.add_credits(
            user_id=str(user.id),
            amount=amount,
            reason=TransactionReason.ADMIN_ADJUSTMENT,
            description=f"Admin adjustment: {reason}",
            reference_id=f"admin_{admin['email']}"
        )
    elif amount < 0:
        # Note: deduct_credits takes positive amount for decrement
        transaction = await CreditService.deduct_credits(
            user_id=str(user.id),
            amount=abs(amount),
            reason=TransactionReason.ADMIN_ADJUSTMENT,
            description=f"Admin adjustment: {reason}",
            reference_id=f"admin_{admin['email']}"
        )
    else:
        return {"success": True, "message": "No adjustment made", "new_balance": user.credits_balance}
        
    # Refetch user to get NEW balance after atomic update
    updated_user = await TBUser.get(user.id)
    
    return {
        "success": True,
        "new_balance": updated_user.credits_balance,
        "adjustment": amount,
        "transaction_id": str(transaction.id)
    }


# ========== ADMIN NOTIFICATION BROADCAST ==========

from pydantic import BaseModel as _BaseModel
from typing import List as _List, Optional as _Optional

class AdminSendNotificationRequest(_BaseModel):
    title: str
    body: str
    notification_type: str = "system"
    user_ids: _Optional[_List[str]] = None  # None = send to all users


@router.post("/notifications/send")
async def send_admin_notification(
    data: AdminSendNotificationRequest,
    admin: dict = Depends(get_current_admin)
):
    """Send a notification to all users or a specific list of users."""
    import uuid as _uuid
    from datetime import datetime, timezone
    from beanie import Document as _Doc
    from pydantic import Field as _Field

    # Use the existing TBNotification model from tb_notifications
    from backend.routes.tb_notifications import TBNotification

    if data.user_ids:
        recipients = data.user_ids
    else:
        all_users = await TBUser.find({"is_active": True}).project(TBUser).to_list()
        recipients = [str(u.id) for u in all_users]

    created = 0
    for uid in recipients:
        notif = TBNotification(
            user_id=uid,
            title=data.title,
            body=data.body,
            notification_type=data.notification_type
        )
        await notif.insert()
        created += 1

    return {
        "success": True,
        "notifications_sent": created,
        "message": f"Notification sent to {created} user(s)."
    }
