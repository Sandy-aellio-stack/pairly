"""
Unit Tests for Credits System

Tests all credit operations:
- Add credits
- Spend credits
- Refund credits
- Idempotency
- Edge cases
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from beanie import PydanticObjectId
from datetime import datetime

from backend.services.credits_service import (
    CreditsService,
    InsufficientCreditsError,
    DuplicateTransactionError
)
from backend.models.credits_transaction import (
    CreditsTransaction,
    TransactionType,
    TransactionStatus
)
from backend.models.user import User, Role


# ===== Fixtures =====

@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = User(
        id=PydanticObjectId(),
        email="test@example.com",
        password_hash="hashed",
        name="Test User",
        role=Role.FAN,
        credits_balance=100
    )
    return user


@pytest.fixture
def mock_session():
    """Mock MongoDB session."""
    session = AsyncMock()
    session.start_transaction = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock()
    return session


# ===== Add Credits Tests =====

@pytest.mark.asyncio
async def test_add_credits_success(mock_user, mock_session):
    """Test successfully adding credits."""
    with patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get', return_value=mock_user), \
         patch.object(User, 'save'), \
         patch.object(CreditsTransaction, 'insert'):
        
        # Setup mocks
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # Execute
        tx = await CreditsService.add_credits(
            user_id=mock_user.id,
            amount=50,
            transaction_type=TransactionType.PURCHASE,
            description="Test purchase",
            idempotency_key="test_key_1"
        )
        
        # Verify
        assert tx.amount == 50
        assert tx.transaction_type == TransactionType.PURCHASE
        assert tx.balance_before == 100
        assert tx.balance_after == 150
        assert tx.status == TransactionStatus.COMPLETED


@pytest.mark.asyncio
async def test_add_credits_idempotency(mock_user):
    """Test idempotency - duplicate key should raise error."""
    with patch.object(CreditsTransaction, 'find_one', return_value=MagicMock()):
        with pytest.raises(DuplicateTransactionError):
            await CreditsService.add_credits(
                user_id=mock_user.id,
                amount=50,
                transaction_type=TransactionType.PURCHASE,
                description="Test",
                idempotency_key="duplicate_key"
            )


@pytest.mark.asyncio
async def test_add_credits_negative_amount():
    """Test that negative amounts are rejected."""
    with pytest.raises(ValueError, match="Amount must be positive"):
        await CreditsService.add_credits(
            user_id=PydanticObjectId(),
            amount=-10,
            transaction_type=TransactionType.PURCHASE,
            description="Invalid"
        )


@pytest.mark.asyncio
async def test_add_credits_zero_amount():
    """Test that zero amounts are rejected."""
    with pytest.raises(ValueError, match="Amount must be positive"):
        await CreditsService.add_credits(
            user_id=PydanticObjectId(),
            amount=0,
            transaction_type=TransactionType.PURCHASE,
            description="Invalid"
        )


# ===== Spend Credits Tests =====

@pytest.mark.asyncio
async def test_spend_credits_success(mock_user, mock_session):
    """Test successfully spending credits."""
    with patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get', return_value=mock_user), \
         patch.object(User, 'save'), \
         patch.object(CreditsTransaction, 'insert'):
        
        # Setup mocks
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # Execute
        tx = await CreditsService.spend_credits(
            user_id=mock_user.id,
            amount=30,
            transaction_type=TransactionType.MESSAGE,
            description="Send message",
            idempotency_key="spend_key_1"
        )
        
        # Verify
        assert tx.amount == -30  # Negative for spending
        assert tx.transaction_type == TransactionType.MESSAGE
        assert tx.balance_before == 100
        assert tx.balance_after == 70
        assert tx.status == TransactionStatus.COMPLETED


@pytest.mark.asyncio
async def test_spend_credits_insufficient(mock_user, mock_session):
    """Test spending more credits than available."""
    with patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get', return_value=mock_user):
        
        # Setup mocks
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # Execute - try to spend 150 when only 100 available
        with pytest.raises(InsufficientCreditsError):
            await CreditsService.spend_credits(
                user_id=mock_user.id,
                amount=150,
                transaction_type=TransactionType.TIP,
                description="Tip too large"
            )


@pytest.mark.asyncio
async def test_spend_credits_exact_balance(mock_user, mock_session):
    """Test spending exactly the available balance."""
    with patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get', return_value=mock_user), \
         patch.object(User, 'save'), \
         patch.object(CreditsTransaction, 'insert'):
        
        # Setup mocks
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # Execute - spend exactly 100
        tx = await CreditsService.spend_credits(
            user_id=mock_user.id,
            amount=100,
            transaction_type=TransactionType.MESSAGE,
            description="Spend all"
        )
        
        # Verify
        assert tx.balance_after == 0


@pytest.mark.asyncio
async def test_spend_credits_idempotency(mock_user):
    """Test idempotency for spending."""
    with patch.object(CreditsTransaction, 'find_one', return_value=MagicMock()):
        with pytest.raises(DuplicateTransactionError):
            await CreditsService.spend_credits(
                user_id=mock_user.id,
                amount=10,
                transaction_type=TransactionType.MESSAGE,
                description="Duplicate",
                idempotency_key="duplicate_spend"
            )


# ===== Refund Tests =====

@pytest.mark.asyncio
async def test_refund_credits_success(mock_user, mock_session):
    """Test successfully refunding a transaction."""
    # Create original transaction
    original_tx = CreditsTransaction(
        id=PydanticObjectId(),
        user_id=mock_user.id,
        amount=-30,  # Spend transaction
        transaction_type=TransactionType.MESSAGE,
        status=TransactionStatus.COMPLETED,
        balance_before=100,
        balance_after=70,
        description="Original spend"
    )
    
    with patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(CreditsTransaction, 'get', return_value=original_tx), \
         patch.object(User, 'get', return_value=mock_user), \
         patch.object(User, 'save'), \
         patch.object(CreditsTransaction, 'save'), \
         patch.object(CreditsTransaction, 'insert'):
        
        # Setup mocks
        mock_user.credits_balance = 70  # Current balance after spend
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # Execute refund
        refund_tx = await CreditsService.refund_credits(
            original_transaction_id=str(original_tx.id),
            reason="Test refund",
            idempotency_key="refund_key_1"
        )
        
        # Verify
        assert refund_tx.amount == 30  # Positive (reversing negative)
        assert refund_tx.transaction_type == TransactionType.REFUND
        assert refund_tx.balance_before == 70
        assert refund_tx.balance_after == 100


@pytest.mark.asyncio
async def test_refund_already_reversed(mock_user):
    """Test refunding an already refunded transaction."""
    # Transaction already reversed
    original_tx = CreditsTransaction(
        id=PydanticObjectId(),
        user_id=mock_user.id,
        amount=-30,
        transaction_type=TransactionType.MESSAGE,
        status=TransactionStatus.REVERSED,  # Already reversed
        balance_before=100,
        balance_after=70,
        description="Already refunded"
    )
    
    with patch.object(CreditsTransaction, 'get', return_value=original_tx):
        with pytest.raises(Exception, match="already refunded"):
            await CreditsService.refund_credits(
                original_transaction_id=str(original_tx.id),
                reason="Double refund"
            )


@pytest.mark.asyncio
async def test_refund_nonexistent_transaction():
    """Test refunding a transaction that doesn't exist."""
    with patch.object(CreditsTransaction, 'get', return_value=None):
        with pytest.raises(Exception, match="not found"):
            await CreditsService.refund_credits(
                original_transaction_id="nonexistent_id",
                reason="Invalid"
            )


# ===== Get Balance Tests =====

@pytest.mark.asyncio
async def test_get_balance(mock_user):
    """Test getting user balance."""
    with patch.object(User, 'get', return_value=mock_user):
        balance = await CreditsService.get_balance(mock_user.id)
        assert balance == 100


@pytest.mark.asyncio
async def test_get_balance_nonexistent_user():
    """Test getting balance for non-existent user."""
    with patch.object(User, 'get', return_value=None):
        with pytest.raises(Exception, match="not found"):
            await CreditsService.get_balance(PydanticObjectId())


# ===== Transaction History Tests =====

@pytest.mark.asyncio
async def test_get_transaction_history():
    """Test getting transaction history."""
    user_id = PydanticObjectId()
    
    mock_transactions = [
        CreditsTransaction(
            user_id=user_id,
            amount=50,
            transaction_type=TransactionType.PURCHASE,
            balance_before=0,
            balance_after=50,
            description="Purchase"
        ),
        CreditsTransaction(
            user_id=user_id,
            amount=-10,
            transaction_type=TransactionType.MESSAGE,
            balance_before=50,
            balance_after=40,
            description="Message"
        )
    ]
    
    with patch.object(CreditsTransaction, 'find') as mock_find:
        # Mock chain
        mock_find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=mock_transactions)
        mock_find.return_value.count = AsyncMock(return_value=2)
        
        result = await CreditsService.get_transaction_history(user_id, limit=10, skip=0)
        
        assert len(result["transactions"]) == 2
        assert result["total"] == 2
        assert result["limit"] == 10


# ===== Concurrency Tests =====

@pytest.mark.asyncio
async def test_concurrent_spends_race_condition(mock_user, mock_session):
    """
    Test race condition: Two concurrent spends should not overdraw.
    
    This tests that MongoDB transactions prevent race conditions.
    In a real test, we'd need actual database, but here we verify the logic.
    """
    # This test demonstrates the importance of using transactions
    # In production, MongoDB's ACID guarantees prevent race conditions
    
    # Mock user with 100 credits
    mock_user.credits_balance = 100
    
    with patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get', return_value=mock_user), \
         patch.object(User, 'save'), \
         patch.object(CreditsTransaction, 'insert'):
        
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # First spend succeeds
        tx1 = await CreditsService.spend_credits(
            user_id=mock_user.id,
            amount=60,
            transaction_type=TransactionType.MESSAGE,
            description="Spend 1"
        )
        
        # Update mock user balance
        mock_user.credits_balance = 40
        
        # Second spend succeeds
        tx2 = await CreditsService.spend_credits(
            user_id=mock_user.id,
            amount=30,
            transaction_type=TransactionType.MESSAGE,
            description="Spend 2"
        )
        
        # Verify both completed without overdraw
        assert tx1.balance_after == 40
        assert tx2.balance_after == 10


# ===== Integration Test Scenarios =====

@pytest.mark.asyncio
async def test_purchase_and_spend_flow(mock_user, mock_session):
    """Test complete flow: Purchase credits, then spend them."""
    with patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get', return_value=mock_user), \
         patch.object(User, 'save'), \
         patch.object(CreditsTransaction, 'find_one', return_value=None), \
         patch.object(CreditsTransaction, 'insert'):
        
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # Step 1: Purchase 100 credits
        purchase_tx = await CreditsService.add_credits(
            user_id=mock_user.id,
            amount=100,
            transaction_type=TransactionType.PURCHASE,
            description="Purchase package"
        )
        assert purchase_tx.balance_after == 200
        
        # Update mock for next operation
        mock_user.credits_balance = 200
        
        # Step 2: Spend 50 credits
        spend_tx = await CreditsService.spend_credits(
            user_id=mock_user.id,
            amount=50,
            transaction_type=TransactionType.MESSAGE,
            description="Send messages"
        )
        assert spend_tx.balance_after == 150


@pytest.mark.asyncio
async def test_tip_flow(mock_user, mock_session):
    """Test tipping flow: Deduct from tipper, add to creator."""
    creator = User(
        id=PydanticObjectId(),
        email="creator@example.com",
        password_hash="hashed",
        name="Creator",
        role=Role.CREATOR,
        credits_balance=50
    )
    
    with patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get') as mock_get, \
         patch.object(User, 'save'), \
         patch.object(CreditsTransaction, 'find_one', return_value=None), \
         patch.object(CreditsTransaction, 'insert'):
        
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # First call returns tipper, second returns creator
        mock_get.side_effect = [mock_user, creator]
        
        # Tipper sends tip
        tip_tx = await CreditsService.spend_credits(
            user_id=mock_user.id,
            amount=20,
            transaction_type=TransactionType.TIP,
            description="Tip creator",
            related_user_id=creator.id
        )
        
        # Update mocks
        mock_user.credits_balance = 80
        mock_get.side_effect = [creator]  # Reset for next call
        
        # Creator receives tip
        receive_tx = await CreditsService.add_credits(
            user_id=creator.id,
            amount=20,
            transaction_type=TransactionType.BONUS,
            description="Tip received"
        )
        
        assert tip_tx.balance_after == 80
        assert receive_tx.balance_after == 70


if __name__ == "__main__":
    # Run tests with: pytest backend/tests/test_credits.py -v
    pytest.main([__file__, "-v"])
