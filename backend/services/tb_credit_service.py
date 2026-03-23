import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from beanie import PydanticObjectId

from backend.models.tb_user import TBUser
from backend.models.tb_credit import TBCreditTransaction, TransactionReason

logger = logging.getLogger("credits")

# Developer account with unlimited coins
UNLIMITED_COINS_USER_ID = "69a18167be16ddc2a28e19aa" # indiranigopi677@gmail.com

class CreditService:
    @staticmethod
    async def get_balance(user_id: str) -> int:
        """Get user's current coin balance"""
        if user_id == UNLIMITED_COINS_USER_ID:
            return 999999
            
        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.coins

    @staticmethod
    async def deduct_credits(
        user_id: str,
        amount: int,
        reason: TransactionReason,
        reference_id: str = None,
        description: str = None,
        session = None
    ) -> TBCreditTransaction:
        """Atomically deduct coins from user. Supports optional session for transactions."""
        if user_id == UNLIMITED_COINS_USER_ID:
            # Bypass deduction for developer account
            return TBCreditTransaction(
                user_id=user_id,
                amount=0,
                reason=reason,
                balance_after=999999,
                reference_id=reference_id,
                description=f"(DEV BYPASS) {description}"
            )
            
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        from backend.utils.objectid_utils import to_object_id
        user_oid = to_object_id(user_id)

        from pymongo import ReturnDocument

        # Atomic find-and-update using native PyMongo collection via Beanie
        result = await TBUser.get_motor_collection().find_one_and_update(
            {
                "_id": user_oid,
                "coins": {"$gte": amount}
            },
            {
                "$inc": {"coins": -amount},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            session=session,
            return_document=ReturnDocument.AFTER
        )

        if not result:
            user = await TBUser.get(user_id, session=session)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient coins. Balance: {user.coins}, Required: {amount}"
                )

        new_balance = result.get("coins", 0) if isinstance(result, dict) else result.coins

        # Log transaction
        transaction = TBCreditTransaction(
            user_id=user_id,
            amount=-amount,
            reason=reason,
            balance_after=new_balance,
            reference_id=reference_id,
            description=description
        )
        await transaction.insert(session=session)

        logger.info(
            f"Coins deducted: user={user_id}, amount={amount}, reason={reason.value if hasattr(reason,'value') else reason}, "
            f"balance_after={new_balance}, ref={reference_id}"
        )
        return transaction

    @staticmethod
    async def add_credits(
        user_id: str,
        amount: int,
        reason: TransactionReason,
        reference_id: str = None,
        description: str = None,
        session = None
    ) -> TBCreditTransaction:
        """Add coins to user. Supports optional session for transactions."""
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        from backend.utils.objectid_utils import to_object_id
        user_oid = to_object_id(user_id)

        from pymongo import ReturnDocument

        # Atomic update
        result = await TBUser.get_motor_collection().find_one_and_update(
            {"_id": user_oid},
            {
                "$inc": {"coins": amount},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            session=session,
            return_document=ReturnDocument.AFTER
        )

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        # Log transaction
        transaction = TBCreditTransaction(
            user_id=user_id,
            amount=amount,
            reason=reason,
            balance_after=result.get("coins", 0) if isinstance(result, dict) else result.coins,
            reference_id=reference_id,
            description=description
        )
        await transaction.insert(session=session)

        logger.info(
            f"Coins added: user={user_id}, amount={amount}, reason={reason.value if hasattr(reason,'value') else reason}, "
            f"balance_after={result.get('coins', 0) if isinstance(result, dict) else result.coins}, ref={reference_id}"
        )
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
