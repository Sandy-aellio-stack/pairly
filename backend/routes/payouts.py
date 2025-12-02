from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.models.user import User, Role
from backend.models.payout import Payout, PayoutStatus
from backend.models.profile import Profile
from backend.routes.profiles import get_current_user
from backend.services.audit import log_event
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/payouts")

class PayoutRequest(BaseModel):
    amount_credits: int
    payment_method: str = "bank_transfer"
    payment_details: dict

class PayoutApprovalRequest(BaseModel):
    approved: bool
    admin_notes: Optional[str] = None

@router.post("/request")
async def request_payout(
    request: PayoutRequest,
    user: User = Depends(get_current_user)
):
    """Creator requests a payout"""
    if user.role != Role.CREATOR:
        raise HTTPException(403, "Only creators can request payouts")
    
    # Check if user has enough credits
    if user.credits_balance < request.amount_credits:
        raise HTTPException(400, "Insufficient credits balance")
    
    # Minimum payout amount (e.g., 1000 credits = $10)
    MIN_PAYOUT = 1000
    if request.amount_credits < MIN_PAYOUT:
        raise HTTPException(400, f"Minimum payout is {MIN_PAYOUT} credits")
    
    # Calculate USD amount (100 credits = $1)
    amount_usd = request.amount_credits / 100
    
    # Create payout request
    payout = Payout(
        creator_id=user.id,
        amount_credits=request.amount_credits,
        amount_usd=amount_usd,
        status=PayoutStatus.PENDING,
        payment_method=request.payment_method,
        payment_details=request.payment_details
    )
    await payout.insert()
    
    # Deduct credits from user
    user.credits_balance -= request.amount_credits
    await user.save()
    
    await log_event(
        actor_user_id=user.id,
        action="payout_requested",
        details={
            "payout_id": str(payout.id),
            "amount_credits": request.amount_credits,
            "amount_usd": amount_usd
        },
        severity="info"
    )
    
    return {
        "payout_id": str(payout.id),
        "amount_credits": request.amount_credits,
        "amount_usd": amount_usd,
        "status": payout.status
    }

@router.get("/my-payouts")
async def get_my_payouts(user: User = Depends(get_current_user)):
    """Get creator's payout history"""
    if user.role != Role.CREATOR:
        raise HTTPException(403, "Only creators can view payouts")
    
    payouts = await Payout.find(Payout.creator_id == user.id).sort("-created_at").to_list()
    
    return [{
        "id": str(p.id),
        "amount_credits": p.amount_credits,
        "amount_usd": p.amount_usd,
        "status": p.status,
        "payment_method": p.payment_method,
        "created_at": p.created_at.isoformat(),
        "approved_at": p.approved_at.isoformat() if p.approved_at else None,
        "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        "admin_notes": p.admin_notes
    } for p in payouts]

@router.get("/admin/pending")
async def get_pending_payouts(user: User = Depends(get_current_user)):
    """Admin: Get all pending payouts"""
    if user.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    payouts = await Payout.find(Payout.status == PayoutStatus.PENDING).sort("-created_at").to_list()
    
    result = []
    for p in payouts:
        creator = await User.get(p.creator_id)
        profile = await Profile.find_one(Profile.user_id == p.creator_id)
        
        result.append({
            "id": str(p.id),
            "creator_id": str(p.creator_id),
            "creator_email": creator.email if creator else None,
            "creator_name": profile.display_name if profile else None,
            "amount_credits": p.amount_credits,
            "amount_usd": p.amount_usd,
            "payment_method": p.payment_method,
            "payment_details": p.payment_details,
            "created_at": p.created_at.isoformat()
        })
    
    return result

@router.post("/admin/review/{payout_id}")
async def review_payout(
    payout_id: str,
    approval: PayoutApprovalRequest,
    user: User = Depends(get_current_user)
):
    """Admin: Approve or reject a payout"""
    if user.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    from beanie import PydanticObjectId
    payout = await Payout.get(PydanticObjectId(payout_id))
    if not payout:
        raise HTTPException(404, "Payout not found")
    
    if payout.status != PayoutStatus.PENDING:
        raise HTTPException(400, "Payout already reviewed")
    
    if approval.approved:
        payout.status = PayoutStatus.APPROVED
        payout.approved_by = user.id
        payout.approved_at = datetime.utcnow()
        payout.admin_notes = approval.admin_notes
        
        # In production, integrate with payment processor here
        # For now, mark as completed immediately
        payout.status = PayoutStatus.COMPLETED
        payout.completed_at = datetime.utcnow()
    else:
        payout.status = PayoutStatus.REJECTED
        payout.approved_by = user.id
        payout.approved_at = datetime.utcnow()
        payout.admin_notes = approval.admin_notes
        
        # Refund credits to creator
        creator = await User.get(payout.creator_id)
        creator.credits_balance += payout.amount_credits
        await creator.save()
    
    await payout.save()
    
    await log_event(
        actor_user_id=user.id,
        action="payout_reviewed",
        details={
            "payout_id": str(payout.id),
            "approved": approval.approved,
            "admin_notes": approval.admin_notes
        },
        severity="info"
    )
    
    return {
        "payout_id": str(payout.id),
        "status": payout.status,
        "approved_by": str(user.id)
    }