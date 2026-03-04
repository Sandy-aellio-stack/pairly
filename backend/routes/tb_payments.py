from fastapi import APIRouter, Depends
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_payment_service import (
    PaymentService, CreateOrderRequest, VerifyPaymentRequest
)

router = APIRouter(tags=["TrueBond Payments"])


@router.get("/api/payments/packages")
async def get_packages():
    """Get available credit packages"""
    return {
        "packages": PaymentService.get_packages(),
        "currency": "INR",
        "min_purchase": 100
    }


@router.post("/api/payments/detect-provider")
async def detect_provider():
    """Detect available payment provider based on region/config"""
    return await PaymentService.detect_provider()


@router.post("/api/payments/checkout")
async def checkout(data: CreateOrderRequest, user: TBUser = Depends(get_current_user)):
    """Unified checkout endpoint for creating orders"""
    return await PaymentService.create_order(
        user_id=str(user.id),
        data=data
    )


@router.post("/api/payments/order")
async def create_order(data: CreateOrderRequest, user: TBUser = Depends(get_current_user)):
    """
    Create a Stripe payment intent for credit purchase.
    Returns payment_intent_id and client_secret for Stripe Elements.
    Note: Credits are ONLY added via webhook, not this endpoint.
    """
    return await PaymentService.create_order(
        user_id=str(user.id),
        data=data
    )


@router.post("/api/payments/verify")
async def verify_payment(data: VerifyPaymentRequest, user: TBUser = Depends(get_current_user)):
    """
    Verify Stripe payment status.
    Note: This only checks status - credits are added via webhook only.
    """
    return await PaymentService.verify_payment(
        user_id=str(user.id),
        data=data
    )


@router.get("/api/payments/history")
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
