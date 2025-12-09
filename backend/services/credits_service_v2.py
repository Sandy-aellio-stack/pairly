import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.models.user import User
from backend.models.credits_transaction import CreditsTransaction
from beanie import PydanticObjectId

logger = logging.getLogger('service.credits_v2')


class CreditsServiceV2:
    """
    Enhanced Credits Service with mock-safe ACID compatibility.
    
    Features:
    - Idempotency support
    - Transaction simulation (for non-replica-set MongoDB)
    - Audit logging
    - Rollback support
    """
    
    def __init__(self):
        self.transactions_enabled = False  # Set to True when MongoDB replica set is available
    
    async def add_credits(
        self,
        user_id: str,
        amount: int,
        description: str,
        transaction_type: str = "purchase",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """
        Add credits to user account with idempotency.
        
        Args:
            user_id: User ID
            amount: Credits to add (positive integer)
            description: Transaction description
            transaction_type: Type of transaction
            metadata: Additional metadata
            idempotency_key: Key to prevent duplicate operations
        
        Returns:
            Transaction ID
        
        Raises:
            ValueError: If user not found or invalid amount
        """
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        
        # Check idempotency
        if idempotency_key:
            existing_transaction = await CreditsTransaction.find_one(
                CreditsTransaction.metadata.get('idempotency_key') == idempotency_key
            )
            if existing_transaction:
                logger.info(
                    f"Duplicate credits add request detected",
                    extra={
                        "idempotency_key": idempotency_key,
                        "existing_transaction_id": str(existing_transaction.id)
                    }
                )
                return str(existing_transaction.id)
        
        # Get user
        user = await User.find_one(User.id == user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Simulate transaction context
        try:
            # Update balance
            old_balance = user.credits_balance
            user.credits_balance += amount
            await user.save()
            
            # Create transaction record
            transaction_metadata = metadata or {}
            if idempotency_key:
                transaction_metadata['idempotency_key'] = idempotency_key
            
            transaction = CreditsTransaction(
                user_id=PydanticObjectId(user_id),
                amount=amount,
                transaction_type=transaction_type,
                balance_after=user.credits_balance,
                description=description,
                metadata=transaction_metadata,
                created_at=datetime.now(timezone.utc)
            )
            await transaction.insert()
            
            logger.info(
                "Credits added successfully",
                extra={
                    "event": "credits_added_v2",
                    "user_id": user_id,
                    "amount": amount,
                    "old_balance": old_balance,
                    "new_balance": user.credits_balance,
                    "transaction_type": transaction_type,
                    "transaction_id": str(transaction.id),
                    "idempotency_key": idempotency_key
                }
            )
            
            return str(transaction.id)
        
        except Exception as e:
            logger.error(
                f"Error adding credits: {e}",
                extra={
                    "user_id": user_id,
                    "amount": amount
                },
                exc_info=True
            )
            
            # In a real transaction, this would rollback automatically
            # For now, we'll attempt manual rollback
            try:
                user = await User.find_one(User.id == user_id)
                if user:
                    user.credits_balance -= amount
                    await user.save()
                    logger.info(f"Rolled back credits add for user {user_id}")
            except:
                logger.error(f"Failed to rollback credits for user {user_id}")
            
            raise
    
    async def deduct_credits(
        self,
        user_id: str,
        amount: int,
        description: str,
        transaction_type: str = "spend",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """
        Deduct credits from user account with idempotency.
        
        Args:
            user_id: User ID
            amount: Credits to deduct (positive integer)
            description: Transaction description
            transaction_type: Type of transaction
            metadata: Additional metadata
            idempotency_key: Key to prevent duplicate operations
        
        Returns:
            Transaction ID
        
        Raises:
            ValueError: If user not found, invalid amount, or insufficient balance
        """
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        
        # Check idempotency
        if idempotency_key:
            existing_transaction = await CreditsTransaction.find_one(
                CreditsTransaction.metadata.get('idempotency_key') == idempotency_key
            )
            if existing_transaction:
                logger.info(
                    f"Duplicate credits deduct request detected",
                    extra={
                        "idempotency_key": idempotency_key,
                        "existing_transaction_id": str(existing_transaction.id)
                    }
                )
                return str(existing_transaction.id)
        
        # Get user
        user = await User.find_one(User.id == user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Check sufficient balance
        if user.credits_balance < amount:
            raise ValueError(
                f"Insufficient credits. Required: {amount}, Available: {user.credits_balance}"
            )
        
        # Simulate transaction context
        try:
            # Update balance
            old_balance = user.credits_balance
            user.credits_balance -= amount
            await user.save()
            
            # Create transaction record
            transaction_metadata = metadata or {}
            if idempotency_key:
                transaction_metadata['idempotency_key'] = idempotency_key
            
            transaction = CreditsTransaction(
                user_id=PydanticObjectId(user_id),
                amount=-amount,  # Negative for deduction
                transaction_type=transaction_type,
                balance_after=user.credits_balance,
                description=description,
                metadata=transaction_metadata,
                created_at=datetime.now(timezone.utc)
            )
            await transaction.insert()
            
            logger.info(
                "Credits deducted successfully",
                extra={
                    "event": "credits_deducted_v2",
                    "user_id": user_id,
                    "amount": amount,
                    "old_balance": old_balance,
                    "new_balance": user.credits_balance,
                    "transaction_type": transaction_type,
                    "transaction_id": str(transaction.id),
                    "idempotency_key": idempotency_key
                }
            )
            
            return str(transaction.id)
        
        except Exception as e:
            logger.error(
                f"Error deducting credits: {e}",
                extra={
                    "user_id": user_id,
                    "amount": amount
                },
                exc_info=True
            )
            
            # Attempt rollback
            try:
                user = await User.find_one(User.id == user_id)
                if user:
                    user.credits_balance += amount
                    await user.save()
                    logger.info(f"Rolled back credits deduction for user {user_id}")
            except:
                logger.error(f"Failed to rollback credits for user {user_id}")
            
            raise
    
    async def get_balance(self, user_id: str) -> int:
        """Get user's current credit balance"""
        user = await User.find_one(User.id == user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        return user.credits_balance
    
    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 50,
        transaction_type: Optional[str] = None
    ) -> list:
        """Get user's transaction history"""
        query = CreditsTransaction.user_id == PydanticObjectId(user_id)
        
        if transaction_type:
            query = query & (CreditsTransaction.transaction_type == transaction_type)
        
        transactions = await CreditsTransaction.find(query).sort("-created_at").limit(limit).to_list()
        
        return transactions
