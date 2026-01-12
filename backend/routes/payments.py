from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, Field
from typing import Optional
from backend.models.user import User
from backend.routes.auth import get_current_user
from backend.services.audit import log_event
from backend.services.fingerprint import register_fingerprint
from backend.services.risk import score_action
from backend.services.location_detector import get_location_detector
from backend.services.payments.manager import get_payment_manager
import os
import logging

logger = logging.getLogger('routes.payments')

router = APIRouter(prefix="/api/legacy/payments", tags=["Legacy Payments"])

CREDIT_PACKAGES = {
    "small": {"credits": 50, "amount_usd": 500, "amount_inr": 5000},
    "medium": {"credits": 120, "amount_usd": 1000, "amount_inr": 10000},
    "large": {"credits": 300, "amount_usd": 2000, "amount_inr": 20000}
}


class CheckoutRequest(BaseModel):
    package_id: str
    provider: Optional[str] = None
    country_code: Optional[str] = None


class CheckoutResponse(BaseModel):
    success: bool
    provider: str
    payment_intent_id: str
    client_secret: str
    amount_cents: int
    currency: str
    credits: int
    requires_action: bool = False
    provider_data: Optional[dict] = None


@router.get("/packages")
async def get_packages():
    """Get available credit packages"""
    return {
        "packages": CREDIT_PACKAGES,
        "supported_providers": ["stripe", "razorpay"],
        "provider_info": {
            "stripe": {
                "name": "Stripe",
                "currencies": ["USD", "EUR", "GBP"],
                "regions": "Global (excluding India)"
            },
            "razorpay": {
                "name": "Razorpay",
                "currencies": ["INR"],
                "regions": "India"
            }
        }
    }


@router.post("/detect-provider")
async def detect_provider(request: Request):
    """Detect recommended payment provider based on user location"""
    client_ip = request.client.host if request.client else None

    location_detector = get_location_detector()
    provider = await location_detector.get_payment_provider_for_user(
        ip_address=client_ip
    )

    currency = location_detector.get_currency_for_provider(provider)

    return {
        "provider": provider,
        "currency": currency,
        "detected_ip": client_ip
    }


@router.post("/checkout")
async def checkout(
    req: CheckoutRequest,
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Create payment intent with automatic provider selection.

    Provider selection logic:
    1. Manual provider (if specified)
    2. Country code (if provided)
    3. IP-based detection
    4. Default to Stripe
    """
    if req.package_id not in CREDIT_PACKAGES:
        raise HTTPException(400, "Invalid package_id")

    package = CREDIT_PACKAGES[req.package_id]
    client_ip = request.client.host if request.client else "unknown"

    location_detector = get_location_detector()
    provider = await location_detector.get_payment_provider_for_user(
        ip_address=client_ip,
        user_country=req.country_code,
        manual_provider=req.provider
    )

    currency = location_detector.get_currency_for_provider(provider)

    amount_cents = package["amount_inr"] if currency == "INR" else package["amount_usd"]

    logger.info(
        f"Checkout initiated",
        extra={
            "user_id": user.id,
            "package_id": req.package_id,
            "provider": provider,
            "currency": currency,
            "amount_cents": amount_cents,
            "client_ip": client_ip
        }
    )

    try:
        fingerprint = await register_fingerprint(
            request=request,
            user_id=user.id,
            ip=client_ip
        )

        risk_result = await score_action(
            action_type="purchase",
            fingerprint=fingerprint,
            user=user,
            metadata={
                "amount_cents": amount_cents,
                "package_id": req.package_id,
                "provider": provider
            }
        )

        if risk_result["action"] == "block":
            raise HTTPException(
                403,
                f"Transaction blocked due to fraud risk. Reasons: {', '.join(risk_result['reasons'])}"
            )

        if risk_result["action"] == "verify":
            return {
                "requires_verification": True,
                "message": "Additional verification required. Please complete 2FA or contact support.",
                "reasons": risk_result["reasons"],
                "score": risk_result["score"]
            }

        payment_manager = get_payment_manager(
            mock_mode=os.getenv('PAYMENTS_MOCK_MODE', 'true').lower() == 'true'
        )

        payment_intent = await payment_manager.create_payment_intent(
            user_id=user.id,
            user_email=user.email,
            provider=provider,
            amount_cents=amount_cents,
            currency=currency,
            credits_amount=package["credits"],
            metadata={
                "package_id": req.package_id,
                "client_ip": client_ip,
                "user_agent": request.headers.get('user-agent', 'unknown')
            },
            fingerprint_id=fingerprint.id if hasattr(fingerprint, 'id') else None,
            risk_score=risk_result.get('score')
        )

        logger.info(
            f"Payment intent created",
            extra={
                "payment_intent_id": payment_intent.id,
                "provider": provider,
                "user_id": user.id
            }
        )

        return CheckoutResponse(
            success=True,
            provider=provider,
            payment_intent_id=payment_intent.id,
            client_secret=payment_intent.provider_client_secret,
            amount_cents=amount_cents,
            currency=currency,
            credits=package["credits"],
            requires_action=payment_intent.provider_response.get('requires_action', False),
            provider_data=payment_intent.provider_response
        )

    except Exception as e:
        logger.error(f"Checkout error: {e}", exc_info=True)
        raise HTTPException(500, f"Checkout failed: {str(e)}")


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Process Stripe webhook"""
    from backend.services.webhooks.processor import get_webhook_processor
    from backend.config import settings

    if not stripe_signature:
        logger.warning("Stripe webhook missing signature header")
        raise HTTPException(400, "Missing Stripe-Signature header")

    try:
        payload = await request.body()

        webhook_processor = get_webhook_processor(
            mock_mode=settings.PAYMENTS_MOCK_MODE
        )

        success, message, webhook_event_id = await webhook_processor.process_stripe_webhook(
            payload=payload,
            signature_header=stripe_signature,
            webhook_secret=settings.STRIPE_WEBHOOK_SECRET
        )

        if success:
            logger.info(f"Stripe webhook processed: {webhook_event_id}")
            return {"success": True, "message": message, "webhook_event_id": webhook_event_id}
        else:
            logger.error(f"Stripe webhook processing failed: {message}")
            raise HTTPException(400, message)

    except Exception as e:
        logger.error(f"Stripe webhook error: {e}", exc_info=True)
        raise HTTPException(500, f"Webhook processing failed: {str(e)}")


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="x-razorpay-signature")
):
    """Process Razorpay webhook"""
    from backend.services.webhooks.processor import get_webhook_processor
    from backend.config import settings

    if not x_razorpay_signature:
        logger.warning("Razorpay webhook missing signature header")
        raise HTTPException(400, "Missing X-Razorpay-Signature header")

    try:
        payload = await request.body()

        webhook_processor = get_webhook_processor(
            mock_mode=settings.PAYMENTS_MOCK_MODE
        )

        success, message, webhook_event_id = await webhook_processor.process_razorpay_webhook(
            payload=payload,
            signature_header=x_razorpay_signature,
            webhook_secret=settings.RAZORPAY_WEBHOOK_SECRET
        )

        if success:
            logger.info(f"Razorpay webhook processed: {webhook_event_id}")
            return {"success": True, "message": message, "webhook_event_id": webhook_event_id}
        else:
            logger.error(f"Razorpay webhook processing failed: {message}")
            raise HTTPException(400, message)

    except Exception as e:
        logger.error(f"Razorpay webhook error: {e}", exc_info=True)
        raise HTTPException(500, f"Webhook processing failed: {str(e)}")