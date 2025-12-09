from fastapi import APIRouter, HTTPException, Depends, Query
from backend.models.user import User
from backend.models.payment_intent import PaymentIntent
from backend.routes.auth import get_current_user
import logging

logger = logging.getLogger('routes.admin_fraud')
router = APIRouter(prefix="/api/admin/fraud", tags=["admin-fraud"])

def check_admin(user: User):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")

@router.get("/high-risk-users")
async def get_high_risk_users(
    user: User = Depends(get_current_user),
    threshold: int = Query(70, ge=0, le=100)
):
    check_admin(user)
    
    # Get payments with high fraud scores
    high_risk = await PaymentIntent.find(
        PaymentIntent.fraud_score >= threshold
    ).sort("-fraud_score").limit(50).to_list()
    
    # Group by user
    user_scores = {}
    for payment in high_risk:
        if payment.user_id not in user_scores:
            user_scores[payment.user_id] = {
                "user_id": payment.user_id,
                "max_score": payment.fraud_score,
                "payment_count": 0
            }
        user_scores[payment.user_id]["payment_count"] += 1
    
    return {
        "high_risk_users": list(user_scores.values()),
        "count": len(user_scores)
    }

@router.get("/payment-history")
async def get_fraud_payment_history(
    user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    check_admin(user)
    
    payments = await PaymentIntent.find(
        PaymentIntent.fraud_score > 0
    ).sort("-fraud_score").limit(limit).to_list()
    
    return {
        "payments": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "fraud_score": p.fraud_score,
                "status": p.status,
                "amount_cents": p.amount_cents,
                "created_at": p.created_at.isoformat()
            }
            for p in payments
        ]
    }

@router.get("/stats")
async def get_fraud_stats(user: User = Depends(get_current_user)):
    check_admin(user)
    
    all_payments = await PaymentIntent.find_all().to_list()
    
    blocked = sum(1 for p in all_payments if p.fraud_score and p.fraud_score >= 70)
    flagged = sum(1 for p in all_payments if p.fraud_score and 40 <= p.fraud_score < 70)
    clean = sum(1 for p in all_payments if not p.fraud_score or p.fraud_score < 40)
    
    return {
        "total_payments": len(all_payments),
        "blocked": blocked,
        "flagged": flagged,
        "clean": clean,
        "block_rate": round(blocked / len(all_payments) * 100, 2) if all_payments else 0
    }
