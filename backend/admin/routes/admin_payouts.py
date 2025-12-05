from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import csv
import io

from backend.models.user import User, Role
from backend.routes.auth import get_current_user
from backend.models.payment_subscription import UserSubscription, SubscriptionStatus

router = APIRouter(prefix="/api/admin/payouts", tags=["admin-payouts"])

class PayoutStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

class Payout(BaseModel):
    id: str
    creator_id: str
    amount: float
    currency: str = "USD"
    status: PayoutStatus
    requested_at: datetime
    processed_at: Optional[datetime] = None
    notes: Optional[str] = None

class PayoutRequest(BaseModel):
    amount: float
    currency: str = "USD"
    notes: Optional[str] = None

class PayoutActionRequest(BaseModel):
    action: str  # "approve" or "reject"
    notes: Optional[str] = None

def admin_only(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is admin"""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("", response_model=List[Payout])
async def get_all_payouts(
    status_filter: Optional[PayoutStatus] = None,
    admin: User = Depends(admin_only)
):
    """Get all payout requests (admin only)
    
    This is a placeholder implementation. In production, you would have
    a separate Payout collection/model.
    """
    # Placeholder: Return empty list
    # In production, query from Payout collection
    return []

@router.post("/{payout_id}/action")
async def process_payout(
    payout_id: str,
    action_request: PayoutActionRequest,
    admin: User = Depends(admin_only)
):
    """Approve or reject a payout request (admin only)"""
    if action_request.action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'approve' or 'reject'"
        )
    
    # Placeholder implementation
    # In production:
    # 1. Fetch payout from database
    # 2. Update status
    # 3. If approved, trigger payment via Stripe Connect or Razorpay
    # 4. Record transaction
    
    return {
        "message": f"Payout {action_request.action}d successfully",
        "payout_id": payout_id
    }

@router.get("/export/csv")
async def export_payouts_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin: User = Depends(admin_only)
):
    """Export payouts as CSV (admin only)"""
    # Placeholder implementation
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Payout ID",
        "Creator ID",
        "Amount",
        "Currency",
        "Status",
        "Requested At",
        "Processed At",
        "Notes"
    ])
    
    # In production, fetch and write actual payout data
    # For now, return empty CSV
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=payouts_export.csv"
        }
    )

@router.get("/stats")
async def get_payout_stats(admin: User = Depends(admin_only)):
    """Get payout statistics (admin only)"""
    # Placeholder implementation
    # In production, aggregate from Payout collection
    
    return {
        "total_pending": 0,
        "total_approved": 0,
        "total_paid": 0,
        "total_amount_pending": 0.0,
        "total_amount_paid": 0.0
    }
