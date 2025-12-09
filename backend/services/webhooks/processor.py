import logging
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.models.webhook_event import WebhookEvent, WebhookEventStatus, WebhookDLQ
from backend.services.webhooks.signature_verifier import WebhookSignatureVerifier
from backend.services.webhooks.event_handler import WebhookEventHandler

logger = logging.getLogger('webhook.processor')


class WebhookProcessor:
    """
    Central webhook processing service.
    
    Responsibilities:
    - Signature verification
    - Event deduplication
    - Event processing
    - DLQ management
    - Retry logic
    """
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self.signature_verifier = WebhookSignatureVerifier(mock_mode=mock_mode)
        self.event_handler = WebhookEventHandler(mock_mode=mock_mode)
        
        logger.info(f"WebhookProcessor initialized (mock_mode={mock_mode})")
    
    async def process_stripe_webhook(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str
    ) -> tuple[bool, str, Optional[str]]:
        """
        Process Stripe webhook.
        
        Steps:
        1. Verify signature
        2. Parse payload
        3. Check for duplicate
        4. Process event
        5. Handle errors (DLQ)
        
        Args:
            payload: Raw webhook payload
            signature_header: Stripe-Signature header
            webhook_secret: Webhook signing secret
        
        Returns:
            Tuple of (success, message, webhook_event_id)
        """
        try:
            # Step 1: Verify signature
            is_valid, error = self.signature_verifier.verify_stripe_signature(
                payload, signature_header, webhook_secret
            )
            
            if not is_valid:
                logger.warning(f"Stripe signature verification failed: {error}")
                return False, f"Signature verification failed: {error}", None
            
            # Step 2: Parse payload
            import json
            try:
                event_data = json.loads(payload.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to parse webhook payload: {e}")
                return False, "Invalid JSON payload", None
            
            event_id = event_data.get('id', '')
            event_type = event_data.get('type', '')
            
            if not event_id:
                return False, "Missing event ID", None
            
            # Step 3: Check for duplicate (idempotency)
            idempotency_key = f"stripe_{event_id}"
            existing_event = await WebhookEvent.find_one(
                WebhookEvent.idempotency_key == idempotency_key
            )
            
            if existing_event:
                logger.info(f"Duplicate Stripe webhook ignored: {event_id}")
                return True, f"Duplicate event (already processed)", existing_event.id
            
            # Step 4: Create webhook event record
            webhook_event = WebhookEvent(
                id=f"wh_{secrets.token_hex(16)}",
                provider="stripe",
                event_id=event_id,
                event_type=event_type,
                raw_payload=event_data,
                signature_header=signature_header,
                status=WebhookEventStatus.PENDING,
                idempotency_key=idempotency_key,
                webhook_timestamp=datetime.now(timezone.utc)
            )
            await webhook_event.insert()
            
            # Step 5: Process event
            success, error, payment_intent_id = await self.event_handler.handle_stripe_event(
                event_type, event_data
            )
            
            if success:
                webhook_event.mark_processed(payment_intent_id)
                await webhook_event.save()
                logger.info(f"Stripe webhook processed successfully: {event_id}")
                return True, "Webhook processed successfully", webhook_event.id
            else:
                # Failed - add to DLQ
                webhook_event.mark_failed(error or "Processing failed")
                await webhook_event.save()
                
                await self._add_to_dlq(webhook_event, error or "Unknown error")
                
                return False, f"Processing failed: {error}", webhook_event.id
        
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {e}", exc_info=True)
            return False, f"Internal error: {str(e)}", None
    
    async def process_razorpay_webhook(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str
    ) -> tuple[bool, str, Optional[str]]:
        """
        Process Razorpay webhook.
        
        Similar flow to Stripe webhook processing.
        """
        try:
            # Step 1: Verify signature
            is_valid, error = self.signature_verifier.verify_razorpay_signature(
                payload, signature_header, webhook_secret
            )
            
            if not is_valid:
                logger.warning(f"Razorpay signature verification failed: {error}")
                return False, f"Signature verification failed: {error}", None
            
            # Step 2: Parse payload
            import json
            try:
                event_data = json.loads(payload.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to parse webhook payload: {e}")
                return False, "Invalid JSON payload", None
            
            event_type = event_data.get('event', '')
            # Razorpay doesn't have a unique event ID, so we use payment ID
            payment_entity = event_data.get('payload', {}).get('payment', {}).get('entity', {})
            event_id = payment_entity.get('id', f"rzp_evt_{secrets.token_hex(8)}")
            
            if not event_type:
                return False, "Missing event type", None
            
            # Step 3: Check for duplicate
            idempotency_key = f"razorpay_{event_id}_{event_type}"
            existing_event = await WebhookEvent.find_one(
                WebhookEvent.idempotency_key == idempotency_key
            )
            
            if existing_event:
                logger.info(f"Duplicate Razorpay webhook ignored: {event_id}")
                return True, f"Duplicate event (already processed)", existing_event.id
            
            # Step 4: Create webhook event record
            webhook_event = WebhookEvent(
                id=f"wh_{secrets.token_hex(16)}",
                provider="razorpay",
                event_id=event_id,
                event_type=event_type,
                raw_payload=event_data,
                signature_header=signature_header,
                status=WebhookEventStatus.PENDING,
                idempotency_key=idempotency_key,
                webhook_timestamp=datetime.now(timezone.utc)
            )
            await webhook_event.insert()
            
            # Step 5: Process event
            success, error, payment_intent_id = await self.event_handler.handle_razorpay_event(
                event_type, event_data
            )
            
            if success:
                webhook_event.mark_processed(payment_intent_id)
                await webhook_event.save()
                logger.info(f"Razorpay webhook processed successfully: {event_id}")
                return True, "Webhook processed successfully", webhook_event.id
            else:
                # Failed - add to DLQ
                webhook_event.mark_failed(error or "Processing failed")
                await webhook_event.save()
                
                await self._add_to_dlq(webhook_event, error or "Unknown error")
                
                return False, f"Processing failed: {error}", webhook_event.id
        
        except Exception as e:
            logger.error(f"Error processing Razorpay webhook: {e}", exc_info=True)
            return False, f"Internal error: {str(e)}", None
    
    async def _add_to_dlq(self, webhook_event: WebhookEvent, error_reason: str):
        """Add failed webhook to Dead Letter Queue"""
        try:
            dlq_entry = WebhookDLQ(
                webhook_event_id=webhook_event.id,
                event_id=webhook_event.event_id,
                provider=webhook_event.provider,
                event_type=webhook_event.event_type,
                error_reason=error_reason,
                raw_payload=webhook_event.raw_payload,
                signature_header=webhook_event.signature_header,
                retry_count=0,
                max_retries=3
            )
            await dlq_entry.insert()
            
            logger.info(
                f"Added webhook to DLQ",
                extra={
                    "event": "webhook_added_to_dlq",
                    "webhook_event_id": webhook_event.id,
                    "provider": webhook_event.provider,
                    "error": error_reason
                }
            )
        except Exception as e:
            logger.error(f"Failed to add webhook to DLQ: {e}", exc_info=True)
    
    async def retry_webhook_event(self, webhook_event_id: str) -> tuple[bool, str]:
        """
        Manually retry a failed webhook event.
        
        Args:
            webhook_event_id: Webhook event ID to retry
        
        Returns:
            Tuple of (success, message)
        """
        webhook_event = await WebhookEvent.find_one(WebhookEvent.id == webhook_event_id)
        
        if not webhook_event:
            return False, f"Webhook event not found: {webhook_event_id}"
        
        if webhook_event.status == WebhookEventStatus.PROCESSED:
            return False, "Webhook already processed successfully"
        
        # Increment retry counter
        webhook_event.increment_retry()
        await webhook_event.save()
        
        # Retry processing
        try:
            if webhook_event.provider == "stripe":
                success, error, payment_intent_id = await self.event_handler.handle_stripe_event(
                    webhook_event.event_type,
                    webhook_event.raw_payload
                )
            elif webhook_event.provider == "razorpay":
                success, error, payment_intent_id = await self.event_handler.handle_razorpay_event(
                    webhook_event.event_type,
                    webhook_event.raw_payload
                )
            else:
                return False, f"Unknown provider: {webhook_event.provider}"
            
            if success:
                webhook_event.mark_processed(payment_intent_id)
                await webhook_event.save()
                
                # Update DLQ if exists
                dlq_entry = await WebhookDLQ.find_one(
                    WebhookDLQ.webhook_event_id == webhook_event_id
                )
                if dlq_entry:
                    dlq_entry.mark_resolved(notes="Retry successful")
                    await dlq_entry.save()
                
                logger.info(f"Webhook retry successful: {webhook_event_id}")
                return True, "Webhook processed successfully on retry"
            else:
                webhook_event.mark_failed(error or "Retry failed")
                await webhook_event.save()
                
                # Update DLQ retry count
                dlq_entry = await WebhookDLQ.find_one(
                    WebhookDLQ.webhook_event_id == webhook_event_id
                )
                if dlq_entry:
                    dlq_entry.increment_retry()
                    await dlq_entry.save()
                
                return False, f"Retry failed: {error}"
        
        except Exception as e:
            logger.error(f"Error retrying webhook: {e}", exc_info=True)
            webhook_event.mark_failed(str(e))
            await webhook_event.save()
            return False, f"Retry error: {str(e)}"


# Global instance
_webhook_processor: Optional[WebhookProcessor] = None


def get_webhook_processor(mock_mode: bool = True) -> WebhookProcessor:
    """Get global webhook processor instance"""
    global _webhook_processor
    if _webhook_processor is None:
        _webhook_processor = WebhookProcessor(mock_mode=mock_mode)
    return _webhook_processor
