import logging
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
from backend.models.user import User
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus

logger = logging.getLogger('service.fraud')

class FraudScoreService:
    async def calculate_score(
        self,
        user: User,
        amount_cents: int,
        ip_address: str,
        fingerprint_id: str = None
    ) -> Dict[str, Any]:
        score = 0
        reasons = []
        
        # Check velocity (payments in last hour)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_payments = await PaymentIntent.find(
            PaymentIntent.user_id == str(user.id),
            PaymentIntent.created_at >= one_hour_ago
        ).count()
        
        if recent_payments > 5:
            score += 30
            reasons.append(f"High velocity: {recent_payments} payments/hour")
        elif recent_payments > 3:
            score += 15
            reasons.append(f"Medium velocity: {recent_payments} payments/hour")
        
        # Large purchase detection
        if amount_cents > 50000:  # > ₹500
            score += 20
            reasons.append("Large purchase amount")
        
        # Account age
        account_age = (datetime.now(timezone.utc) - user.created_at).days
        if account_age < 1:
            score += 25
            reasons.append("New account (<1 day)")
        elif account_age < 7:
            score += 10
            reasons.append("Young account (<7 days)")
        
        # Failed payments history
        failed_payments = await PaymentIntent.find(
            PaymentIntent.user_id == str(user.id),
            PaymentIntent.status == PaymentIntentStatus.FAILED
        ).count()
        
        if failed_payments > 3:
            score += 20
            reasons.append(f"High failure rate: {failed_payments} failed")
        
        # Determine action
        if score >= 70:
            action = "block"
        elif score >= 40:
            action = "verify"
        else:
            action = "allow"
        
        logger.info(
            f"Fraud score calculated",
            extra={
                "user_id": str(user.id),
                "score": score,
                "action": action,
                "reasons": reasons
            }
        )
        
        return {
            "score": score,
            "action": action,
            "reasons": reasons,
            "details": {
                "velocity": recent_payments,
                "account_age_days": account_age,
                "failed_count": failed_payments
            }
        }

_fraud_service = None

def get_fraud_service():
    global _fraud_service
    if _fraud_service is None:
        _fraud_service = FraudScoreService()
    return _fraud_service
