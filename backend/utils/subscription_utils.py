from typing import Optional, Dict, Any
from datetime import datetime
from backend.models.payment_subscription import UserSubscription, SubscriptionStatus
from backend.core.redis_client import redis_client

async def is_user_subscribed(user_id: str, tier_id: Optional[str] = None) -> bool:
    """Check if user has an active subscription
    
    Checks Redis cache first, then falls back to database.
    """
    # Check Redis cache
    cached = await redis_client.get_cached_subscription(user_id)
    if cached is not None:
        return cached
    
    # Query database
    query = {
        "user_id": user_id,
        "status": SubscriptionStatus.ACTIVE,
        "current_period_end": {"$gt": datetime.now()}
    }
    
    if tier_id:
        query["tier_id"] = tier_id
    
    subscription = await UserSubscription.find_one(query)
    is_subscribed = subscription is not None
    
    # Cache result
    await redis_client.cache_subscription(user_id, is_subscribed, ttl=300)
    
    return is_subscribed

async def sync_subscription_from_provider(event: Dict[str, Any], provider: str):
    """Sync subscription state from provider webhook event
    
    Updates UserSubscription based on webhook data.
    """
    if provider == "stripe":
        await _sync_stripe_subscription(event)
    elif provider == "razorpay":
        await _sync_razorpay_subscription(event)

async def _sync_stripe_subscription(event: Dict[str, Any]):
    """Sync Stripe subscription event"""
    event_type = event["type"]
    
    if event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            subscription = await UserSubscription.find_one(
                {"provider_subscription_id": subscription_id}
            )
            if subscription:
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.last_payment_at = datetime.now()
                subscription.current_period_end = datetime.fromtimestamp(
                    invoice.get("period_end", 0)
                )
                await subscription.save()
                await redis_client.invalidate_subscription_cache(subscription.user_id)
    
    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            subscription = await UserSubscription.find_one(
                {"provider_subscription_id": subscription_id}
            )
            if subscription:
                subscription.status = SubscriptionStatus.PAST_DUE
                await subscription.save()
                await redis_client.invalidate_subscription_cache(subscription.user_id)
    
    elif event_type == "customer.subscription.updated":
        sub_obj = event["data"]["object"]
        subscription_id = sub_obj["id"]
        
        subscription = await UserSubscription.find_one(
            {"provider_subscription_id": subscription_id}
        )
        if subscription:
            subscription.status = SubscriptionStatus(sub_obj["status"])
            subscription.cancel_at_period_end = sub_obj.get("cancel_at_period_end", False)
            subscription.current_period_end = datetime.fromtimestamp(
                sub_obj.get("current_period_end", 0)
            )
            await subscription.save()
            await redis_client.invalidate_subscription_cache(subscription.user_id)
    
    elif event_type == "customer.subscription.deleted":
        sub_obj = event["data"]["object"]
        subscription_id = sub_obj["id"]
        
        subscription = await UserSubscription.find_one(
            {"provider_subscription_id": subscription_id}
        )
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            await subscription.save()
            await redis_client.invalidate_subscription_cache(subscription.user_id)

async def _sync_razorpay_subscription(event: Dict[str, Any]):
    """Sync Razorpay subscription event"""
    event_type = event.get("event")
    payload = event.get("payload", {})
    subscription_entity = payload.get("subscription", {}).get("entity", {})
    
    if event_type == "subscription.charged":
        subscription_id = subscription_entity.get("id")
        
        if subscription_id:
            subscription = await UserSubscription.find_one(
                {"provider_subscription_id": subscription_id}
            )
            if subscription:
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.last_payment_at = datetime.now()
                await subscription.save()
                await redis_client.invalidate_subscription_cache(subscription.user_id)
    
    elif event_type == "subscription.cancelled":
        subscription_id = subscription_entity.get("id")
        
        if subscription_id:
            subscription = await UserSubscription.find_one(
                {"provider_subscription_id": subscription_id}
            )
            if subscription:
                subscription.status = SubscriptionStatus.CANCELED
                await subscription.save()
                await redis_client.invalidate_subscription_cache(subscription.user_id)

# Safe no-op stub for credits migration
async def migrate_credits_to_subscription():
    """Placeholder for future credits-to-subscription migration
    
    This is intentionally a no-op. Credits system remains independent.
    """
    pass
