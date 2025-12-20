import razorpay
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel

from backend.models.tb_user import TBUser
from backend.models.tb_payment import TBPayment, PaymentStatus, PaymentProvider, CREDIT_PACKAGES
from backend.models.tb_credit import TransactionReason
from backend.services.tb_credit_service import CreditService

# Razorpay configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_yourtestkey")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "yourtestsecret")

# Initialize Razorpay client
try:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception as e:
    print(f"Razorpay client initialization error: {e}")
    razorpay_client = None


class CreateOrderRequest(BaseModel):
    package_id: str  # pack_100, pack_250, etc.


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentService:
    @staticmethod
    def get_packages():
        """Get available credit packages"""
        return CREDIT_PACKAGES

    @staticmethod
    async def create_order(user_id: str, data: CreateOrderRequest) -> dict:
        """Create Razorpay order for credit purchase"""
        # Find package
        package = next((p for p in CREDIT_PACKAGES if p["id"] == data.package_id), None)
        if not package:
            raise HTTPException(status_code=400, detail="Invalid package")

        if package["amount_inr"] < 100:
            raise HTTPException(status_code=400, detail="Minimum purchase amount is ₹100")

        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create Razorpay order
        if razorpay_client:
            try:
                order_data = {
                    "amount": package["amount_inr"] * 100,  # Amount in paise
                    "currency": "INR",
                    "receipt": f"tb_{user_id[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "notes": {
                        "user_id": user_id,
                        "package_id": package["id"],
                        "credits": package["credits"]
                    }
                }
                razorpay_order = razorpay_client.order.create(data=order_data)
                order_id = razorpay_order["id"]
            except Exception as e:
                print(f"Razorpay order creation error: {e}")
                # For development, create mock order
                order_id = f"order_mock_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        else:
            # Mock order for development
            order_id = f"order_mock_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Save payment record
        payment = TBPayment(
            user_id=user_id,
            amount_inr=package["amount_inr"],
            credits_purchased=package["credits"],
            provider=PaymentProvider.RAZORPAY,
            provider_order_id=order_id,
            status=PaymentStatus.PENDING
        )
        await payment.insert()

        return {
            "order_id": order_id,
            "amount": package["amount_inr"] * 100,  # In paise
            "currency": "INR",
            "credits": package["credits"],
            "key_id": RAZORPAY_KEY_ID,
            "payment_id": str(payment.id)
        }

    @staticmethod
    async def verify_payment(user_id: str, data: VerifyPaymentRequest) -> dict:
        """Verify Razorpay payment and credit wallet"""
        # Find payment record
        payment = await TBPayment.find_one(
            TBPayment.provider_order_id == data.razorpay_order_id,
            TBPayment.user_id == user_id
        )

        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment.status == PaymentStatus.COMPLETED:
            return {
                "status": "already_processed",
                "credits_added": payment.credits_purchased
            }

        # Skip verification for mock/demo orders
        is_mock_order = data.razorpay_order_id.startswith("order_mock_")
        
        # Verify signature with Razorpay (only for real orders)
        if razorpay_client and not is_mock_order:
            try:
                razorpay_client.utility.verify_payment_signature({
                    "razorpay_order_id": data.razorpay_order_id,
                    "razorpay_payment_id": data.razorpay_payment_id,
                    "razorpay_signature": data.razorpay_signature
                })
            except razorpay.errors.SignatureVerificationError:
                payment.status = PaymentStatus.FAILED
                payment.error_message = "Signature verification failed"
                await payment.save()
                raise HTTPException(status_code=400, detail="Payment verification failed")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Verification error: {str(e)}")

        # Update payment record
        payment.provider_payment_id = data.razorpay_payment_id
        payment.provider_signature = data.razorpay_signature
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.now(timezone.utc)
        await payment.save()

        # Add credits to user
        await CreditService.add_credits(
            user_id=user_id,
            amount=payment.credits_purchased,
            reason=TransactionReason.CREDIT_PURCHASE,
            reference_id=str(payment.id),
            description=f"Purchased {payment.credits_purchased} credits for ₹{payment.amount_inr}"
        )

        # Get updated balance
        user = await TBUser.get(user_id)

        return {
            "status": "success",
            "credits_added": payment.credits_purchased,
            "new_balance": user.credits_balance,
            "payment_id": data.razorpay_payment_id
        }

    @staticmethod
    async def get_payment_history(user_id: str, limit: int = 50) -> list:
        """Get user's payment history"""
        payments = await TBPayment.find(
            TBPayment.user_id == user_id
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
