from fastapi import APIRouter, Request, HTTPException, Header, status
from typing import Optional
import logging

from backend.core.payment_clients import StripeClient
from backend.utils.subscription_utils import sync_subscription_from_provider
from backend.core.redis_client import redis_client
from backend.services.webhooks.event_handler import WebhookEventHandler
from backend.services.tb_payment_service import PaymentService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("webhooks")


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events with signature verification and idempotency"""
    if not stripe_signature:
        logger.warning("Missing stripe-signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    payload = await request.body()
    
    try:
        event = StripeClient.verify_webhook_signature(payload, stripe_signature)
    except ValueError as e:
        logger.error(f"Invalid Stripe payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except Exception as e:
        logger.error(f"Stripe signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signature verification failed"
        )
    
    event_id = event.get("id")
    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event ID"
        )
    
    async with redis_client.acquire_lock(f"stripe_webhook:{event_id}", ttl=300) as acquired:
        if not acquired:
            logger.info(f"Duplicate webhook event ignored: {event_id}")
            return {"status": "duplicate", "message": "Event already processed"}
        
        event_type = event.get("type")
        
        payment_events = [
            "payment_intent.succeeded",
            "payment_intent.failed",
            "payment_intent.processing"
        ]
        
        subscription_events = [
            "invoice.payment_succeeded",
            "invoice.payment_failed",
            "customer.subscription.updated",
            "customer.subscription.deleted"
        ]
        
        if event_type in payment_events:
            handler = WebhookEventHandler(mock_mode=False)
            success, error, payment_id = await handler.handle_stripe_event(event_type, event)
            
            if not success:
                logger.error(f"Payment event handling failed: {error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Event processing failed"
                )
            
            logger.info(f"Payment event processed: {event_type}, payment_id: {payment_id}")
            return {"status": "success", "event_type": event_type}
        
        elif event_type in subscription_events:
            await sync_subscription_from_provider(event, "stripe")
            logger.info(f"Subscription event processed: {event_type}")
            return {"status": "success", "event_type": event_type}
        
        else:
            logger.debug(f"Unhandled event type ignored: {event_type}")
            return {"status": "ignored", "event_type": event_type}


@router.post("/stripe/credits")
async def stripe_credits_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Dedicated webhook for TrueBond credit purchases.
    Credits are ONLY added through this webhook - never from frontend.
    """
    if not stripe_signature:
        logger.warning("Missing stripe-signature header for credits webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    payload = await request.body()
    
    try:
        event = StripeClient.verify_webhook_signature(payload, stripe_signature)
    except Exception as e:
        logger.error(f"Credits webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signature verification failed"
        )
    
    event_id = event.get("id")
    event_type = event.get("type")
    
    async with redis_client.acquire_lock(f"stripe_credits:{event_id}", ttl=3600) as acquired:
        if not acquired:
            logger.info(f"Duplicate credits webhook ignored: {event_id}")
            return {"status": "duplicate"}
        
        if event_type == "payment_intent.succeeded":
            data_object = event.get('data', {}).get('object', {})
            payment_intent_id = data_object.get('id')
            
            if payment_intent_id:
                result = await PaymentService.fulfill_payment_via_webhook(payment_intent_id)
                
                if result.get("success"):
                    logger.info(f"Credits added via webhook: {result.get('credits_added')} for user {result.get('user_id')}")
                    return {"status": "success", "credits_added": result.get("credits_added")}
                else:
                    logger.error(f"Credits fulfillment failed: {result.get('error')}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Credits fulfillment failed"
                    )
            else:
                logger.warning("No payment_intent_id in webhook event")
                return {"status": "error", "message": "No payment intent ID"}
        
        return {"status": "ignored", "event_type": event_type}
