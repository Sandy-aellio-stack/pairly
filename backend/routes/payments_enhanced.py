from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, Field
from typing import Optional, Literal
from backend.models.user import User
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus
from backend.routes.auth import get_current_user
from backend.services.payments import get_payment_manager
from backend.services.audit import log_event
from backend.services.fingerprint import register_fingerprint
from backend.services.risk import score_action
import logging

logger = logging.getLogger('routes.payments_enhanced')

router = APIRouter(prefix="/api/payments")

# Credit packages configuration
CREDIT_PACKAGES = {
    "small": {"credits": 50, "amount_cents": 5000, "currency": "INR"},
    "medium": {"credits": 120, "amount_cents": 10000, "currency": "INR"},
    "large": {"credits": 300, "amount_cents": 20000, "currency": "INR"},
    "xlarge": {"credits": 600, "amount_cents": 35000, "currency": "INR"},
}


class CreatePaymentIntentRequest(BaseModel):
    """Request to create a payment intent"""
    provider: Literal["stripe", "razorpay"] = Field(..., description="Payment provider")
    package_id: str = Field(..., description="Credit package ID")


class PaymentIntentResponse(BaseModel):
    """Payment intent response"""
    id: str
    provider: str
    provider_intent_id: str
    client_secret: Optional[str] = None
    amount_cents: int
    currency: str
    credits_amount: int
    status: str
    mock_mode: bool = False


class SimulatePaymentRequest(BaseModel):
    """Request to simulate payment completion (mock mode only)"""
    payment_intent_id: str
    success: bool = True


@router.post("/intent/create", response_model=PaymentIntentResponse)
async def create_payment_intent(
    req: CreatePaymentIntentRequest,
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Create a payment intent.
    
    Steps:
    1. Validate package
    2. Run fraud checks
    3. Create payment intent via PaymentManager
    4. Return client secret for payment confirmation
    """
    # Validate package
    if req.package_id not in CREDIT_PACKAGES:
        raise HTTPException(400, f"Invalid package_id: {req.package_id}")
    
    package = CREDIT_PACKAGES[req.package_id]
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Fraud detection (Phase 8.6)
    fingerprint = None
    fraud_score = 0
    
    try:
        from backend.services.fraud_detection import get_fraud_service
        
        fraud_service = get_fraud_service()
        fraud_result = await fraud_service.calculate_score(
            user=user,
            amount_cents=package["amount_cents"],
            ip_address=client_ip,
            fingerprint_id=None
        )
        
        fraud_score = fraud_result["score"]
        
        if fraud_result["action"] == "block":
            logger.warning(
                f"Payment blocked by fraud detection",
                extra={
                    "user_id": str(user.id),
                    "fraud_score": fraud_score,
                    "reasons": fraud_result["reasons"]
                }
            )
            raise HTTPException(
                403,
                f"Transaction blocked due to fraud risk. Score: {fraud_score}"
            )
        
        if fraud_result["action"] == "verify":
            logger.warning(
                f"Payment requires verification",
                extra={
                    "user_id": str(user.id),
                    "fraud_score": fraud_score
                }
            )
            # Log but allow (in production, would trigger 2FA)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fraud scoring error: {e}", exc_info=True)
        # Continue with payment creation (fail open)
    
    # Create payment intent
    try:
        payment_manager = get_payment_manager(mock_mode=True)  # MOCK MODE enabled
        
        payment_intent = await payment_manager.create_payment_intent(
            user_id=str(user.id),
            user_email=user.email,
            provider=req.provider,
            amount_cents=package["amount_cents"],
            currency=package["currency"],
            credits_amount=package["credits"],
            metadata={
                "package_id": req.package_id,
                "client_ip": client_ip,
                "user_agent": user_agent
            },
            fingerprint_id=str(fingerprint.id) if fingerprint else None,
            risk_score=fraud_score
        )
        
        # Log event
        await log_event(
            actor_user_id=user.id,
            action="payment_intent_created",
            details={
                "payment_intent_id": payment_intent.id,
                "provider": req.provider,
                "amount_cents": package["amount_cents"],
                "credits_amount": package["credits"],
                "package_id": req.package_id
            }
        )
        
        return PaymentIntentResponse(
            id=payment_intent.id,
            provider=payment_intent.provider,
            provider_intent_id=payment_intent.provider_intent_id,
            client_secret=payment_intent.provider_client_secret,
            amount_cents=payment_intent.amount_cents,
            currency=payment_intent.currency,
            credits_amount=payment_intent.credits_amount,
            status=payment_intent.status,
            mock_mode=payment_manager.mock_mode
        )
    
    except Exception as e:
        logger.error(f"Payment intent creation failed: {e}", exc_info=True)
        raise HTTPException(500, f"Payment intent creation failed: {str(e)}")


@router.get("/intent/{payment_intent_id}")
async def get_payment_intent(
    payment_intent_id: str,
    user: User = Depends(get_current_user)
):
    """Get payment intent details"""
    payment_intent = await PaymentIntent.find_one(
        PaymentIntent.id == payment_intent_id,
        PaymentIntent.user_id == str(user.id)
    )
    
    if not payment_intent:
        raise HTTPException(404, "Payment intent not found")
    
    return payment_intent.to_dict()


@router.post("/intent/{payment_intent_id}/cancel")
async def cancel_payment_intent(
    payment_intent_id: str,
    user: User = Depends(get_current_user)
):
    """Cancel a payment intent"""
    payment_intent = await PaymentIntent.find_one(
        PaymentIntent.id == payment_intent_id,
        PaymentIntent.user_id == str(user.id)
    )
    
    if not payment_intent:
        raise HTTPException(404, "Payment intent not found")
    
    if payment_intent.status in [PaymentIntentStatus.SUCCEEDED, PaymentIntentStatus.FAILED]:
        raise HTTPException(400, f"Cannot cancel payment in status: {payment_intent.status}")
    
    payment_manager = get_payment_manager(mock_mode=True)
    success = await payment_manager.cancel_payment_intent(payment_intent_id)
    
    if not success:
        raise HTTPException(500, "Failed to cancel payment intent")
    
    return {"success": True, "status": "canceled"}


@router.get("/packages")
async def get_credit_packages():
    """Get available credit packages"""
    return {
        "packages": [
            {
                "id": package_id,
                "credits": details["credits"],
                "amount_cents": details["amount_cents"],
                "currency": details["currency"],
                "price_display": f"₹{details['amount_cents'] / 100:.2f}"
            }
            for package_id, details in CREDIT_PACKAGES.items()
        ]
    }


@router.get("/history")
async def get_payment_history(
    user: User = Depends(get_current_user),
    limit: int = 20
):
    """Get user's payment history"""
    payments = await PaymentIntent.find(
        PaymentIntent.user_id == str(user.id)
    ).sort("-created_at").limit(limit).to_list()
    
    return {
        "payments": [p.to_dict() for p in payments],
        "total": len(payments)
    }


# ============================================================================
# MOCK MODE TESTING ENDPOINTS (disabled in production)
# ============================================================================

@router.post("/simulate/payment", tags=["mock-testing"])
async def simulate_payment_completion(
    req: SimulatePaymentRequest,
    user: User = Depends(get_current_user)
):
    """
    Simulate payment completion (MOCK MODE ONLY).
    
    This endpoint allows testing the payment fulfillment flow without real payments.
    """
    payment_intent = await PaymentIntent.find_one(
        PaymentIntent.id == req.payment_intent_id,
        PaymentIntent.user_id == str(user.id)
    )
    
    if not payment_intent:
        raise HTTPException(404, "Payment intent not found")
    
    if payment_intent.status == PaymentIntentStatus.SUCCEEDED:
        return {"success": True, "message": "Payment already completed", "credits_added": True}
    
    # Simulate payment completion
    payment_manager = get_payment_manager(mock_mode=True)
    
    if req.success:
        # Fulfill payment (add credits)
        success = await payment_manager.fulfill_payment(payment_intent, simulate_success=True)
        
        if success:
            logger.info(
                "MOCK: Payment simulated successfully",
                extra={
                    "payment_intent_id": payment_intent.id,
                    "user_id": str(user.id),
                    "credits_added": payment_intent.credits_amount
                }
            )
            return {
                "success": True,
                "message": "Payment simulated successfully",
                "credits_added": payment_intent.credits_amount,
                "new_balance": (await User.get(user.id)).credits_balance
            }
        else:
            raise HTTPException(500, "Payment fulfillment failed")
    else:
        # Simulate failure
        payment_intent.mark_completed(success=False, reason="Simulated failure")
        await payment_intent.save()
        
        return {
            "success": False,
            "message": "Payment failure simulated",
            "status": "failed"
        }


# ============================================================================
# WEBHOOK ENDPOINTS (skeletons for Phase 3)
# ============================================================================

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint.
    
    Phase 8.3: Full webhook processing with signature verification.
    """
    from backend.services.webhooks import get_webhook_processor
    import os
    
    # Get signature header
    signature = request.headers.get("stripe-signature", "")
    
    if not signature:
        raise HTTPException(400, "Missing Stripe-Signature header")
    
    # Get raw body
    body = await request.body()
    
    # Get webhook secret (or use mock)
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock_stripe_secret")
    
    # Process webhook
    processor = get_webhook_processor(mock_mode=True)
    success, message, webhook_id = await processor.process_stripe_webhook(
        body, signature, webhook_secret
    )
    
    if success:
        logger.info(f"Stripe webhook processed: {webhook_id}")
        return {"received": True, "webhook_id": webhook_id}
    else:
        logger.error(f"Stripe webhook failed: {message}")
        # Return 200 to prevent retries for invalid signatures
        if "signature" in message.lower():
            raise HTTPException(401, message)
        return {"received": True, "error": message, "webhook_id": webhook_id}


@router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    """
    Razorpay webhook endpoint.
    
    Phase 8.3: Full webhook processing with signature verification.
    """
    from backend.services.webhooks import get_webhook_processor
    import os
    
    # Get signature header
    signature = request.headers.get("x-razorpay-signature", "")
    
    if not signature:
        raise HTTPException(400, "Missing X-Razorpay-Signature header")
    
    # Get raw body
    body = await request.body()
    
    # Get webhook secret (or use mock)
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "rzp_mock_webhook_secret")
    
    # Process webhook
    processor = get_webhook_processor(mock_mode=True)
    success, message, webhook_id = await processor.process_razorpay_webhook(
        body, signature, webhook_secret
    )
    
    if success:
        logger.info(f"Razorpay webhook processed: {webhook_id}")
        return {"received": True, "webhook_id": webhook_id}
    else:
        logger.error(f"Razorpay webhook failed: {message}")
        # Return 200 to prevent retries for invalid signatures
        if "signature" in message.lower():
            raise HTTPException(401, message)
        return {"received": True, "error": message, "webhook_id": webhook_id}
