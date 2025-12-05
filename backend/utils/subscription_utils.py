"""Subscription utility functions.

Helpers for checking subscriptions, syncing provider events, and caching.
"""
from typing import Optional
from beanie import PydanticObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def is_user_subscribed_to_tier(user_id: PydanticObjectId, tier_id: PydanticObjectId) -> bool:
    """Check if user has active subscription to tier.
    
    Uses Redis cache first, then falls back to database.
    
    Args:
        user_id: User ID
        tier_id: Subscription tier ID
        
    Returns:
        True if user is subscribed and subscription is active
    """
    from backend.core.redis_client import get_cached_subscription, cache_subscription
    from backend.models.payment_subscription import UserSubscription, SubscriptionStatus
    
    user_id_str = str(user_id)
    tier_id_str = str(tier_id)
    
    # Check cache first
    cached = await get_cached_subscription(user_id_str, tier_id_str)
    if cached is not None:
        return cached
    
    # Check database
    subscription = await UserSubscription.find_one(
        UserSubscription.user_id == user_id,
        UserSubscription.tier_id == tier_id,
        UserSubscription.status == SubscriptionStatus.ACTIVE
    )
    
    result = subscription is not None
    
    # Cache result
    await cache_subscription(user_id_str, tier_id_str, result, ttl=300)
    
    return result


async def is_user_subscribed_to_creator(user_id: PydanticObjectId, creator_id: PydanticObjectId) -> bool:
    """Check if user has any active subscription to creator.
    
    Args:
        user_id: User ID
        creator_id: Creator's profile ID
        
    Returns:
        True if user has any active subscription to this creator
    """
    from backend.models.payment_subscription import UserSubscription, SubscriptionStatus
    
    subscription = await UserSubscription.find_one(
        UserSubscription.user_id == user_id,
        UserSubscription.creator_id == creator_id,
        UserSubscription.status == SubscriptionStatus.ACTIVE
    )
    
    return subscription is not None


async def sync_subscription_from_provider(event_data: dict, provider: str):
    """Sync subscription state from provider webhook event.
    
    Args:
        event_data: Event data from webhook
        provider: 'stripe' or 'razorpay'
    """
    from backend.models.payment_subscription import UserSubscription, SubscriptionStatus, PaymentProvider, Payment
    from backend.core.redis_client import invalidate_subscription_cache
    
    try:
        if provider == 'stripe':
            await _sync_stripe_subscription(event_data)
        elif provider == 'razorpay':
            await _sync_razorpay_subscription(event_data)
        
        logger.info(f"Synced subscription from {provider} event")
        
    except Exception as e:
        logger.error(f"Failed to sync subscription from {provider}: {e}")
        raise


async def _sync_stripe_subscription(event_data: dict):
    """Sync Stripe subscription event."""
    from backend.models.payment_subscription import UserSubscription, SubscriptionStatus, Payment, PaymentProvider
    from backend.core.redis_client import invalidate_subscription_cache
    
    event_type = event_data.get('type')
    
    if event_type == 'customer.subscription.updated':
        sub_data = event_data['data']['object']
        sub_id = sub_data['id']
        
        # Find subscription in DB
        subscription = await UserSubscription.find_one(
            UserSubscription.provider_subscription_id == sub_id
        )
        
        if subscription:
            # Update status
            subscription.status = SubscriptionStatus(sub_data['status'])
            subscription.current_period_end = datetime.fromtimestamp(sub_data['current_period_end'])
            subscription.cancel_at_period_end = sub_data.get('cancel_at_period_end', False)
            subscription.last_synced_at = datetime.utcnow()
            
            await subscription.save()
            
            # Invalidate cache
            await invalidate_subscription_cache(str(subscription.user_id), str(subscription.tier_id))
            
    elif event_type == 'customer.subscription.deleted':
        sub_data = event_data['data']['object']
        sub_id = sub_data['id']
        
        subscription = await UserSubscription.find_one(
            UserSubscription.provider_subscription_id == sub_id
        )
        
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.utcnow()
            subscription.last_synced_at = datetime.utcnow()
            
            await subscription.save()
            await invalidate_subscription_cache(str(subscription.user_id), str(subscription.tier_id))


async def _sync_razorpay_subscription(event_data: dict):
    """Sync Razorpay subscription event."""
    from backend.models.payment_subscription import UserSubscription, SubscriptionStatus
    from backend.core.redis_client import invalidate_subscription_cache
    
    event_type = event_data.get('event')
    
    if event_type in ['subscription.charged', 'subscription.activated']:
        sub_data = event_data['payload']['subscription']['entity']
        sub_id = sub_data['id']
        
        subscription = await UserSubscription.find_one(
            UserSubscription.provider_subscription_id == sub_id
        )
        
        if subscription:
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.last_payment_at = datetime.utcnow()
            subscription.last_synced_at = datetime.utcnow()
            
            await subscription.save()
            await invalidate_subscription_cache(str(subscription.user_id), str(subscription.tier_id))
            
    elif event_type == 'subscription.cancelled':
        sub_data = event_data['payload']['subscription']['entity']
        sub_id = sub_data['id']
        
        subscription = await UserSubscription.find_one(
            UserSubscription.provider_subscription_id == sub_id
        )
        
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.utcnow()
            subscription.last_synced_at = datetime.utcnow()
            
            await subscription.save()
            await invalidate_subscription_cache(str(subscription.user_id), str(subscription.tier_id))


async def migrate_credits_to_subscription(user_id: PydanticObjectId, mapping: dict):
    """Migrate credits to subscription (safe no-op stub).
    
    This is a stub for future migration needs.
    
    Documentation:
    -------------
    In production, you might want to:
    1. Identify high-value credit users
    2. Offer them equivalent subscription tiers
    3. Convert their credit balance to subscription period
    
    Example mapping:
    {
        'user_id': '507f1f77bcf86cd799439011',
        'target_tier_id': '507f1f77bcf86cd799439012',
        'credit_balance': 10000,
        'equivalent_months': 2
    }
    
    Args:
        user_id: User to migrate
        mapping: Migration configuration
    """
    logger.info(f"Credits to subscription migration stub called for user {user_id}")
    logger.info("This is a safe no-op. Implement migration logic as needed.")
    pass
