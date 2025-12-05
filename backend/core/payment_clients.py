import stripe
import razorpay
import hmac
import hashlib
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) if RAZORPAY_KEY_ID else None

class StripeClient:
    @staticmethod
    async def get_or_create_customer(user_id: str, email: str, name: str) -> str:
        """Get existing Stripe customer or create new one"""
        # Search for existing customer
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            return customers.data[0].id
        
        # Create new customer
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"user_id": user_id}
        )
        return customer.id

    @staticmethod
    async def attach_payment_method(customer_id: str, payment_method_id: str):
        """Attach payment method to customer"""
        stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        stripe.Customer.modify(
            customer_id,
            invoice_settings={"default_payment_method": payment_method_id}
        )

    @staticmethod
    async def create_subscription(
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Stripe subscription"""
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
            metadata=metadata or {}
        )
        return subscription

    @staticmethod
    async def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout session"""
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {}
        )
        return session

    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature"""
        return stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )

    @staticmethod
    async def cancel_subscription(subscription_id: str, cancel_at_period_end: bool = True):
        """Cancel a Stripe subscription"""
        if cancel_at_period_end:
            return stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            return stripe.Subscription.delete(subscription_id)

class RazorpayClient:
    @staticmethod
    async def create_subscription(
        plan_id: str,
        customer_notify: int = 1,
        total_count: int = 12,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Razorpay subscription"""
        if not razorpay_client:
            raise ValueError("Razorpay client not configured")
        
        subscription = razorpay_client.subscription.create({
            "plan_id": plan_id,
            "customer_notify": customer_notify,
            "total_count": total_count,
            "notes": metadata or {}
        })
        return subscription

    @staticmethod
    async def create_order(
        amount: int,
        currency: str = "INR",
        receipt: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Razorpay order"""
        if not razorpay_client:
            raise ValueError("Razorpay client not configured")
        
        order = razorpay_client.order.create({
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "notes": metadata or {}
        })
        return order

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify Razorpay webhook signature"""
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

    @staticmethod
    async def cancel_subscription(subscription_id: str):
        """Cancel a Razorpay subscription"""
        if not razorpay_client:
            raise ValueError("Razorpay client not configured")
        
        return razorpay_client.subscription.cancel(subscription_id)

    @staticmethod
    async def fetch_subscription(subscription_id: str) -> Dict[str, Any]:
        """Fetch subscription details from Razorpay"""
        if not razorpay_client:
            raise ValueError("Razorpay client not configured")
        
        return razorpay_client.subscription.fetch(subscription_id)
