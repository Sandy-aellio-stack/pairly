"""
Credit Routes - Purchase, spend, refund, and manage credits.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from beanie import PydanticObjectId
import os

from backend.models.user import User, Role
from backend.models.credits_transaction import TransactionType
from backend.routes.auth import get_current_user
from backend.services.credits_service import (
    CreditsService,
    InsufficientCreditsError,
    DuplicateTransactionError
)

router = APIRouter(prefix="/api/legacy/credits", tags=["Legacy Credits"])


# ===== User Endpoints =====

@router.get("/balance")
async def get_balance(user: User = Depends(get_current_user)):
    """Get current credit balance."""
    return {
        "user_id": str(user.id),
        "credits_balance": user.credits_balance
    }


@router.get("/history")
async def get_history(
    limit: int = 50,
    skip: int = 0,
    transaction_type: Optional[TransactionType] = None,
    user: User = Depends(get_current_user)
):
    """Get credit transaction history."""
    result = await CreditsService.get_transaction_history(
        user_id=user.id,
        limit=limit,
        skip=skip,
        transaction_type=transaction_type
    )
    
    return {
        "transactions": [
            {
                "id": str(tx.id),
                "amount": tx.amount,
                "transaction_type": tx.transaction_type,
                "status": tx.status,
                "balance_before": tx.balance_before,
                "balance_after": tx.balance_after,
                "description": tx.description,
                "related_user_id": str(tx.related_user_id) if tx.related_user_id else None,
                "created_at": tx.created_at.isoformat()
            }
            for tx in result["transactions"]
        ],
        "total": result["total"],
        "limit": result["limit"],
        "skip": result["skip"]
    }


# ===== Credit Packages =====

CREDIT_PACKAGES = {
    "starter": {
        "credits": 50,
        "price_usd": 4.99,
        "price_inr": 399,
        "bonus_credits": 0,
        "description": "Perfect for trying out"
    },
    "popular": {
        "credits": 120,
        "price_usd": 9.99,
        "price_inr": 799,
        "bonus_credits": 10,
        "description": "Most popular choice"
    },
    "premium": {
        "credits": 300,
        "price_usd": 19.99,
        "price_inr": 1599,
        "bonus_credits": 50,
        "description": "Best value"
    },
    "ultimate": {
        "credits": 1000,
        "price_usd": 49.99,
        "price_inr": 3999,
        "bonus_credits": 200,
        "description": "Ultimate package"
    }
}


@router.get("/packages")
async def get_packages():
    """Get available credit packages."""
    return {"packages": CREDIT_PACKAGES}


# ===== Purchase Flow =====

class PurchaseRequest(BaseModel):
    package_id: str
    payment_provider: str  # "stripe" or "razorpay"
    payment_method_id: Optional[str] = None  # For saved payment methods


@router.post("/purchase/initiate")
async def initiate_purchase(
    req: PurchaseRequest,
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Initiate credit purchase.
    
    Returns payment intent/order for frontend to complete.
    """
    if req.package_id not in CREDIT_PACKAGES:
        raise HTTPException(400, "Invalid package_id")
    
    package = CREDIT_PACKAGES[req.package_id]
    
    # Generate idempotency key
    import uuid
    idempotency_key = f"purchase_{user.id}_{uuid.uuid4()}"
    
    if req.payment_provider == "stripe":
        # Create Stripe Payment Intent
        try:
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            
            intent = stripe.PaymentIntent.create(
                amount=int(package["price_usd"] * 100),  # Convert to cents
                currency="usd",
                customer=str(user.id),  # You should create/link Stripe customer
                metadata={
                    "user_id": str(user.id),
                    "package_id": req.package_id,
                    "credits": package["credits"] + package["bonus_credits"],
                    "idempotency_key": idempotency_key
                },
                idempotency_key=idempotency_key
            )
            
            return {
                "provider": "stripe",
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": package["price_usd"],
                "currency": "USD",
                "credits": package["credits"] + package["bonus_credits"]
            }
        except ImportError:
            # Stripe not installed - return mock
            return {
                "provider": "stripe",
                "client_secret": f"mock_secret_{idempotency_key}",
                "payment_intent_id": f"pi_mock_{idempotency_key}",
                "amount": package["price_usd"],
                "currency": "USD",
                "credits": package["credits"] + package["bonus_credits"],
                "mock": True
            }
        except Exception as e:
            print(f"Stripe error: {e}")
            raise HTTPException(500, "Payment processing error")
    
    elif req.payment_provider == "razorpay":
        # Create Razorpay Order
        try:
            import razorpay
            client = razorpay.Client(
                auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
            )
            
            order = client.order.create({
                "amount": int(package["price_inr"] * 100),  # Convert to paise
                "currency": "INR",
                "receipt": idempotency_key,
                "notes": {
                    "user_id": str(user.id),
                    "package_id": req.package_id,
                    "credits": package["credits"] + package["bonus_credits"]
                }
            })
            
            return {
                "provider": "razorpay",
                "order_id": order["id"],
                "amount": package["price_inr"],
                "currency": "INR",
                "credits": package["credits"] + package["bonus_credits"]
            }
        except ImportError:
            # Razorpay not installed - return mock
            return {
                "provider": "razorpay",
                "order_id": f"order_mock_{idempotency_key}",
                "amount": package["price_inr"],
                "currency": "INR",
                "credits": package["credits"] + package["bonus_credits"],
                "mock": True
            }
        except Exception as e:
            print(f"Razorpay error: {e}")
            raise HTTPException(500, "Payment processing error")
    
    else:
        raise HTTPException(400, f"Unsupported payment provider: {req.payment_provider}")


class ConfirmPurchaseRequest(BaseModel):
    payment_id: str
    payment_provider: str
    package_id: str


@router.post("/purchase/confirm")
async def confirm_purchase(
    req: ConfirmPurchaseRequest,
    user: User = Depends(get_current_user)
):
    """
    Confirm purchase after payment completion.
    
    Note: In production, this should be called from webhook,
    not directly by user (to prevent fraud).
    """
    if req.package_id not in CREDIT_PACKAGES:
        raise HTTPException(400, "Invalid package_id")
    
    package = CREDIT_PACKAGES[req.package_id]
    credits_to_add = package["credits"] + package["bonus_credits"]
    
    try:
        tx = await CreditsService.add_credits(
            user_id=user.id,
            amount=credits_to_add,
            transaction_type=TransactionType.PURCHASE,
            description=f"Purchased {credits_to_add} credits ({req.package_id} package)",
            idempotency_key=req.payment_id,
            payment_provider=req.payment_provider,
            payment_id=req.payment_id,
            payment_amount_cents=int(package["price_usd"] * 100),
            payment_currency="USD",
            metadata={"package_id": req.package_id}
        )
        
        return {
            "success": True,
            "credits_added": credits_to_add,
            "new_balance": tx.balance_after,
            "transaction_id": str(tx.id)
        }
    
    except DuplicateTransactionError:
        # Payment already processed
        return {
            "success": True,
            "message": "Credits already added for this payment"
        }


# ===== Spending Credits =====

class SpendCreditsRequest(BaseModel):
    amount: int
    transaction_type: TransactionType
    description: str
    related_user_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    idempotency_key: Optional[str] = None


@router.post("/spend")
async def spend_credits(
    req: SpendCreditsRequest,
    user: User = Depends(get_current_user)
):
    """
    Spend credits (internal API for other services).
    
    Used by messaging, calling, tipping services.
    """
    try:
        related_user_oid = PydanticObjectId(req.related_user_id) if req.related_user_id else None
        
        tx = await CreditsService.spend_credits(
            user_id=user.id,
            amount=req.amount,
            transaction_type=req.transaction_type,
            description=req.description,
            idempotency_key=req.idempotency_key,
            related_user_id=related_user_oid,
            related_entity_type=req.related_entity_type,
            related_entity_id=req.related_entity_id
        )
        
        return {
            "success": True,
            "credits_spent": req.amount,
            "new_balance": tx.balance_after,
            "transaction_id": str(tx.id)
        }
    
    except InsufficientCreditsError as e:
        raise HTTPException(400, str(e))
    
    except DuplicateTransactionError:
        raise HTTPException(409, "Transaction already processed")


# ===== Tipping =====

class TipCreatorRequest(BaseModel):
    creator_id: str
    amount: int
    message: Optional[str] = None


@router.post("/tip")
async def tip_creator(
    req: TipCreatorRequest,
    user: User = Depends(get_current_user)
):
    """
    Tip a creator with credits.
    """
    if req.amount <= 0:
        raise HTTPException(400, "Tip amount must be positive")
    
    # Generate idempotency key
    import uuid
    idempotency_key = f"tip_{user.id}_{req.creator_id}_{uuid.uuid4()}"
    
    try:
        creator_oid = PydanticObjectId(req.creator_id)
        
        # Spend credits from tipper
        spend_tx = await CreditsService.spend_credits(
            user_id=user.id,
            amount=req.amount,
            transaction_type=TransactionType.TIP,
            description=f"Tipped {req.amount} credits to creator",
            idempotency_key=idempotency_key,
            related_user_id=creator_oid,
            related_entity_type="tip",
            metadata={"message": req.message}
        )
        
        # Add credits to creator (platform takes no cut for now)
        add_tx = await CreditsService.add_credits(
            user_id=creator_oid,
            amount=req.amount,
            transaction_type=TransactionType.BONUS,  # Tip received
            description=f"Received {req.amount} credits tip",
            idempotency_key=f"{idempotency_key}_creator",
            related_user_id=user.id,
            metadata={"tipper_id": str(user.id), "message": req.message}
        )
        
        return {
            "success": True,
            "amount": req.amount,
            "new_balance": spend_tx.balance_after,
            "creator_id": req.creator_id
        }
    
    except InsufficientCreditsError as e:
        raise HTTPException(400, str(e))
    
    except DuplicateTransactionError:
        raise HTTPException(409, "Tip already processed")


# ===== Admin Endpoints =====

class AdminAdjustCreditsRequest(BaseModel):
    user_id: str
    amount: int  # Positive to add, negative to deduct
    reason: str
    idempotency_key: Optional[str] = None


@router.post("/admin/adjust")
async def admin_adjust_credits(
    req: AdminAdjustCreditsRequest,
    admin: User = Depends(get_current_user)
):
    """
    Admin: Manually adjust user credits.
    
    Admin only. Used for:
    - Compensating users for issues
    - Applying penalties
    - Manual corrections
    """
    if admin.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    user_oid = PydanticObjectId(req.user_id)
    
    try:
        if req.amount > 0:
            # Add credits
            tx = await CreditsService.add_credits(
                user_id=user_oid,
                amount=req.amount,
                transaction_type=TransactionType.ADMIN_GRANT,
                description=f"Admin adjustment: {req.reason}",
                idempotency_key=req.idempotency_key,
                metadata={"admin_id": str(admin.id), "reason": req.reason}
            )
        else:
            # Deduct credits
            tx = await CreditsService.spend_credits(
                user_id=user_oid,
                amount=abs(req.amount),
                transaction_type=TransactionType.ADMIN_DEDUCT,
                description=f"Admin deduction: {req.reason}",
                idempotency_key=req.idempotency_key,
                metadata={"admin_id": str(admin.id), "reason": req.reason}
            )
        
        return {
            "success": True,
            "user_id": req.user_id,
            "amount_adjusted": req.amount,
            "new_balance": tx.balance_after,
            "transaction_id": str(tx.id)
        }
    
    except InsufficientCreditsError as e:
        raise HTTPException(400, str(e))
    
    except DuplicateTransactionError:
        raise HTTPException(409, "Adjustment already processed")


class AdminRefundRequest(BaseModel):
    transaction_id: str
    reason: str
    idempotency_key: Optional[str] = None


@router.post("/admin/refund")
async def admin_refund(
    req: AdminRefundRequest,
    admin: User = Depends(get_current_user)
):
    """
    Admin: Refund a transaction.
    
    Admin only. Reverses a previous transaction.
    """
    if admin.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    try:
        refund_tx = await CreditsService.refund_credits(
            original_transaction_id=req.transaction_id,
            reason=f"Admin refund: {req.reason}",
            idempotency_key=req.idempotency_key
        )
        
        return {
            "success": True,
            "original_transaction_id": req.transaction_id,
            "refund_amount": refund_tx.amount,
            "new_balance": refund_tx.balance_after,
            "refund_transaction_id": str(refund_tx.id)
        }
    
    except DuplicateTransactionError:
        raise HTTPException(409, "Refund already processed")
