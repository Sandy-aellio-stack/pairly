import stripe
import os
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel

from backend.models.tb_user import TBUser
from backend.models.tb_payment import TBPayment, PaymentStatus, PaymentProvider, CREDIT_PACKAGES

logger = logging.getLogger("payments")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

stripe.api_key = STRIPE_SECRET_KEY


class CreateOrderRequest(BaseModel):
    package_id: str


class VerifyPaymentRequest(BaseModel):
    payment_intent_id: str
    payment_method_id: Optional[str] = None


class PaymentService:
    @staticmethod
    def get_packages():
        """Get available credit packages"""
        return CREDIT_PACKAGES

    @staticmethod
    async def create_order(user_id: str, data: CreateOrderRequest) -> dict:
        """Create Stripe payment intent for credit purchase"""
        package = next((p for p in CREDIT_PACKAGES if p["id"] == data.package_id), None)
        if not package:
            raise HTTPException(status_code=400, detail="Invalid package")

        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        amount_cents = package["amount_inr"] * 100

        if STRIPE_SECRET_KEY:
            try:
                payment_intent = stripe.PaymentIntent.create(
                    amount=amount_cents,
                    currency="inr",
                    metadata={
                        "user_id": user_id,
                        "package_id": package["id"],
                        "credits": str(package["credits"])
                    }
                )
                intent_id = payment_intent.id
                client_secret = payment_intent.client_secret
            except Exception as e:
                logger.error(f"Stripe payment intent creation error: {e}")
                intent_id = f"pi_mock_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                client_secret = f"mock_secret_{intent_id}"
        else:
            intent_id = f"pi_mock_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            client_secret = f"mock_secret_{intent_id}"

        payment = TBPayment(
            user_id=user_id,
            amount_inr=package["amount_inr"],
            credits_purchased=package["credits"],
            provider=PaymentProvider.STRIPE,
            provider_order_id=intent_id,
            status=PaymentStatus.PENDING
        )
        await payment.insert()

        logger.info(f"Payment intent created: {intent_id} for user {user_id}")

        return {
            "payment_intent_id": intent_id,
            "client_secret": client_secret,
            "amount": amount_cents,
            "currency": "inr",
            "credits": package["credits"],
            "payment_id": str(payment.id)
        }

    @staticmethod
    async def verify_payment(user_id: str, data: VerifyPaymentRequest) -> dict:
        """
        Check Stripe payment status.
        NOTE: Credits are ONLY added via Stripe webhook, NOT here.
        This endpoint only returns the current status.
        """
        payment = await TBPayment.find_one(
            {"provider_order_id": data.payment_intent_id, "user_id": user_id}
        )

        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment.status == PaymentStatus.COMPLETED:
            user = await TBUser.get(user_id)
            return {
                "status": "completed",
                "credits_added": payment.credits_purchased,
                "current_balance": user.credits_balance if user else 0,
                "message": "Payment completed and credits added"
            }

        is_mock_order = data.payment_intent_id.startswith("pi_mock_")
        
        if STRIPE_SECRET_KEY and not is_mock_order:
            try:
                intent = stripe.PaymentIntent.retrieve(data.payment_intent_id)
                
                if intent.status == "succeeded":
                    return {
                        "status": "pending_fulfillment",
                        "message": "Payment successful. Credits will be added shortly via webhook."
                    }
                elif intent.status in ["processing", "requires_action"]:
                    return {
                        "status": "processing",
                        "message": f"Payment is {intent.status}"
                    }
                elif intent.status in ["requires_payment_method", "canceled"]:
                    payment.status = PaymentStatus.FAILED
                    payment.error_message = f"Payment {intent.status}"
                    await payment.save()
                    return {
                        "status": "failed",
                        "message": f"Payment {intent.status}"
                    }
                else:
                    return {
                        "status": intent.status,
                        "message": f"Payment status: {intent.status}"
                    }
            except stripe.error.StripeError as e:
                logger.error(f"Stripe verification error: {e}")
                return {
                    "status": "error",
                    "message": "Unable to verify payment status"
                }
        else:
            return {
                "status": "pending",
                "message": "Payment pending. Use Stripe webhook for production credit fulfillment."
            }

    @staticmethod
    async def fulfill_payment_via_webhook(payment_intent_id: str) -> dict:
        """
        Fulfill payment - ONLY called from webhook handler.
        This is the ONLY place credits are added.
        """
        from backend.services.tb_credit_service import CreditService
        from backend.models.tb_credit import TransactionReason
        
        payment = await TBPayment.find_one({"provider_order_id": payment_intent_id})
        
        if not payment:
            logger.error(f"Payment not found for intent: {payment_intent_id}")
            return {"success": False, "error": "Payment not found"}
        
        if payment.status == PaymentStatus.COMPLETED:
            logger.info(f"Payment already fulfilled: {payment_intent_id}")
            return {"success": True, "already_processed": True}
        
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.now(timezone.utc)
        await payment.save()
        
        await CreditService.add_credits(
            user_id=payment.user_id,
            amount=payment.credits_purchased,
            reason=TransactionReason.CREDIT_PURCHASE,
            reference_id=str(payment.id),
            description=f"Purchased {payment.credits_purchased} credits"
        )
        
        logger.info(
            f"Credits fulfilled via webhook: {payment.credits_purchased} credits for user {payment.user_id}",
            extra={
                "payment_intent_id": payment_intent_id,
                "user_id": payment.user_id,
                "credits": payment.credits_purchased
            }
        )
        
        return {
            "success": True,
            "credits_added": payment.credits_purchased,
            "user_id": payment.user_id
        }

    @staticmethod
    async def get_payment_history(user_id: str, limit: int = 50) -> list:
        """Get user's payment history"""
        payments = await TBPayment.find(
            {"user_id": user_id}
        ).sort(-TBPayment.created_at).limit(limit).to_list()

        return [
            {
                "id": str(p.id),
                "amount_inr": p.amount_inr,
                "credits_purchased": p.credits_purchased,
                "status": p.status,
                "provider": p.provider,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None
            }
            for p in payments
        ]
