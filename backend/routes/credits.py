from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from beanie import PydanticObjectId
from backend.models.user import User
from backend.models.credits_transaction import CreditsTransaction, TransactionType
from backend.routes.profiles import get_current_user
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime

router = APIRouter(prefix="/api/credits")


@router.get("/balance")
async def get_balance(user: User = Depends(get_current_user)):
    return {"credits_balance": user.credits_balance}


@router.get("/transactions")
async def get_transactions(
    limit: int = Query(50),
    offset: int = Query(0),
    user: User = Depends(get_current_user)
):
    txs = (
        await CreditsTransaction.find(CreditsTransaction.user_id == user.id)
        .sort("-created_at")
        .skip(offset)
        .limit(limit)
        .to_list()
    )
    return [tx.dict(by_alias=True) for tx in txs]


class ApplyCreditRequest(BaseModel):
    user_id: str
    delta: int
    idempotency_key: str
    reason: Optional[str] = None


@router.post("/apply")
async def apply_credit(req: ApplyCreditRequest):

    if req.delta == 0:
        raise HTTPException(400, "delta cannot be zero")

    existing = await CreditsTransaction.find_one(
        CreditsTransaction.reference_id == req.idempotency_key
    )
    if existing:
        return existing.dict(by_alias=True)

    user_oid = PydanticObjectId(req.user_id)

    client: AsyncIOMotorClient = User.get_motor_client()
    async with await client.start_session() as session:
        async with session.start_transaction():
            user = await User.get(user_oid, session=session)
            if not user:
                raise HTTPException(404, "User not found")

            new_balance = user.credits_balance + req.delta
            if new_balance < 0:
                raise HTTPException(400, "Insufficient credits")

            user.credits_balance = new_balance
            await user.save(session=session)

            if req.delta > 0:
                tx_type = TransactionType.PURCHASE
            else:
                tx_type = TransactionType.MESSAGE

            tx = CreditsTransaction(
                user_id=user_oid,
                delta=req.delta,
                balance_after=new_balance,
                type=tx_type,
                reference_id=req.idempotency_key,
                created_at=datetime.utcnow()
            )
            await tx.insert(session=session)

            return tx.dict(by_alias=True)
