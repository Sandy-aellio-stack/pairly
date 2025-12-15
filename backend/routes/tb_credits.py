from fastapi import APIRouter, Depends
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_credit_service import CreditService

router = APIRouter(prefix="/api/credits", tags=["TrueBond Credits"])


@router.get("/balance")
async def get_balance(user: TBUser = Depends(get_current_user)):
    """Get current credit balance"""
    balance = await CreditService.get_balance(str(user.id))
    return {
        "credits_balance": balance
    }


@router.get("/history")
async def get_transaction_history(
    limit: int = 50,
    skip: int = 0,
    user: TBUser = Depends(get_current_user)
):
    """Get credit transaction history"""
    transactions = await CreditService.get_transaction_history(
        user_id=str(user.id),
        limit=limit,
        skip=skip
    )
    return {
        "transactions": transactions,
        "count": len(transactions)
    }
