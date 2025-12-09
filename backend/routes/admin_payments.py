from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from backend.models.user import User
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus, PaymentProvider
from backend.routes.auth import get_current_user
from backend.services.payments import get_payment_manager
from backend.services.payments.expiration_handler import get_expiration_handler
import logging
import json

logger = logging.getLogger('routes.admin_payments')

router = APIRouter(prefix="/api/admin/payments", tags=["admin-payments"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RefundRequest(BaseModel):
    """Request to refund a payment"""
    payment_intent_id: str
    reason: str = "Admin refund"


class PaymentFilterParams(BaseModel):
    """Filter parameters for payment list"""
    user_id: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None  # Search by payment intent ID or user email


class PaymentStatsResponse(BaseModel):
    """Payment statistics response"""
    total_payments: int
    total_amount_cents: int
    successful_payments: int
    failed_payments: int
    pending_payments: int
    refunded_payments: int
    total_credits_sold: int


# ============================================================================
# Helper Functions
# ============================================================================

def check_admin_access(user: User):
    """Check if user has admin access"""
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")


# ============================================================================
# Admin Payment Endpoints
# ============================================================================

@router.get("/list")
async def list_payments(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List all payment intents with filtering.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    # Build query
    query_filters = []
    
    if user_id:
        query_filters.append(PaymentIntent.user_id == user_id)
    
    if provider:
        try:
            query_filters.append(PaymentIntent.provider == PaymentProvider(provider))
        except ValueError:
            raise HTTPException(400, f"Invalid provider: {provider}")
    
    if status:
        try:
            query_filters.append(PaymentIntent.status == PaymentIntentStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    
    if min_amount is not None:
        query_filters.append(PaymentIntent.amount_cents >= min_amount)
    
    if max_amount is not None:
        query_filters.append(PaymentIntent.amount_cents <= max_amount)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query_filters.append(PaymentIntent.created_at >= start_dt)
        except:
            raise HTTPException(400, "Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query_filters.append(PaymentIntent.created_at <= end_dt)
        except:
            raise HTTPException(400, "Invalid end_date format")
    
    if search:
        # Search by payment intent ID
        query_filters.append(PaymentIntent.id.contains(search))
    
    # Execute query
    skip = (page - 1) * limit
    
    if query_filters:
        from functools import reduce
        import operator
        combined_query = reduce(operator.and_, query_filters)
        payments = await PaymentIntent.find(combined_query).sort("-created_at").skip(skip).limit(limit).to_list()
        total = await PaymentIntent.find(combined_query).count()
    else:
        payments = await PaymentIntent.find_all().sort("-created_at").skip(skip).limit(limit).to_list()
        total = await PaymentIntent.find_all().count()
    
    logger.info(
        f"Admin listed payments",
        extra={
            "admin_user_id": str(user.id),
            "filters": {
                "user_id": user_id,
                "provider": provider,
                "status": status,
                "page": page,
                "limit": limit
            },
            "results": len(payments)
        }
    )
    
    return {
        "payments": [p.to_dict() for p in payments],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }


@router.get("/stats")
async def get_payment_stats(
    user: User = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get payment statistics.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    # Build date range filter
    query_filters = []
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query_filters.append(PaymentIntent.created_at >= start_dt)
        except:
            raise HTTPException(400, "Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query_filters.append(PaymentIntent.created_at <= end_dt)
        except:
            raise HTTPException(400, "Invalid end_date format")
    
    # Get all payments in range
    if query_filters:
        from functools import reduce
        import operator
        combined_query = reduce(operator.and_, query_filters)
        payments = await PaymentIntent.find(combined_query).to_list()
    else:
        payments = await PaymentIntent.find_all().to_list()
    
    # Calculate stats
    total_payments = len(payments)
    total_amount = sum(p.amount_cents for p in payments)
    successful = sum(1 for p in payments if p.status == PaymentIntentStatus.SUCCEEDED)
    failed = sum(1 for p in payments if p.status == PaymentIntentStatus.FAILED)
    pending = sum(1 for p in payments if p.status == PaymentIntentStatus.PENDING)
    refunded = sum(1 for p in payments if p.status == PaymentIntentStatus.REFUNDED)
    total_credits = sum(p.credits_amount for p in payments if p.credits_added)
    
    return {
        "total_payments": total_payments,
        "total_amount_cents": total_amount,
        "successful_payments": successful,
        "failed_payments": failed,
        "pending_payments": pending,
        "refunded_payments": refunded,
        "total_credits_sold": total_credits,
        "date_range": {
            "start": start_date,
            "end": end_date
        }
    }


@router.get("/user/{user_id}/financial-history")
async def get_user_financial_history(
    user_id: str,
    user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get complete financial history for a user.
    
    Includes:
    - All payment intents
    - Credits balance
    - Transaction history
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    # Get user
    target_user = await User.get(user_id)
    if not target_user:
        raise HTTPException(404, f"User not found: {user_id}")
    
    # Get payment history
    payments = await PaymentIntent.find(
        PaymentIntent.user_id == user_id
    ).sort("-created_at").limit(limit).to_list()
    
    # Get credits transactions
    from backend.models.credits_transaction import CreditsTransaction
    from beanie import PydanticObjectId
    
    transactions = await CreditsTransaction.find(
        CreditsTransaction.user_id == PydanticObjectId(user_id)
    ).sort("-created_at").limit(limit).to_list()
    
    return {
        "user": {
            "id": str(target_user.id),
            "email": target_user.email,
            "name": target_user.name,
            "credits_balance": target_user.credits_balance
        },
        "payments": [p.to_dict() for p in payments],
        "transactions": [
            {
                "id": str(t.id),
                "amount": t.amount,
                "type": t.transaction_type,
                "balance_before": t.balance_before,
                "balance_after": t.balance_after,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ],
        "summary": {
            "total_payments": len(payments),
            "successful_payments": sum(1 for p in payments if p.status == PaymentIntentStatus.SUCCEEDED),
            "total_spent_cents": sum(p.amount_cents for p in payments if p.status == PaymentIntentStatus.SUCCEEDED),
            "total_credits_purchased": sum(p.credits_amount for p in payments if p.credits_added),
            "current_balance": target_user.credits_balance
        }
    }


@router.post("/refund")
async def refund_payment(
    req: RefundRequest,
    user: User = Depends(get_current_user)
):
    """
    Refund a payment (mock mode only).
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    payment_manager = get_payment_manager(mock_mode=True)
    
    success = await payment_manager.refund_payment(
        payment_intent_id=req.payment_intent_id,
        reason=f"Admin refund: {req.reason}",
        mock_mode=True
    )
    
    if not success:
        raise HTTPException(500, "Refund failed")
    
    logger.info(
        f"Admin refunded payment",
        extra={
            "admin_user_id": str(user.id),
            "payment_intent_id": req.payment_intent_id,
            "reason": req.reason
        }
    )
    
    return {
        "success": True,
        "message": "Payment refunded successfully",
        "payment_intent_id": req.payment_intent_id
    }


@router.get("/search")
async def search_payments(
    user: User = Depends(get_current_user),
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search payments by:
    - Payment intent ID
    - User ID
    - Provider intent ID
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    # Search by payment intent ID or provider intent ID
    payments = []
    
    # Try exact match on payment intent ID
    intent = await PaymentIntent.find_one(PaymentIntent.id == q)
    if intent:
        payments.append(intent)
    
    # Try partial match on provider intent ID or user ID
    if not payments:
        payments = await PaymentIntent.find(
            (PaymentIntent.provider_intent_id.contains(q)) | 
            (PaymentIntent.user_id.contains(q))
        ).limit(limit).to_list()
    
    return {
        "query": q,
        "results": len(payments),
        "payments": [p.to_dict() for p in payments]
    }


@router.get("/export")
async def export_payments(
    user: User = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Export payments as JSON.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    # Build query
    query_filters = []
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query_filters.append(PaymentIntent.created_at >= start_dt)
        except:
            raise HTTPException(400, "Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query_filters.append(PaymentIntent.created_at <= end_dt)
        except:
            raise HTTPException(400, "Invalid end_date format")
    
    if status:
        try:
            query_filters.append(PaymentIntent.status == PaymentIntentStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    
    # Get payments
    if query_filters:
        from functools import reduce
        import operator
        combined_query = reduce(operator.and_, query_filters)
        payments = await PaymentIntent.find(combined_query).sort("-created_at").to_list()
    else:
        payments = await PaymentIntent.find_all().sort("-created_at").to_list()
    
    # Convert to dict with all fields
    export_data = []
    for p in payments:
        data = p.to_dict()
        data.update({
            "provider_intent_id": p.provider_intent_id,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            "credits_added": p.credits_added,
            "credits_refunded": p.credits_refunded,
            "retry_count": p.retry_count,
            "risk_score": p.risk_score,
            "fraud_score": p.fraud_score
        })
        export_data.append(data)
    
    logger.info(
        f"Admin exported payments",
        extra={
            "admin_user_id": str(user.id),
            "exported_count": len(export_data)
        }
    )
    
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(export_data),
        "payments": export_data
    }


@router.post("/expire-old")
async def expire_old_payments(
    user: User = Depends(get_current_user)
):
    """
    Manually trigger expiration of old payment intents.
    
    In production, this would run automatically via Celery Beat.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    expiration_handler = get_expiration_handler()
    expired_count = await expiration_handler.expire_old_intents(batch_size=100)
    
    logger.info(
        f"Admin triggered payment expiration",
        extra={
            "admin_user_id": str(user.id),
            "expired_count": expired_count
        }
    )
    
    return {
        "success": True,
        "expired_count": expired_count,
        "message": f"Expired {expired_count} old payment intents"
    }


@router.get("/expiring-soon")
async def get_expiring_soon(
    user: User = Depends(get_current_user),
    minutes: int = Query(5, ge=1, le=60)
):
    """
    Get payment intents expiring soon.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    expiration_handler = get_expiration_handler()
    expiring = await expiration_handler.get_expiring_soon(minutes=minutes)
    
    return {
        "count": len(expiring),
        "threshold_minutes": minutes,
        "payments": [p.to_dict() for p in expiring]
    }
