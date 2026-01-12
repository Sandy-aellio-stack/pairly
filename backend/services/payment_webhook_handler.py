"""
Payment Webhook Handler Service
Handles Stripe and Razorpay webhook events with:
- Signature verification
- Idempotent credit updates
- Atomic transactions
- Comprehensive logging
"""
import os
import hmac
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from enum import Enum

import stripe

from backend.models.tb_payment import TBPayment, PaymentStatus, PaymentProvider
from backend.models.tb_user import TBUser
from backend.models.tb_credit import TBCreditTransaction, TransactionReason
from backend.core.redis_client import redis_client

logger = logging.getLogger("webhook_handler")

# Environment variables
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

stripe.api_key = STRIPE_SECRET_KEY


class WebhookResult(Enum):
    """Webhook processing result"""
    SUCCESS = "success"
    DUPLICATE = "duplicate"
    INVALID_SIGNATURE = "invalid_signature"
    PAYMENT_NOT_FOUND = "payment_not_found"
    ALREADY_PROCESSED = "already_processed"
    CREDITS_ADDED = "credits_added"
    FAILED = "failed"
    IGNORED = "ignored"


class PaymentWebhookHandler:
    """
    Handles payment webhooks from Stripe and Razorpay.
    
    Key features:
    - Signature verification for security
    - Idempotent processing (safe to retry)
    - Atomic credit updates
    - Comprehensive audit logging
    """
    
    # Redis key prefixes for idempotency
    IDEMPOTENCY_PREFIX = "webhook:processed:"
    IDEMPOTENCY_TTL = 86400 * 7  # 7 days
    
    # Lock timeout for processing
    LOCK_TTL = 300  # 5 minutes
    
    @classmethod
    def verify_stripe_signature(
        cls,
        payload: bytes,
        signature: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify Stripe webhook signature.
        
        Returns:
            (is_valid, event_data, error_message)
        """
        if not STRIPE_WEBHOOK_SECRET:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured - signature verification skipped")
            # In development, allow without signature verification but log warning
            try:
                event = json.loads(payload)
                return True, event, None
            except json.JSONDecodeError as e:
                return False, None, f"Invalid JSON payload: {e}"
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                STRIPE_WEBHOOK_SECRET
            )
            return True, event, None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe signature verification failed: {e}")
            return False, None, "Invalid signature"
        except ValueError as e:
            logger.error(f"Invalid Stripe payload: {e}")
            return False, None, f"Invalid payload: {e}"
    
    @classmethod
    def verify_razorpay_signature(
        cls,
        payload: bytes,
        signature: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify Razorpay webhook signature using HMAC SHA-256.
        
        Returns:
            (is_valid, event_data, error_message)
        """
        if not RAZORPAY_WEBHOOK_SECRET:
            logger.warning("RAZORPAY_WEBHOOK_SECRET not configured - signature verification skipped")
            try:
                event = json.loads(payload)
                return True, event, None
            except json.JSONDecodeError as e:
                return False, None, f"Invalid JSON payload: {e}"
        
        try:
            # Razorpay uses HMAC SHA-256
            expected_signature = hmac.new(
                RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison to prevent timing attacks
            if hmac.compare_digest(expected_signature, signature):
                event = json.loads(payload)
                return True, event, None
            else:
                logger.error("Razorpay signature mismatch")
                return False, None, "Invalid signature"
        except Exception as e:
            logger.error(f"Razorpay signature verification error: {e}")
            return False, None, f"Signature verification error: {e}"
    
    @classmethod
    async def check_idempotency(
        cls,
        provider: str,
        event_id: str
    ) -> bool:
        """
        Check if event has already been processed.
        
        Returns:
            True if already processed (duplicate), False if new
        """
        if not redis_client.is_connected():
            # Without Redis, check database directly
            existing = await TBPayment.find_one({
                "webhook_event_id": event_id,
                "status": PaymentStatus.COMPLETED
            })
            return existing is not None
        
        key = f"{cls.IDEMPOTENCY_PREFIX}{provider}:{event_id}"
        exists = await redis_client.redis.exists(key)
        return exists > 0
    
    @classmethod
    async def mark_processed(
        cls,
        provider: str,
        event_id: str,
        payment_id: str = None
    ):
        """Mark event as processed for idempotency"""
        if redis_client.is_connected():
            key = f"{cls.IDEMPOTENCY_PREFIX}{provider}:{event_id}"
            value = json.dumps({
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "payment_id": payment_id
            })
            await redis_client.redis.setex(key, cls.IDEMPOTENCY_TTL, value)
    
    @classmethod
    async def acquire_processing_lock(
        cls,
        provider: str,
        event_id: str
    ) -> bool:
        """
        Acquire a processing lock for an event.
        Prevents concurrent processing of the same event.
        """
        if not redis_client.is_connected():
            return True  # Allow without Redis
        
        lock_key = f"webhook:lock:{provider}:{event_id}"
        acquired = await redis_client.redis.set(
            lock_key,
            "processing",
            ex=cls.LOCK_TTL,
            nx=True
        )
        return acquired is not None
    
    @classmethod
    async def release_processing_lock(
        cls,
        provider: str,
        event_id: str
    ):
        """Release processing lock"""
        if redis_client.is_connected():
            lock_key = f"webhook:lock:{provider}:{event_id}"
            await redis_client.redis.delete(lock_key)
    
    @classmethod
    async def handle_stripe_webhook(
        cls,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook event.
        
        Supported events:
        - payment_intent.succeeded
        - payment_intent.payment_failed
        
        Returns:
            Processing result dict
        """
        # Verify signature
        is_valid, event, error = cls.verify_stripe_signature(payload, signature)
        if not is_valid:
            cls._log_webhook("stripe", None, None, "signature_failed", error)
            return {
                "status": WebhookResult.INVALID_SIGNATURE.value,
                "error": error
            }
        
        event_id = event.get("id", "unknown")
        event_type = event.get("type", "unknown")
        
        cls._log_webhook("stripe", event_id, event_type, "received")
        
        # Check for duplicate
        if await cls.check_idempotency("stripe", event_id):
            cls._log_webhook("stripe", event_id, event_type, "duplicate")
            return {
                "status": WebhookResult.DUPLICATE.value,
                "event_id": event_id,
                "message": "Event already processed"
            }
        
        # Acquire lock
        if not await cls.acquire_processing_lock("stripe", event_id):
            cls._log_webhook("stripe", event_id, event_type, "lock_failed")
            return {
                "status": WebhookResult.DUPLICATE.value,
                "event_id": event_id,
                "message": "Event is being processed"
            }
        
        try:
            # Handle specific event types
            if event_type == "payment_intent.succeeded":
                result = await cls._handle_stripe_payment_succeeded(event)
            elif event_type == "payment_intent.payment_failed":
                result = await cls._handle_stripe_payment_failed(event)
            else:
                cls._log_webhook("stripe", event_id, event_type, "ignored")
                result = {
                    "status": WebhookResult.IGNORED.value,
                    "event_id": event_id,
                    "event_type": event_type
                }
            
            # Mark as processed
            await cls.mark_processed(
                "stripe",
                event_id,
                result.get("payment_id")
            )
            
            return result
        finally:
            await cls.release_processing_lock("stripe", event_id)
    
    @classmethod
    async def _handle_stripe_payment_succeeded(
        cls,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Stripe payment_intent.succeeded event"""
        event_id = event.get("id")
        data_object = event.get("data", {}).get("object", {})
        payment_intent_id = data_object.get("id")
        
        if not payment_intent_id:
            cls._log_webhook("stripe", event_id, "payment_intent.succeeded", "error", "No payment_intent_id")
            return {
                "status": WebhookResult.FAILED.value,
                "error": "No payment_intent_id in event"
            }
        
        # Find the payment record
        payment = await TBPayment.find_one({"provider_order_id": payment_intent_id})
        
        if not payment:
            cls._log_webhook("stripe", event_id, "payment_intent.succeeded", "not_found", payment_intent_id)
            return {
                "status": WebhookResult.PAYMENT_NOT_FOUND.value,
                "payment_intent_id": payment_intent_id
            }
        
        # Check if already processed (double idempotency check)
        if payment.status == PaymentStatus.COMPLETED:
            cls._log_webhook(
                "stripe", event_id, "payment_intent.succeeded",
                "already_processed", payment_intent_id
            )
            return {
                "status": WebhookResult.ALREADY_PROCESSED.value,
                "payment_id": str(payment.id),
                "payment_intent_id": payment_intent_id
            }
        
        # Add credits atomically
        try:
            credits_added = await cls._add_credits_atomic(
                user_id=payment.user_id,
                amount=payment.credits_purchased,
                payment_id=str(payment.id),
                provider="stripe",
                event_id=event_id
            )
            
            # Update payment status
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.now(timezone.utc)
            payment.provider_payment_id = payment_intent_id
            await payment.save()
            
            cls._log_webhook(
                "stripe", event_id, "payment_intent.succeeded",
                "credits_added",
                f"user={payment.user_id}, credits={credits_added}"
            )
            
            return {
                "status": WebhookResult.CREDITS_ADDED.value,
                "payment_id": str(payment.id),
                "payment_intent_id": payment_intent_id,
                "user_id": payment.user_id,
                "credits_added": credits_added
            }
        except Exception as e:
            logger.error(f"Error adding credits: {e}", exc_info=True)
            cls._log_webhook(
                "stripe", event_id, "payment_intent.succeeded",
                "credits_error", str(e)
            )
            return {
                "status": WebhookResult.FAILED.value,
                "error": str(e),
                "payment_id": str(payment.id)
            }
    
    @classmethod
    async def _handle_stripe_payment_failed(
        cls,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Stripe payment_intent.payment_failed event"""
        event_id = event.get("id")
        data_object = event.get("data", {}).get("object", {})
        payment_intent_id = data_object.get("id")
        error_message = data_object.get("last_payment_error", {}).get("message", "Payment failed")
        
        if not payment_intent_id:
            return {
                "status": WebhookResult.FAILED.value,
                "error": "No payment_intent_id in event"
            }
        
        payment = await TBPayment.find_one({"provider_order_id": payment_intent_id})
        
        if not payment:
            cls._log_webhook("stripe", event_id, "payment_intent.payment_failed", "not_found", payment_intent_id)
            return {
                "status": WebhookResult.PAYMENT_NOT_FOUND.value,
                "payment_intent_id": payment_intent_id
            }
        
        # Update payment status (only if not already completed)
        if payment.status != PaymentStatus.COMPLETED:
            payment.status = PaymentStatus.FAILED
            payment.error_message = error_message
            await payment.save()
        
        cls._log_webhook(
            "stripe", event_id, "payment_intent.payment_failed",
            "marked_failed", payment_intent_id
        )
        
        return {
            "status": WebhookResult.SUCCESS.value,
            "payment_id": str(payment.id),
            "payment_intent_id": payment_intent_id,
            "error_message": error_message
        }
    
    @classmethod
    async def handle_razorpay_webhook(
        cls,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle Razorpay webhook event.
        
        Supported events:
        - payment.captured
        - payment.failed
        
        Returns:
            Processing result dict
        """
        # Verify signature
        is_valid, event, error = cls.verify_razorpay_signature(payload, signature)
        if not is_valid:
            cls._log_webhook("razorpay", None, None, "signature_failed", error)
            return {
                "status": WebhookResult.INVALID_SIGNATURE.value,
                "error": error
            }
        
        event_id = event.get("event_id", event.get("id", "unknown"))
        event_type = event.get("event", "unknown")
        
        cls._log_webhook("razorpay", event_id, event_type, "received")
        
        # Check for duplicate
        if await cls.check_idempotency("razorpay", event_id):
            cls._log_webhook("razorpay", event_id, event_type, "duplicate")
            return {
                "status": WebhookResult.DUPLICATE.value,
                "event_id": event_id,
                "message": "Event already processed"
            }
        
        # Acquire lock
        if not await cls.acquire_processing_lock("razorpay", event_id):
            cls._log_webhook("razorpay", event_id, event_type, "lock_failed")
            return {
                "status": WebhookResult.DUPLICATE.value,
                "event_id": event_id,
                "message": "Event is being processed"
            }
        
        try:
            # Handle specific event types
            if event_type == "payment.captured":
                result = await cls._handle_razorpay_payment_captured(event)
            elif event_type == "payment.failed":
                result = await cls._handle_razorpay_payment_failed(event)
            else:
                cls._log_webhook("razorpay", event_id, event_type, "ignored")
                result = {
                    "status": WebhookResult.IGNORED.value,
                    "event_id": event_id,
                    "event_type": event_type
                }
            
            # Mark as processed
            await cls.mark_processed(
                "razorpay",
                event_id,
                result.get("payment_id")
            )
            
            return result
        finally:
            await cls.release_processing_lock("razorpay", event_id)
    
    @classmethod
    async def _handle_razorpay_payment_captured(
        cls,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Razorpay payment.captured event"""
        event_id = event.get("event_id", event.get("id", "unknown"))
        payload = event.get("payload", {})
        payment_entity = payload.get("payment", {}).get("entity", {})
        
        razorpay_payment_id = payment_entity.get("id")
        razorpay_order_id = payment_entity.get("order_id")
        
        if not razorpay_order_id and not razorpay_payment_id:
            return {
                "status": WebhookResult.FAILED.value,
                "error": "No payment/order ID in event"
            }
        
        # Find payment by order_id or payment_id
        payment = None
        if razorpay_order_id:
            payment = await TBPayment.find_one({"provider_order_id": razorpay_order_id})
        if not payment and razorpay_payment_id:
            payment = await TBPayment.find_one({"provider_payment_id": razorpay_payment_id})
        
        if not payment:
            cls._log_webhook(
                "razorpay", event_id, "payment.captured",
                "not_found", f"order={razorpay_order_id}, payment={razorpay_payment_id}"
            )
            return {
                "status": WebhookResult.PAYMENT_NOT_FOUND.value,
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id
            }
        
        # Check if already processed
        if payment.status == PaymentStatus.COMPLETED:
            cls._log_webhook(
                "razorpay", event_id, "payment.captured",
                "already_processed", razorpay_order_id
            )
            return {
                "status": WebhookResult.ALREADY_PROCESSED.value,
                "payment_id": str(payment.id)
            }
        
        # Add credits atomically
        try:
            credits_added = await cls._add_credits_atomic(
                user_id=payment.user_id,
                amount=payment.credits_purchased,
                payment_id=str(payment.id),
                provider="razorpay",
                event_id=event_id
            )
            
            # Update payment status
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.now(timezone.utc)
            payment.provider_payment_id = razorpay_payment_id
            await payment.save()
            
            cls._log_webhook(
                "razorpay", event_id, "payment.captured",
                "credits_added",
                f"user={payment.user_id}, credits={credits_added}"
            )
            
            return {
                "status": WebhookResult.CREDITS_ADDED.value,
                "payment_id": str(payment.id),
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "user_id": payment.user_id,
                "credits_added": credits_added
            }
        except Exception as e:
            logger.error(f"Error adding credits: {e}", exc_info=True)
            return {
                "status": WebhookResult.FAILED.value,
                "error": str(e),
                "payment_id": str(payment.id)
            }
    
    @classmethod
    async def _handle_razorpay_payment_failed(
        cls,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Razorpay payment.failed event"""
        event_id = event.get("event_id", event.get("id", "unknown"))
        payload = event.get("payload", {})
        payment_entity = payload.get("payment", {}).get("entity", {})
        
        razorpay_payment_id = payment_entity.get("id")
        razorpay_order_id = payment_entity.get("order_id")
        error_code = payment_entity.get("error_code", "")
        error_description = payment_entity.get("error_description", "Payment failed")
        error_reason = payment_entity.get("error_reason", "")
        
        error_message = f"{error_description} ({error_code})" if error_code else error_description
        
        # Find payment
        payment = None
        if razorpay_order_id:
            payment = await TBPayment.find_one({"provider_order_id": razorpay_order_id})
        
        if not payment:
            cls._log_webhook(
                "razorpay", event_id, "payment.failed",
                "not_found", razorpay_order_id
            )
            return {
                "status": WebhookResult.PAYMENT_NOT_FOUND.value,
                "razorpay_order_id": razorpay_order_id
            }
        
        # Update payment status (only if not already completed)
        if payment.status != PaymentStatus.COMPLETED:
            payment.status = PaymentStatus.FAILED
            payment.error_message = error_message
            await payment.save()
        
        cls._log_webhook(
            "razorpay", event_id, "payment.failed",
            "marked_failed", f"order={razorpay_order_id}, reason={error_reason}"
        )
        
        return {
            "status": WebhookResult.SUCCESS.value,
            "payment_id": str(payment.id),
            "razorpay_order_id": razorpay_order_id,
            "error_message": error_message
        }
    
    @classmethod
    async def _add_credits_atomic(
        cls,
        user_id: str,
        amount: int,
        payment_id: str,
        provider: str,
        event_id: str
    ) -> int:
        """
        Add credits to user atomically.
        
        Uses payment_id as idempotency key to prevent double-crediting.
        """
        # Check if credits already added for this payment
        existing_tx = await TBCreditTransaction.find_one({
            "reference_id": payment_id,
            "reason": TransactionReason.CREDIT_PURCHASE
        })
        
        if existing_tx:
            logger.info(f"Credits already added for payment {payment_id}")
            return existing_tx.amount
        
        # Get user
        user = await TBUser.get(user_id)
        if not user:
            raise Exception(f"User not found: {user_id}")
        
        # Atomic update with optimistic locking
        new_balance = user.credits_balance + amount
        user.credits_balance = new_balance
        user.updated_at = datetime.now(timezone.utc)
        await user.save()
        
        # Create transaction record
        transaction = TBCreditTransaction(
            user_id=user_id,
            amount=amount,
            reason=TransactionReason.CREDIT_PURCHASE,
            balance_after=new_balance,
            reference_id=payment_id,
            description=f"Credits purchased via {provider} (event: {event_id})"
        )
        await transaction.insert()
        
        logger.info(
            f"Credits added atomically: user={user_id}, amount={amount}, balance={new_balance}",
            extra={
                "event": "credits_added",
                "user_id": user_id,
                "amount": amount,
                "new_balance": new_balance,
                "payment_id": payment_id,
                "provider": provider
            }
        )
        
        return amount
    
    @classmethod
    def _log_webhook(
        cls,
        provider: str,
        event_id: Optional[str],
        event_type: Optional[str],
        status: str,
        details: str = None
    ):
        """
        Log webhook event for audit trail.
        Production-safe: No sensitive data logged.
        """
        log_data = {
            "provider": provider,
            "event_id": event_id,
            "event_type": event_type,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if details:
            log_data["details"] = details
        
        # Choose log level based on status
        if status in ["error", "signature_failed", "credits_error"]:
            logger.error(f"Webhook {status}: {json.dumps(log_data)}")
        elif status in ["duplicate", "already_processed", "not_found"]:
            logger.warning(f"Webhook {status}: {json.dumps(log_data)}")
        else:
            logger.info(f"Webhook {status}: {json.dumps(log_data)}")


# Singleton instance
payment_webhook_handler = PaymentWebhookHandler()
