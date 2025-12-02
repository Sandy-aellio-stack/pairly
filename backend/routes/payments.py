from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel
from backend.models.user import User
from backend.routes.auth import get_current_user
from backend.services.audit import log_event
from backend.services.fingerprint import register_fingerprint
from backend.services.risk import score_action
import os

router = APIRouter(prefix="/api/payments")

CREDIT_PACKAGES = {
    "small": {"credits": 50, "amount": 5000},
    "medium": {"credits": 120, "amount": 10000},
    "large": {"credits": 300, "amount": 20000}
}


class CheckoutRequest(BaseModel):
    provider: str
    package_id: str


@router.post("/checkout")
async def checkout(req: CheckoutRequest, request: Request, user: User = Depends(get_current_user)):
    if req.package_id not in CREDIT_PACKAGES:
        raise HTTPException(400, "Invalid package_id")

    package = CREDIT_PACKAGES[req.package_id]
    
    client_ip = request.client.host if request.client else "unknown"
    
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
                "amount_cents": package["amount"],
                "package_id": req.package_id,
                "provider": req.provider
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
    except Exception as e:
        print(f"Risk scoring error: {e}")

    return {
        "provider": req.provider,
        "package_id": req.package_id,
        "amount": package["amount"],
        "credits": package["credits"],
        "message": "Payment processing mock - integrate Stripe/Razorpay SDKs for production"
    }


@router.post("/webhook/stripe")
async def stripe_webhook():
    return {"success": True}


@router.post("/webhook/razorpay")
async def razorpay_webhook():
    return {"success": True}