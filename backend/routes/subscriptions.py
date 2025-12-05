from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.models.user import User
from backend.models.subscription import SubscriptionTier
from backend.models.payment_subscription import (
    UserSubscription,
    SubscriptionProvider,
    SubscriptionStatus
)
from backend.routes.auth import get_current_user
from backend.core.payment_clients import StripeClient, RazorpayClient
import os

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Feature flag
FEATURE_SUBSCRIPTIONS = os.getenv("FEATURE_SUBSCRIPTIONS", "true").lower() == "true"

class CreateSessionRequest(BaseModel):
    tier_id: str
    provider: SubscriptionProvider
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class CreateSessionResponse(BaseModel):
    session_id: Optional[str] = None
    client_secret: Optional[str] = None
    subscription_id: Optional[str] = None
    checkout_url: Optional[str] = None

@router.post("/create-session", response_model=CreateSessionResponse)
async def create_subscription_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a subscription session with Stripe or Razorpay"""
    if not FEATURE_SUBSCRIPTIONS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Subscriptions feature is not enabled"
        )
    
    # Get subscription tier
    tier = await SubscriptionTier.get(request.tier_id)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription tier not found"
        )
    
    # Check if user already has active subscription to this tier
    existing = await UserSubscription.find_one({
        "user_id": str(current_user.id),
        "tier_id": request.tier_id,
        "status": SubscriptionStatus.ACTIVE
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription to this tier"
        )
    
    if request.provider == SubscriptionProvider.STRIPE:
        # Stripe flow
        customer_id = await StripeClient.get_or_create_customer(
            user_id=str(current_user.id),
            email=current_user.email,
            name=getattr(current_user, 'display_name', current_user.email)
        )
        
        # Get or create Stripe price_id from tier metadata
        stripe_price_id = tier.metadata.get("stripe_price_id")
        if not stripe_price_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stripe price not configured for this tier"
            )
        
        # Create checkout session
        success_url = request.success_url or f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/subscription/success"
        cancel_url = request.cancel_url or f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/subscription/cancel"
        
        session = await StripeClient.create_checkout_session(
            customer_id=customer_id,
            price_id=stripe_price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "tier_id": request.tier_id
            }
        )
        
        # Create pending subscription record
        user_subscription = UserSubscription(
            user_id=str(current_user.id),
            tier_id=request.tier_id,
            provider_subscription_id=session.get("subscription", session["id"]),
            provider=SubscriptionProvider.STRIPE,
            status=SubscriptionStatus.TRIALING,
            metadata={
                "customer_id": customer_id,
                "session_id": session["id"]
            }
        )
        await user_subscription.insert()
        
        return CreateSessionResponse(
            session_id=session["id"],
            checkout_url=session.get("url")
        )
    
    elif request.provider == SubscriptionProvider.RAZORPAY:
        # Razorpay flow
        razorpay_plan_id = tier.metadata.get("razorpay_plan_id")
        if not razorpay_plan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Razorpay plan not configured for this tier"
            )
        
        subscription = await RazorpayClient.create_subscription(
            plan_id=razorpay_plan_id,
            customer_notify=1,
            total_count=12,
            metadata={
                "user_id": str(current_user.id),
                "tier_id": request.tier_id
            }
        )
        
        # Create subscription record
        user_subscription = UserSubscription(
            user_id=str(current_user.id),
            tier_id=request.tier_id,
            provider_subscription_id=subscription["id"],
            provider=SubscriptionProvider.RAZORPAY,
            status=SubscriptionStatus.TRIALING,
            metadata=subscription
        )
        await user_subscription.insert()
        
        return CreateSessionResponse(
            subscription_id=subscription["id"],
            checkout_url=subscription.get("short_url")
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid provider"
    )

@router.post("/cancel/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a user's subscription"""
    if not FEATURE_SUBSCRIPTIONS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Subscriptions feature is not enabled"
        )
    
    subscription = await UserSubscription.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    if subscription.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this subscription"
        )
    
    # Cancel with provider
    if subscription.provider == SubscriptionProvider.STRIPE:
        await StripeClient.cancel_subscription(
            subscription.provider_subscription_id,
            cancel_at_period_end=True
        )
    elif subscription.provider == SubscriptionProvider.RAZORPAY:
        await RazorpayClient.cancel_subscription(
            subscription.provider_subscription_id
        )
    
    # Update local record
    subscription.cancel_at_period_end = True
    subscription.updated_at = datetime.now()
    await subscription.save()
    
    return {"message": "Subscription will be canceled at period end"}

@router.get("", response_model=List[UserSubscription])
async def get_user_subscriptions(current_user: User = Depends(get_current_user)):
    """Get all subscriptions for the current user"""
    subscriptions = await UserSubscription.find(
        {"user_id": str(current_user.id)}
    ).to_list()
    return subscriptions

@router.get("/tiers", response_model=List[SubscriptionTier])
async def get_subscription_tiers():
    """Get all available subscription tiers"""
    tiers = await SubscriptionTier.find_all().to_list()
    return tiers
