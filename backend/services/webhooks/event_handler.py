import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus
from backend.services.payments import get_payment_manager

logger = logging.getLogger('webhook.handler')


class WebhookEventHandler:
    """
    Handles different webhook event types.
    
    Responsibilities:
    - Parse webhook payload
    - Update PaymentIntent status
    - Trigger credits fulfillment
    - Log audit events
    """
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self.payment_manager = get_payment_manager(mock_mode=mock_mode)
    
    async def handle_stripe_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Handle Stripe webhook event.
        
        Args:
            event_type: Event type (e.g., "payment_intent.succeeded")
            event_data: Event data from webhook
        
        Returns:
            Tuple of (success, error_message, payment_intent_id)
        """
        try:
            # Extract payment intent data
            data_object = event_data.get('data', {}).get('object', {})
            provider_intent_id = data_object.get('id', '')
            status = data_object.get('status', '')
            
            if not provider_intent_id:
                return False, "No payment intent ID in webhook", None
            
            # Find our payment intent
            payment_intent = await PaymentIntent.find_one(
                PaymentIntent.provider_intent_id == provider_intent_id
            )
            
            if not payment_intent:
                logger.warning(f"Payment intent not found for provider ID: {provider_intent_id}")
                return False, f"Payment intent not found: {provider_intent_id}", None
            
            # Handle different event types
            if event_type == "payment_intent.succeeded":
                return await self._handle_payment_succeeded(payment_intent)
            
            elif event_type == "payment_intent.failed":
                return await self._handle_payment_failed(payment_intent, "Payment failed at provider")
            
            elif event_type == "payment_intent.processing":
                payment_intent.mark_processing(reason="Payment processing at provider")
                await payment_intent.save()
                logger.info(f"Payment intent marked as processing: {payment_intent.id}")
                return True, None, payment_intent.id
            
            elif event_type == "charge.refunded":
                logger.info(f"Refund webhook received for: {payment_intent.id}")
                return True, None, payment_intent.id
            
            else:
                return False, f"Unhandled event type: {event_type}", payment_intent.id
        
        except Exception as e:
            logger.error(f"Error handling Stripe event: {e}", exc_info=True)
            return False, str(e), None
    
    async def handle_razorpay_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Handle Razorpay webhook event.
        
        Args:
            event_type: Event type (e.g., "payment.captured")
            event_data: Event data from webhook
        
        Returns:
            Tuple of (success, error_message, payment_intent_id)
        """
        try:
            # Extract payment data
            payment_entity = event_data.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id', '')
            payment_id = payment_entity.get('id', '')
            status = payment_entity.get('status', '')
            
            if not order_id:
                return False, "No order ID in webhook", None
            
            # Find our payment intent by Razorpay order ID
            payment_intent = await PaymentIntent.find_one(
                PaymentIntent.provider_intent_id == order_id
            )
            
            if not payment_intent:
                logger.warning(f"Payment intent not found for order ID: {order_id}")
                return False, f"Payment intent not found: {order_id}", None
            
            # Handle different event types
            if event_type == "payment.captured":
                return await self._handle_payment_succeeded(payment_intent)
            
            elif event_type == "payment.failed":
                return await self._handle_payment_failed(payment_intent, "Payment failed at Razorpay")
            
            elif event_type == "refund.created":
                logger.info(f"Refund webhook received for: {payment_intent.id}")
                return True, None, payment_intent.id
            
            else:
                return False, f"Unhandled event type: {event_type}", payment_intent.id
        
        except Exception as e:
            logger.error(f"Error handling Razorpay event: {e}", exc_info=True)
            return False, str(e), None
    
    async def _handle_payment_succeeded(
        self,
        payment_intent: PaymentIntent
    ) -> tuple[bool, Optional[str], str]:
        """
        Handle successful payment.
        
        Steps:
        1. Check if already processed
        2. Mark as processing
        3. Fulfill payment (add credits)
        4. Mark as succeeded
        """
        # Check if already processed
        if payment_intent.status == PaymentIntentStatus.SUCCEEDED:
            logger.info(f"Payment already processed: {payment_intent.id}")
            return True, None, payment_intent.id
        
        try:
            # Mark as processing
            payment_intent.mark_processing(reason="Processing webhook success event")
            await payment_intent.save()
            
            # Fulfill payment (add credits)
            success = await self.payment_manager.fulfill_payment(payment_intent)
            
            if not success:
                return False, "Credit fulfillment failed", payment_intent.id
            
            logger.info(
                f"Payment succeeded via webhook",
                extra={
                    "event": "webhook_payment_succeeded",
                    "payment_intent_id": payment_intent.id,
                    "user_id": payment_intent.user_id,
                    "credits_amount": payment_intent.credits_amount
                }
            )
            
            return True, None, payment_intent.id
        
        except Exception as e:
            logger.error(f"Error fulfilling payment: {e}", exc_info=True)
            payment_intent.mark_failed(reason=f"Fulfillment error: {str(e)}")
            await payment_intent.save()
            return False, str(e), payment_intent.id
    
    async def _handle_payment_failed(
        self,
        payment_intent: PaymentIntent,
        reason: str
    ) -> tuple[bool, Optional[str], str]:
        """
        Handle failed payment.
        """
        if payment_intent.status == PaymentIntentStatus.FAILED:
            logger.info(f"Payment already marked as failed: {payment_intent.id}")
            return True, None, payment_intent.id
        
        payment_intent.mark_completed(success=False, reason=reason)
        payment_intent.increment_retry(error=reason)
        await payment_intent.save()
        
        logger.info(
            f"Payment failed via webhook",
            extra={
                "event": "webhook_payment_failed",
                "payment_intent_id": payment_intent.id,
                "user_id": payment_intent.user_id,
                "reason": reason
            }
        )
        
        return True, None, payment_intent.id
