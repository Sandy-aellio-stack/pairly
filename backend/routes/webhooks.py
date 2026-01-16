"""
Payment Webhooks - Stripe and Razorpay
Production-ready webhook handlers with:
- Signature verification
- Idempotent processing
- Atomic credit updates
- Comprehensive logging
"""
from fastapi import APIRouter, Request, HTTPException, Header, status
from typing import Optional
import logging

from backend.services.payment_webhook_handler import (
    PaymentWebhookHandler,
    WebhookResult
)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger("webhooks")


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhook events.
    
    Supported events:
    - payment_intent.succeeded: Add credits to user
    - payment_intent.payment_failed: Mark payment as failed
    
    Security:
    - Verifies webhook signature using Stripe signing secret
    - Idempotent - safe to receive duplicate events
    - Atomic credit updates - no double-crediting
    
    Returns:
    - 200 OK for successfully processed events
    - 200 OK for duplicate events (idempotent)
    - 200 OK for ignored events (unhandled event types)
    - 400 Bad Request for invalid signature
    - 500 Internal Server Error for processing failures
    """
    if not stripe_signature:
        logger.warning("Stripe webhook: Missing stripe-signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    payload = await request.body()
    
    # Process webhook using handler
    result = await PaymentWebhookHandler.handle_stripe_webhook(
        payload=payload,
        signature=stripe_signature
    )
    
    result_status = result.get("status")
    
    # Handle different results
    if result_status == WebhookResult.INVALID_SIGNATURE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    if result_status == WebhookResult.FAILED.value:
        logger.error(f"Stripe webhook processing failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
    
    # All other statuses are considered successful
    return {
        "status": "received",
        "result": result_status,
        "event_id": result.get("event_id"),
        "credits_added": result.get("credits_added")
    }


@router.post("/stripe/credits")
async def stripe_credits_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Dedicated Stripe webhook for Luveloop credit purchases.
    
    This is the ONLY endpoint that adds credits to user accounts.
    Credits are NEVER added from frontend or verify endpoints.
    
    Flow:
    1. Stripe sends payment_intent.succeeded webhook
    2. Signature is verified
    3. Payment record is found by payment_intent_id
    4. Credits are added atomically (with idempotency)
    5. Payment is marked as completed
    
    Idempotency:
    - Uses event_id for deduplication
    - Uses payment_id as credit transaction reference
    - Safe to receive multiple times
    """
    if not stripe_signature:
        logger.warning("Stripe credits webhook: Missing signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    payload = await request.body()
    
    result = await PaymentWebhookHandler.handle_stripe_webhook(
        payload=payload,
        signature=stripe_signature
    )
    
    result_status = result.get("status")
    
    if result_status == WebhookResult.INVALID_SIGNATURE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    if result_status == WebhookResult.FAILED.value:
        logger.error(f"Stripe credits webhook failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credits fulfillment failed"
        )
    
    if result_status == WebhookResult.CREDITS_ADDED.value:
        logger.info(
            f"Credits added via webhook: {result.get('credits_added')} for user {result.get('user_id')}"
        )
    
    return {
        "status": "success" if result_status in [
            WebhookResult.CREDITS_ADDED.value,
            WebhookResult.DUPLICATE.value,
            WebhookResult.ALREADY_PROCESSED.value
        ] else "received",
        "result": result_status,
        "credits_added": result.get("credits_added"),
        "user_id": result.get("user_id")
    }


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature")
):
    """
    Handle Razorpay webhook events.
    
    Supported events:
    - payment.captured: Add credits to user
    - payment.failed: Mark payment as failed
    
    Security:
    - Verifies webhook signature using HMAC SHA-256
    - Idempotent - safe to receive duplicate events
    - Atomic credit updates - no double-crediting
    
    Returns:
    - 200 OK for successfully processed events
    - 200 OK for duplicate events (idempotent)
    - 200 OK for ignored events (unhandled event types)
    - 400 Bad Request for invalid signature
    - 500 Internal Server Error for processing failures
    """
    if not x_razorpay_signature:
        logger.warning("Razorpay webhook: Missing X-Razorpay-Signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header"
        )
    
    payload = await request.body()
    
    # Process webhook using handler
    result = await PaymentWebhookHandler.handle_razorpay_webhook(
        payload=payload,
        signature=x_razorpay_signature
    )
    
    result_status = result.get("status")
    
    # Handle different results
    if result_status == WebhookResult.INVALID_SIGNATURE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    if result_status == WebhookResult.FAILED.value:
        logger.error(f"Razorpay webhook processing failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
    
    # All other statuses are considered successful
    return {
        "status": "received",
        "result": result_status,
        "event_id": result.get("event_id"),
        "credits_added": result.get("credits_added")
    }


@router.post("/razorpay/credits")
async def razorpay_credits_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature")
):
    """
    Dedicated Razorpay webhook for Luveloop credit purchases.
    
    This is the ONLY endpoint that adds credits for Razorpay payments.
    Credits are NEVER added from frontend or verify endpoints.
    
    Flow:
    1. Razorpay sends payment.captured webhook
    2. Signature is verified using HMAC SHA-256
    3. Payment record is found by order_id or payment_id
    4. Credits are added atomically (with idempotency)
    5. Payment is marked as completed
    
    Idempotency:
    - Uses event_id for deduplication
    - Uses payment_id as credit transaction reference
    - Safe to receive multiple times
    """
    if not x_razorpay_signature:
        logger.warning("Razorpay credits webhook: Missing signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header"
        )
    
    payload = await request.body()
    
    result = await PaymentWebhookHandler.handle_razorpay_webhook(
        payload=payload,
        signature=x_razorpay_signature
    )
    
    result_status = result.get("status")
    
    if result_status == WebhookResult.INVALID_SIGNATURE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    if result_status == WebhookResult.FAILED.value:
        logger.error(f"Razorpay credits webhook failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credits fulfillment failed"
        )
    
    if result_status == WebhookResult.CREDITS_ADDED.value:
        logger.info(
            f"Credits added via Razorpay webhook: {result.get('credits_added')} for user {result.get('user_id')}"
        )
    
    return {
        "status": "success" if result_status in [
            WebhookResult.CREDITS_ADDED.value,
            WebhookResult.DUPLICATE.value,
            WebhookResult.ALREADY_PROCESSED.value
        ] else "received",
        "result": result_status,
        "credits_added": result.get("credits_added"),
        "user_id": result.get("user_id")
    }


# Health check endpoint for webhook infrastructure
@router.get("/health")
async def webhook_health():
    """
    Check webhook handler health.
    Used by payment providers to verify endpoint availability.
    """
    return {
        "status": "healthy",
        "service": "webhook-handler",
        "supported_providers": ["stripe", "razorpay"],
        "supported_events": {
            "stripe": ["payment_intent.succeeded", "payment_intent.payment_failed"],
            "razorpay": ["payment.captured", "payment.failed"]
        }
    }
