"""Payment provider clients for Stripe and Razorpay."""
import stripe
import razorpay
import os
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
from backend.models.user import User

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None


async def get_or_create_stripe_customer(user: User) -> str:
    """Get or create Stripe customer."""
    try:
        customers = stripe.Customer.list(email=user.email, limit=1)
        
        if customers.data:
            return customers.data[0].id
        
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": str(user.id), "platform": "pairly"}
        )
        
        return customer.id
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


async def attach_payment_method_stripe(customer_id: str, payment_method_id: str, set_as_default: bool = True) -> Dict[str, Any]:
    """Attach payment method to Stripe customer."""
    try:
        payment_method = stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        
        if set_as_default:
            stripe.Customer.modify(customer_id, invoice_settings={"default_payment_method": payment_method_id})
        
        return payment_method
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


async def create_stripe_subscription(customer_id: str, price_id: str, trial_days: int = 0, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Create Stripe subscription."""
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
        return subscription
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


async def cancel_stripe_subscription(subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
    """Cancel Stripe subscription."""
    try:
        if at_period_end:
            subscription = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
        else:
            subscription = stripe.Subscription.delete(subscription_id)
        return subscription
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


def verify_stripe_webhook(payload: bytes, sig_header: str) -> Dict[str, Any]:
    """Verify Stripe webhook signature."""
    if not STRIPE_WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        return event
    except Exception as e:
        raise ValueError(f"Invalid signature: {str(e)}")


async def create_razorpay_subscription(plan_id: str, customer_notify: int = 1, total_count: int = 12, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Create Razorpay subscription."""
    if not razorpay_client:
        raise Exception("Razorpay not configured")
    
    try:
        params = {"plan_id": plan_id, "customer_notify": customer_notify, "total_count": total_count}
        if metadata:
            params["notes"] = metadata
        
        return razorpay_client.subscription.create(params)
    except razorpay.errors.BadRequestError as e:
        raise Exception(f"Razorpay error: {str(e)}")


async def cancel_razorpay_subscription(subscription_id: str, cancel_at_cycle_end: int = 1) -> Dict[str, Any]:
    """Cancel Razorpay subscription."""
    if not razorpay_client:
        raise Exception("Razorpay not configured")
    
    try:
        return razorpay_client.subscription.cancel(subscription_id, cancel_at_cycle_end)
    except razorpay.errors.BadRequestError as e:
        raise Exception(f"Razorpay error: {str(e)}")


def verify_razorpay_signature(payload: str, signature: str, secret: Optional[str] = None) -> bool:
    """Verify Razorpay webhook signature."""
    if secret is None:
        secret = RAZORPAY_KEY_SECRET
    
    if not secret:
        raise ValueError("Razorpay webhook secret not configured")
    
    expected_signature = hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature):
        raise ValueError("Invalid Razorpay webhook signature")
    
    return True


async def create_razorpay_order_for_subscription(amount_paise: int, currency: str = "INR", notes: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Create Razorpay order for subscription."""
    if not razorpay_client:
        raise Exception("Razorpay not configured")
    
    try:
        params = {"amount": amount_paise, "currency": currency, "payment_capture": 1}
        if notes:
            params["notes"] = notes
        
        return razorpay_client.order.create(params)
    except razorpay.errors.BadRequestError as e:
        raise Exception(f"Razorpay error: {str(e)}")
