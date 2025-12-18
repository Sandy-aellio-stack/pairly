from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from beanie import PydanticObjectId

from backend.models.tb_user import TBUser
from backend.models.tb_credit import TBCreditTransaction, TransactionReason


class CreditService:
    @staticmethod
    async def get_balance(user_id: str) -> int:
        """Get user's current credit balance"""
        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.credits_balance

    @staticmethod
    async def deduct_credits(
        user_id: str,
        amount: int,
        reason: TransactionReason,
        reference_id: str = None,
        description: str = None
    ) -> TBCreditTransaction:
        """Atomically deduct credits from user"""
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.credits_balance < amount:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Balance: {user.credits_balance}, Required: {amount}"
            )

        # Atomic update
        new_balance = user.credits_balance - amount
        user.credits_balance = new_balance
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

        # Log transaction
        transaction = TBCreditTransaction(
            user_id=user_id,
            amount=-amount,
            reason=reason,
            balance_after=new_balance,
            reference_id=reference_id,
            description=description
        )
        await transaction.insert()

        return transaction

    @staticmethod
    async def add_credits(
        user_id: str,
        amount: int,
        reason: TransactionReason,
        reference_id: str = None,
        description: str = None
    ) -> TBCreditTransaction:
        """Add credits to user"""
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Atomic update
        new_balance = user.credits_balance + amount
        user.credits_balance = new_balance
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

        # Log transaction
        transaction = TBCreditTransaction(
            user_id=user_id,
            amount=amount,
            reason=reason,
            balance_after=new_balance,
            reference_id=reference_id,
            description=description
        )
        await transaction.insert()

        return transaction

    @staticmethod
    async def get_transaction_history(
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> list:
        """Get user's credit transaction history"""
        transactions = await TBCreditTransaction.find(
            TBCreditTransaction.user_id == user_id
        ).sort(-TBCreditTransaction.created_at).skip(skip).limit(limit).to_list()

        return [
            {
                "id": str(t.id),
                "amount": t.amount,
                "reason": t.reason,
                "balance_after": t.balance_after,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]

    # Credit costs
    MESSAGE_COST = 1  # 1 coin per message
    AUDIO_CALL_COST_PER_MIN = 5  # 5 coins per minute voice call
    VIDEO_CALL_COST_PER_MIN = 10  # 10 coins per minute video call

    @staticmethod
    async def can_send_message(user_id: str) -> bool:
        """Check if user has enough credits to send a message (1 coin)"""
        balance = await CreditService.get_balance(user_id)
        return balance >= CreditService.MESSAGE_COST

    @staticmethod
    async def can_start_audio_call(user_id: str, minutes: int = 1) -> bool:
        """Check if user has enough credits for audio call (5 coins per minute)"""
        balance = await CreditService.get_balance(user_id)
        return balance >= (CreditService.AUDIO_CALL_COST_PER_MIN * minutes)

    @staticmethod
    async def can_start_video_call(user_id: str, minutes: int = 1) -> bool:
        """Check if user has enough credits for video call (10 coins per minute)"""
        balance = await CreditService.get_balance(user_id)
        return balance >= (CreditService.VIDEO_CALL_COST_PER_MIN * minutes)

    @staticmethod
    def get_pricing() -> dict:
        """Get current pricing structure"""
        return {
            "message_cost": CreditService.MESSAGE_COST,
            "audio_call_cost_per_min": CreditService.AUDIO_CALL_COST_PER_MIN,
            "video_call_cost_per_min": CreditService.VIDEO_CALL_COST_PER_MIN
        }
