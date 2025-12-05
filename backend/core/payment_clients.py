"""Payment provider clients for Stripe and Razorpay.

Centralizes all payment provider interactions.
"""
import stripe
import razorpay
import os
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
from backend.models.user import User

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Initialize Razorpay
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None


# ============================================================================
# STRIPE HELPERS
# ============================================================================

async def get_or_create_stripe_customer(user: User) -> str:
    """Get or create Stripe customer for user.
    
    Args:
        user: User object
        
    Returns:
        Stripe customer ID
    """
    try:
        # Search for existing customer by email
        customers = stripe.Customer.list(email=user.email, limit=1)
        
        if customers.data:
            logger.info(f"Found existing Stripe customer for user {user.id}")
            return customers.data[0].id
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name if hasattr(user, 'name') else None,
            metadata={
                "user_id": str(user.id),
                "platform": "pairly"
            }
        )
        
        logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
        return customer.id
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe customer creation failed: {str(e)}")
        raise Exception(f"Stripe error: {str(e)}")


async def attach_payment_method_stripe(
    customer_id: str,
    payment_method_id: str,
    set_as_default: bool = True
) -> Dict[str, Any]:
    """Attach payment method to Stripe customer.
    
    Args:
        customer_id: Stripe customer ID
        payment_method_id: Stripe payment method ID
        set_as_default: Set as default payment method
        
    Returns:
        Payment method object
    """
    try:
        # Attach payment method to customer
        payment_method = stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id
        )
        
        # Set as default if requested
        if set_as_default:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )
        
        logger.info(f"Attached payment method {payment_method_id} to customer {customer_id}")
        return payment_method
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe payment method attachment failed: {str(e)}")
        raise Exception(f"Stripe error: {str(e)}")


async def create_stripe_subscription(
    customer_id: str,
    price_id: str,
    trial_days: int = 0,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create Stripe subscription.
    
    Args:
        customer_id: Stripe customer ID
        price_id: Stripe price ID
        trial_days: Trial period in days
        metadata: Additional metadata
        
    Returns:
        Subscription object
    """
    try:
        params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "payment_behavior": "default_incomplete",
            "payment_settings": {"save_default_payment_method": "on_subscription"},
            "expand": ["latest_invoice.payment_intent"],
        }
        
        if trial_days > 0:
            params["trial_period_days"] = trial_days
        
        if metadata:
            params["metadata"] = metadata
        
        subscription = stripe.Subscription.create(**params)
        
        logger.info(f"Created Stripe subscription {subscription.id} for customer {customer_id}")
        return subscription
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription creation failed: {str(e)}")
        raise Exception(f"Stripe error: {str(e)}")


async def cancel_stripe_subscription(
    subscription_id: str,
    at_period_end: bool = True
) -> Dict[str, Any]:
    """Cancel Stripe subscription.
    
    Args:
        subscription_id: Stripe subscription ID
        at_period_end: Cancel at end of period or immediately
        
    Returns:
        Updated subscription object
    """
    try:
        if at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"Scheduled Stripe subscription {subscription_id} for cancellation at period end")
        else:
            subscription = stripe.Subscription.delete(subscription_id)
            logger.info(f"Immediately canceled Stripe subscription {subscription_id}")
        
        return subscription
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription cancellation failed: {str(e)}")
        raise Exception(f"Stripe error: {str(e)}")


def verify_stripe_webhook(payload: bytes, sig_header: str) -> Dict[str, Any]:
    """Verify Stripe webhook signature.
    
    Args:
        payload: Raw request body
        sig_header: Stripe-Signature header
        
    Returns:
        Verified event object
        
    Raises:
        ValueError: If signature is invalid
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        logger.info(f"Verified Stripe webhook event: {event['id']} ({event['type']})")
        return event
    except ValueError as e:
        logger.error(f"Stripe webhook signature verification failed: {str(e)}")
        raise ValueError(f"Invalid signature: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe signature verification error: {str(e)}")
        raise ValueError(f"Signature verification failed: {str(e)}")


# ============================================================================
# RAZORPAY HELPERS
# ============================================================================

async def create_razorpay_subscription(
    plan_id: str,
    customer_notify: int = 1,
    total_count: int = 12,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create Razorpay subscription.
    
    Args:
        plan_id: Razorpay plan ID
        customer_notify: Notify customer (1 = yes, 0 = no)
        total_count: Number of billing cycles
        metadata: Additional metadata
        
    Returns:
        Subscription object
    """
    if not razorpay_client:
        raise Exception("Razorpay client not initialized")
    
    try:
        params = {
            "plan_id": plan_id,
            "customer_notify": customer_notify,
            "total_count": total_count,
        }
        
        if metadata:
            params["notes"] = metadata
        
        subscription = razorpay_client.subscription.create(params)
        
        logger.info(f"Created Razorpay subscription {subscription['id']}")
        return subscription
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay subscription creation failed: {str(e)}")
        raise Exception(f"Razorpay error: {str(e)}")


async def cancel_razorpay_subscription(
    subscription_id: str,
    cancel_at_cycle_end: int = 1
) -> Dict[str, Any]:
    """Cancel Razorpay subscription.
    
    Args:
        subscription_id: Razorpay subscription ID
        cancel_at_cycle_end: Cancel at cycle end (1) or immediately (0)
        
    Returns:
        Updated subscription object
    """
    if not razorpay_client:
        raise Exception("Razorpay client not initialized")
    
    try:
        subscription = razorpay_client.subscription.cancel(
            subscription_id,
            cancel_at_cycle_end
        )
        
        logger.info(f"Canceled Razorpay subscription {subscription_id}")
        return subscription
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay subscription cancellation failed: {str(e)}")
        raise Exception(f"Razorpay error: {str(e)}")


def verify_razorpay_signature(
    payload: str,
    signature: str,
    secret: Optional[str] = None
) -> bool:
    """Verify Razorpay webhook signature.
    
    Args:
        payload: Raw request body as string
        signature: X-Razorpay-Signature header
        secret: Webhook secret (defaults to RAZORPAY_KEY_SECRET)
        
    Returns:
        True if signature is valid
        
    Raises:
        ValueError: If signature is invalid
    """
    if secret is None:
        secret = RAZORPAY_KEY_SECRET
    
    if not secret:
        raise ValueError("Razorpay webhook secret not configured")
    
    # Generate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(expected_signature, signature):
        logger.error("Razorpay webhook signature mismatch")
        raise ValueError("Invalid Razorpay webhook signature")
    
    logger.info("Razorpay webhook signature verified")
    return True


async def create_razorpay_order_for_subscription(
    amount_paise: int,
    currency: str = "INR",
    notes: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create Razorpay order for subscription payment.
    
    Args:
        amount_paise: Amount in paise (smallest currency unit)
        currency: Currency code (default INR)
        notes: Additional notes
        
    Returns:
        Order object
    """
    if not razorpay_client:
        raise Exception("Razorpay client not initialized")
    
    try:
        params = {
            "amount": amount_paise,
            "currency": currency,
            "payment_capture": 1,
        }
        
        if notes:
            params["notes"] = notes
        
        order = razorpay_client.order.create(params)
        
        logger.info(f"Created Razorpay order {order['id']}")
        return order
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay order creation failed: {str(e)}")
        raise Exception(f"Razorpay error: {str(e)}")
