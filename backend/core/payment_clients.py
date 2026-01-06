import stripe
import os
from typing import Dict, Any, Optional

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


class StripeClient:
    @staticmethod
    async def get_or_create_customer(user_id: str, email: str, name: str) -> str:
        """Get existing Stripe customer or create new one"""
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            return customers.data[0].id
        
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

    @staticmethod
    async def create_payment_intent(
        amount_cents: int,
        currency: str = "inr",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a payment intent for one-time payment"""
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata=metadata or {}
        )
        return {"id": intent.id, "client_secret": intent.client_secret}
