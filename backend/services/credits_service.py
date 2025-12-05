"""Credits Service - All credit operations with transaction safety."""

from typing import Optional, Dict, Any
from datetime import datetime
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException

from backend.models.user import User
from backend.models.credits_transaction import (
    CreditsTransaction,
    TransactionType,
    TransactionStatus
)


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits."""
    pass


class DuplicateTransactionError(Exception):
    """Raised when idempotency key already exists."""
    pass


class CreditsService:
    """Service for managing credit transactions with ACID guarantees."""
    
    @staticmethod
    async def add_credits(
        user_id: PydanticObjectId,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        idempotency_key: Optional[str] = None,
        payment_provider: Optional[str] = None,
        payment_id: Optional[str] = None,
        payment_amount_cents: Optional[int] = None,
        payment_currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CreditsTransaction:
        """
        Add credits to user account.
        
        Args:
            user_id: User ID
            amount: Number of credits to add (must be positive)
            transaction_type: Type of transaction
            description: Human-readable description
            idempotency_key: Optional key to prevent duplicate transactions
            payment_provider: Payment provider (stripe, razorpay)
            payment_id: Payment transaction ID from provider
            payment_amount_cents: Amount paid in cents
            payment_currency: Currency code (USD, INR)
            metadata: Additional metadata
        
        Returns:
            CreditsTransaction object
        
        Raises:
            DuplicateTransactionError: If idempotency_key already exists
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Check idempotency
        if idempotency_key:
            existing = await CreditsTransaction.find_one(
                CreditsTransaction.idempotency_key == idempotency_key
            )
            if existing:
                raise DuplicateTransactionError(f"Transaction with key {idempotency_key} already exists")
        
        # Use MongoDB transaction for atomicity
        client: AsyncIOMotorClient = User.get_motor_client()
        async with await client.start_session() as session:
            async with session.start_transaction():
                # Get user with lock
                user = await User.get(user_id, session=session)
                if not user:
                    raise HTTPException(404, "User not found")
                
                balance_before = user.credits_balance
                balance_after = balance_before + amount
                
                # Update user balance
                user.credits_balance = balance_after
                user.updated_at = datetime.utcnow()
                await user.save(session=session)
                
                # Create transaction record
                tx = CreditsTransaction(
                    user_id=user_id,
                    amount=amount,
                    transaction_type=transaction_type,
                    status=TransactionStatus.COMPLETED,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    description=description,
                    idempotency_key=idempotency_key,
                    payment_provider=payment_provider,
                    payment_id=payment_id,
                    payment_amount_cents=payment_amount_cents,
                    payment_currency=payment_currency,
                    metadata=metadata,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                await tx.insert(session=session)
                
                return tx
    
    @staticmethod
    async def spend_credits(
        user_id: PydanticObjectId,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        idempotency_key: Optional[str] = None,
        related_user_id: Optional[PydanticObjectId] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CreditsTransaction:
        """
        Spend credits from user account.
        
        Args:
            user_id: User ID
            amount: Number of credits to spend (must be positive)
            transaction_type: Type of transaction
            description: Human-readable description
            idempotency_key: Optional key to prevent duplicate transactions
            related_user_id: User receiving credits (e.g., creator)
            related_entity_type: Type of entity (message, post, call)
            related_entity_id: ID of related entity
            metadata: Additional metadata
        
        Returns:
            CreditsTransaction object
        
        Raises:
            InsufficientCreditsError: If user doesn't have enough credits
            DuplicateTransactionError: If idempotency_key already exists
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Check idempotency
        if idempotency_key:
            existing = await CreditsTransaction.find_one(
                CreditsTransaction.idempotency_key == idempotency_key
            )
            if existing:
                raise DuplicateTransactionError(f"Transaction with key {idempotency_key} already exists")
        
        # Use MongoDB transaction for atomicity
        client: AsyncIOMotorClient = User.get_motor_client()
        async with await client.start_session() as session:
            async with session.start_transaction():
                # Get user with lock
                user = await User.get(user_id, session=session)
                if not user:
                    raise HTTPException(404, "User not found")
                
                balance_before = user.credits_balance
                balance_after = balance_before - amount
                
                # Check sufficient balance
                if balance_after < 0:
                    raise InsufficientCreditsError(f"Insufficient credits. Required: {amount}, Available: {balance_before}")
                
                # Update user balance
                user.credits_balance = balance_after
                user.updated_at = datetime.utcnow()
                await user.save(session=session)
                
                # Create transaction record (negative amount)
                tx = CreditsTransaction(
                    user_id=user_id,
                    amount=-amount,  # Negative for spending
                    transaction_type=transaction_type,
                    status=TransactionStatus.COMPLETED,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    description=description,
                    idempotency_key=idempotency_key,
                    related_user_id=related_user_id,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                    metadata=metadata,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                await tx.insert(session=session)
                
                return tx
    
    @staticmethod
    async def refund_credits(
        original_transaction_id: str,
        reason: str,
        idempotency_key: Optional[str] = None
    ) -> CreditsTransaction:
        """
        Refund a previous transaction.
        
        Args:
            original_transaction_id: ID of transaction to refund
            reason: Reason for refund
            idempotency_key: Optional key to prevent duplicate refunds
        
        Returns:
            CreditsTransaction object (refund)
        
        Raises:
            HTTPException: If original transaction not found or already refunded
        """
        # Check idempotency
        if idempotency_key:
            existing = await CreditsTransaction.find_one(
                CreditsTransaction.idempotency_key == idempotency_key
            )
            if existing:
                raise DuplicateTransactionError(f"Refund with key {idempotency_key} already exists")
        
        # Get original transaction
        original_tx = await CreditsTransaction.get(original_transaction_id)
        if not original_tx:
            raise HTTPException(404, "Original transaction not found")
        
        if original_tx.status == TransactionStatus.REVERSED:
            raise HTTPException(400, "Transaction already refunded")
        
        # Calculate refund amount (reverse the original)
        refund_amount = -original_tx.amount
        
        # Use MongoDB transaction
        client: AsyncIOMotorClient = User.get_motor_client()
        async with await client.start_session() as session:
            async with session.start_transaction():
                # Get user with lock
                user = await User.get(original_tx.user_id, session=session)
                if not user:
                    raise HTTPException(404, "User not found")
                
                balance_before = user.credits_balance
                balance_after = balance_before + refund_amount
                
                # Update user balance
                user.credits_balance = balance_after
                user.updated_at = datetime.utcnow()
                await user.save(session=session)
                
                # Mark original transaction as reversed
                original_tx.status = TransactionStatus.REVERSED
                original_tx.updated_at = datetime.utcnow()
                await original_tx.save(session=session)
                
                # Create refund transaction
                refund_tx = CreditsTransaction(
                    user_id=original_tx.user_id,
                    amount=refund_amount,
                    transaction_type=TransactionType.REFUND,
                    status=TransactionStatus.COMPLETED,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    description=f"Refund: {reason}",
                    idempotency_key=idempotency_key,
                    related_entity_type="transaction",
                    related_entity_id=str(original_tx.id),
                    metadata={"original_tx_id": str(original_tx.id), "reason": reason},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                await refund_tx.insert(session=session)
                
                return refund_tx
    
    @staticmethod
    async def get_balance(user_id: PydanticObjectId) -> int:
        """Get current credit balance for user."""
        user = await User.get(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        return user.credits_balance
    
    @staticmethod
    async def get_transaction_history(
        user_id: PydanticObjectId,
        limit: int = 50,
        skip: int = 0,
        transaction_type: Optional[TransactionType] = None
    ):
        """Get credit transaction history for user."""
        query = {"user_id": user_id}
        if transaction_type:
            query["transaction_type"] = transaction_type
        
        transactions = await CreditsTransaction.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
        total = await CreditsTransaction.find(query).count()
        
        return {
            "transactions": transactions,
            "total": total,
            "limit": limit,
            "skip": skip
        }
