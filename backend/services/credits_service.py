import logging
from datetime import datetime, timezone
from typing import Optional
from backend.models.user import User
from backend.models.credits_transaction import CreditsTransaction
from backend.models.profile import Profile
from beanie import PydanticObjectId

logger = logging.getLogger('service.credits')


# Custom exceptions
class InsufficientCreditsError(Exception):
    """Raised when user has insufficient credits"""
    pass


class DuplicateTransactionError(Exception):
    """Raised when a duplicate transaction is detected"""
    pass


class CreditsService:
    """Centralized credits management service"""
    
    @staticmethod
    async def add_credits(
        user_id: PydanticObjectId,
        amount: int,
        description: str,
        transaction_type: str = "purchase",
        metadata: Optional[dict] = None
    ) -> bool:
        """Add credits to user account with transaction logging"""
        try:
            user = await User.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Update balance
            old_balance = user.credits_balance
            user.credits_balance += amount
            await user.save()
            
            # Log transaction
            transaction = CreditsTransaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                balance_after=user.credits_balance,
                description=description,
                metadata=metadata or {},
                created_at=datetime.now(timezone.utc)
            )
            await transaction.insert()
            
            logger.info(
                f"Credits added",
                extra={
                    "event": "credits_added",
                    "user_id": str(user_id),
                    "amount": amount,
                    "old_balance": old_balance,
                    "new_balance": user.credits_balance,
                    "transaction_type": transaction_type
                }
            )
            
            return True
        except Exception as e:
            logger.error(f"Error adding credits: {e}", exc_info=True)
            return False
    
    @staticmethod
    async def deduct_credits(
        user_id: PydanticObjectId,
        amount: int,
        description: str,
        transaction_type: str = "spend",
        metadata: Optional[dict] = None
    ) -> bool:
        """Deduct credits from user account with transaction logging"""
        try:
            user = await User.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Check sufficient balance
            if user.credits_balance < amount:
                logger.warning(
                    "Insufficient credits",
                    extra={
                        "event": "insufficient_credits",
                        "user_id": str(user_id),
                        "required": amount,
                        "available": user.credits_balance
                    }
                )
                return False
            
            # Update balance
            old_balance = user.credits_balance
            user.credits_balance -= amount
            await user.save()
            
            # Log transaction
            transaction = CreditsTransaction(
                user_id=user_id,
                amount=-amount,
                transaction_type=transaction_type,
                balance_after=user.credits_balance,
                description=description,
                metadata=metadata or {},
                created_at=datetime.now(timezone.utc)
            )
            await transaction.insert()
            
            logger.info(
                "Credits deducted",
                extra={
                    "event": "credits_deducted",
                    "user_id": str(user_id),
                    "amount": amount,
                    "old_balance": old_balance,
                    "new_balance": user.credits_balance,
                    "transaction_type": transaction_type
                }
            )
            
            return True
        except Exception as e:
            logger.error(f"Error deducting credits: {e}", exc_info=True)
            return False
    
    @staticmethod
    async def transfer_credits(
        from_user_id: PydanticObjectId,
        to_user_id: PydanticObjectId,
        amount: int,
        description: str
    ) -> bool:
        """Transfer credits between users"""
        # Deduct from sender
        success = await CreditsService.deduct_credits(
            from_user_id,
            amount,
            f"Transfer to {to_user_id}: {description}",
            "transfer_out",
            {"to_user_id": str(to_user_id)}
        )
        
        if not success:
            return False
        
        # Add to recipient
        success = await CreditsService.add_credits(
            to_user_id,
            amount,
            f"Transfer from {from_user_id}: {description}",
            "transfer_in",
            {"from_user_id": str(from_user_id)}
        )
        
        if not success:
            # Rollback - add back to sender
            await CreditsService.add_credits(
                from_user_id,
                amount,
                "Transfer rollback",
                "refund"
            )
            return False
        
        return True
    
    @staticmethod
    async def charge_for_message(
        sender_id: PydanticObjectId,
        recipient_id: PydanticObjectId
    ) -> bool:
        """Charge credits for sending a message"""
        # Get recipient's profile to check pricing
        recipient_profile = await Profile.find_one(Profile.user_id == recipient_id)
        
        if not recipient_profile or recipient_profile.price_per_message == 0:
            return True  # Free message
        
        price = recipient_profile.price_per_message
        
        # Deduct from sender
        success = await CreditsService.deduct_credits(
            sender_id,
            price,
            f"Message to {recipient_id}",
            "message",
            {"recipient_id": str(recipient_id)}
        )
        
        if not success:
            return False
        
        # Add to recipient
        await CreditsService.add_credits(
            recipient_id,
            price,
            f"Message earnings from {sender_id}",
            "message_earnings",
            {"sender_id": str(sender_id)}
        )
        
        return True
    
    @staticmethod
    async def get_balance(user_id: PydanticObjectId) -> int:
        """Get user's credit balance"""
        user = await User.get(user_id)
        return user.credits_balance if user else 0
    
    @staticmethod
    async def get_transactions(user_id: PydanticObjectId, limit: int = 50):
        """Get user's transaction history"""
        transactions = await CreditsTransaction.find(
            CreditsTransaction.user_id == user_id
        ).sort("-created_at").limit(limit).to_list()
        
        return transactions
