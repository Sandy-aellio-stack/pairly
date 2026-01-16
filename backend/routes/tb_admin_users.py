from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import datetime, timezone
from beanie import PydanticObjectId

from backend.models.tb_user import TBUser
from backend.models.tb_credit import TBCreditTransaction
from backend.routes.tb_admin_auth import get_current_admin

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
    # banned users could have a separate flag
    
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
    try:
        user = await TBUser.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    try:
        user = await TBUser.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    try:
        user = await TBUser.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    admin: dict = Depends(get_current_admin)
):
    """Adjust user's credit balance"""
    try:
        user = await TBUser.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from backend.models.tb_credit import TransactionReason
    
    # Update balance first
    new_balance = user.credits_balance + amount
    if new_balance < 0:
        new_balance = 0
    
    # Create transaction record
    transaction = TBCreditTransaction(
        user_id=str(user.id),
        amount=amount,
        reason=TransactionReason.ADMIN_ADJUSTMENT,
        balance_after=new_balance,
        description=f"Admin adjustment: {reason}",
        reference_id=f"admin_{admin['email']}"
    )
    await transaction.insert()
    
    # Update user balance
    user.credits_balance = new_balance
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    
    return {
        "success": True,
        "new_balance": user.credits_balance,
        "adjustment": amount
    }
