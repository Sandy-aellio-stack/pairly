import logging
from datetime import datetime, timezone
from typing import List
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus

logger = logging.getLogger('payment.expiration')


class PaymentExpirationHandler:
    """
    Handles payment intent expiration logic.
    
    In production, this would run as a Celery Beat scheduled task.
    For mock mode, can be called manually or via API.
    """
    
    async def expire_old_intents(self, batch_size: int = 100) -> int:
        """
        Find and expire old payment intents.
        
        Args:
            batch_size: Number of intents to process in one batch
        
        Returns:
            Number of intents expired
        """
        now = datetime.now(timezone.utc)
        
        # Find pending/processing intents that have expired
        expired_intents = await PaymentIntent.find(
            PaymentIntent.status.in_([PaymentIntentStatus.PENDING, PaymentIntentStatus.PROCESSING]),
            PaymentIntent.expires_at < now
        ).limit(batch_size).to_list()
        
        expired_count = 0
        
        for intent in expired_intents:
            try:
                intent.mark_expired(reason="Payment intent expired due to timeout")
                await intent.save()
                
                logger.info(
                    f"Payment intent expired",
                    extra={
                        "event": "payment_intent_expired",
                        "payment_intent_id": intent.id,
                        "user_id": intent.user_id,
                        "created_at": intent.created_at.isoformat(),
                        "expires_at": intent.expires_at.isoformat()
                    }
                )
                
                expired_count += 1
            
            except Exception as e:
                logger.error(
                    f"Failed to expire payment intent: {e}",
                    extra={"payment_intent_id": intent.id},
                    exc_info=True
                )
        
        if expired_count > 0:
            logger.info(f"Expired {expired_count} payment intents")
        
        return expired_count
    
    async def get_expiring_soon(self, minutes: int = 5) -> List[PaymentIntent]:
        """
        Get payment intents expiring soon.
        
        Args:
            minutes: Number of minutes ahead to check
        
        Returns:
            List of payment intents expiring soon
        """
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        threshold = now + timedelta(minutes=minutes)
        
        expiring_intents = await PaymentIntent.find(
            PaymentIntent.status.in_([PaymentIntentStatus.PENDING, PaymentIntentStatus.PROCESSING]),
            PaymentIntent.expires_at <= threshold,
            PaymentIntent.expires_at > now
        ).to_list()
        
        return expiring_intents


# Global instance
_expiration_handler = None


def get_expiration_handler() -> PaymentExpirationHandler:
    """Get global expiration handler instance"""
    global _expiration_handler
    if _expiration_handler is None:
        _expiration_handler = PaymentExpirationHandler()
    return _expiration_handler
