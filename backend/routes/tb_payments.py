from fastapi import APIRouter, Depends, Request
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_payment_service import (
    PaymentService, CreateOrderRequest, VerifyPaymentRequest
)

router = APIRouter(prefix="/api/payments", tags=["TrueBond Payments"])


@router.get("/packages")
async def get_packages():
    """Get available credit packages"""
    return {
        "packages": PaymentService.get_packages(),
        "currency": "INR",
        "min_purchase": 100
    }


@router.post("/order")
async def create_order(data: CreateOrderRequest, user: TBUser = Depends(get_current_user)):
    """
    Create a Razorpay order for credit purchase.
    Returns order_id and key_id to initiate payment on frontend.
    """
    return await PaymentService.create_order(
        user_id=str(user.id),
        data=data
    )


@router.post("/verify")
async def verify_payment(data: VerifyPaymentRequest, user: TBUser = Depends(get_current_user)):
    """
    Verify Razorpay payment signature and credit wallet.
    Call this after successful Razorpay checkout.
    """
    return await PaymentService.verify_payment(
        user_id=str(user.id),
        data=data
    )


@router.get("/history")
async def get_payment_history(limit: int = 50, user: TBUser = Depends(get_current_user)):
    """Get user's payment history"""
    payments = await PaymentService.get_payment_history(
        user_id=str(user.id),
        limit=limit
    )
    return {
        "payments": payments,
        "count": len(payments)
    }


@router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    """
    Razorpay webhook handler.
    Handles payment.captured, payment.failed events.
    """
    # TODO: Implement webhook signature verification
    payload = await request.json()
    event = payload.get("event")
    
    if event == "payment.captured":
        # Payment successful - already handled in verify endpoint
        pass
    elif event == "payment.failed":
        # Mark payment as failed
        pass
    
    return {"status": "ok"}
