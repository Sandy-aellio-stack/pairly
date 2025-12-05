from fastapi import APIRouter, Request, HTTPException, Header, status
from typing import Optional
import json
import os

from backend.core.payment_clients import StripeClient, RazorpayClient
from backend.utils.subscription_utils import sync_subscription_from_provider
from backend.core.redis_client import redis_client

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events with signature verification and idempotency"""
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    payload = await request.body()
    
    try:
        # Verify webhook signature
        event = StripeClient.verify_webhook_signature(payload, stripe_signature)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signature verification failed: {str(e)}"
        )
    
    # Idempotency lock using Redis
    event_id = event.get("id")
    async with redis_client.acquire_lock(f"stripe_webhook:{event_id}", ttl=300) as acquired:
        if not acquired:
            # Event already being processed or was processed
            return {"status": "duplicate", "message": "Event already processed"}
        
        # Process event
        event_type = event.get("type")
        handled_events = [
            "invoice.payment_succeeded",
            "invoice.payment_failed",
            "customer.subscription.updated",
            "customer.subscription.deleted"
        ]
        
        if event_type in handled_events:
            await sync_subscription_from_provider(event, "stripe")
            return {"status": "success", "event_type": event_type}
        else:
            return {"status": "ignored", "event_type": event_type}

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):
    """Handle Razorpay webhook events with signature verification and idempotency"""
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing x-razorpay-signature header"
        )
    
    payload = await request.body()
    payload_str = payload.decode("utf-8")
    
    # Verify webhook signature
    is_valid = RazorpayClient.verify_webhook_signature(
        payload_str,
        x_razorpay_signature,
        RAZORPAY_WEBHOOK_SECRET
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signature verification failed"
        )
    
    event = json.loads(payload_str)
    event_id = event.get("id") or event.get("payload", {}).get("payment", {}).get("entity", {}).get("id")
    
    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event ID"
        )
    
    # Idempotency lock using Redis
    async with redis_client.acquire_lock(f"razorpay_webhook:{event_id}", ttl=300) as acquired:
        if not acquired:
            return {"status": "duplicate", "message": "Event already processed"}
        
        # Process event
        event_type = event.get("event")
        handled_events = ["subscription.charged", "subscription.cancelled"]
        
        if event_type in handled_events:
            await sync_subscription_from_provider(event, "razorpay")
            return {"status": "success", "event_type": event_type}
        else:
            return {"status": "ignored", "event_type": event_type}
