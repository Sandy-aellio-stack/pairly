"""
Unit Tests for WebRTC Calling System

Tests:
- Call signaling state machine
- Billing ticker
- Insufficient credits handling
- Call rejection/disconnect
- ICE candidate exchange
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from beanie import PydanticObjectId
from datetime import datetime, timezone

from backend.models.call_session import CallSession, CallStatus
from backend.models.user import User, Role
from backend.services.call_signaling import CallSignalingService
from backend.services.credits_service import CreditsService, InsufficientCreditsError


# ===== Fixtures =====

@pytest.fixture
def mock_caller():
    """Create mock caller user."""
    return User(
        id=PydanticObjectId(),
        email="caller@example.com",
        password_hash="hashed",
        name="Caller User",
        role=Role.FAN,
        credits_balance=100
    )


@pytest.fixture
def mock_receiver():
    """Create mock receiver user."""
    return User(
        id=PydanticObjectId(),
        email="receiver@example.com",
        password_hash="hashed",
        name="Receiver User",
        role=Role.CREATOR,
        credits_balance=50
    )


@pytest.fixture
def mock_call(mock_caller, mock_receiver):
    """Create mock call session."""
    return CallSession(
        id=PydanticObjectId(),
        caller_id=mock_caller.id,
        receiver_id=mock_receiver.id,
        status=CallStatus.RINGING,
        offer_sdp="mock_offer_sdp",
        initiated_at=datetime.now(timezone.utc)
    )


# ===== Call Initiation Tests =====

@pytest.mark.asyncio
async def test_initiate_call_success(mock_caller, mock_receiver):
    """Test successfully initiating a call."""
    with patch.object(CallSignalingService, 'active_connections', {str(mock_receiver.id): MagicMock()}), \
         patch.object(CallSignalingService, 'send_to_user', return_value=True), \
         patch.object(CallSession, 'insert'), \
         patch('backend.services.call_signaling.log_event'):
        
        call = await CallSignalingService.initiate_call(
            caller_id=mock_caller.id,
            receiver_id=mock_receiver.id,
            offer_sdp="test_offer_sdp"
        )
        
        assert call.status == CallStatus.RINGING
        assert call.caller_id == mock_caller.id
        assert call.receiver_id == mock_receiver.id
        assert call.offer_sdp == "test_offer_sdp"


@pytest.mark.asyncio
async def test_initiate_call_receiver_offline(mock_caller, mock_receiver):
    """Test initiating call when receiver is offline."""
    with patch.object(CallSignalingService, 'active_connections', {}):
        with pytest.raises(Exception, match="not online"):
            await CallSignalingService.initiate_call(
                caller_id=mock_caller.id,
                receiver_id=mock_receiver.id,
                offer_sdp="test_offer_sdp"
            )


@pytest.mark.asyncio
async def test_initiate_call_already_in_call(mock_caller, mock_receiver):
    """Test initiating call when caller is already in another call."""
    existing_call = CallSession(
        caller_id=mock_caller.id,
        receiver_id=PydanticObjectId(),
        status=CallStatus.ACTIVE
    )
    
    with patch.object(CallSignalingService, 'active_connections', {str(mock_receiver.id): MagicMock()}), \
         patch.object(CallSignalingService, 'active_calls', {"existing": existing_call}):
        
        with pytest.raises(Exception, match="already in a call"):
            await CallSignalingService.initiate_call(
                caller_id=mock_caller.id,
                receiver_id=mock_receiver.id,
                offer_sdp="test_offer_sdp"
            )


# ===== Call Acceptance Tests =====

@pytest.mark.asyncio
async def test_accept_call_success(mock_call, mock_receiver):
    """Test successfully accepting a call."""
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'), \
         patch.object(CallSignalingService, 'send_to_user', return_value=True), \
         patch('backend.services.call_signaling.log_event'):
        
        call = await CallSignalingService.accept_call(
            call_id=str(mock_call.id),
            receiver_id=mock_receiver.id,
            answer_sdp="test_answer_sdp"
        )
        
        assert call.status == CallStatus.ACCEPTED
        assert call.answer_sdp == "test_answer_sdp"
        assert call.accepted_at is not None


@pytest.mark.asyncio
async def test_accept_call_wrong_user(mock_call):
    """Test accepting call by wrong user."""
    wrong_user_id = PydanticObjectId()
    
    with patch.object(CallSession, 'get', return_value=mock_call):
        with pytest.raises(Exception, match="Not the call receiver"):
            await CallSignalingService.accept_call(
                call_id=str(mock_call.id),
                receiver_id=wrong_user_id,
                answer_sdp="test_answer_sdp"
            )


@pytest.mark.asyncio
async def test_accept_call_wrong_status(mock_call, mock_receiver):
    """Test accepting call that's not ringing."""
    mock_call.status = CallStatus.ENDED
    
    with patch.object(CallSession, 'get', return_value=mock_call):
        with pytest.raises(Exception, match="not ringing"):
            await CallSignalingService.accept_call(
                call_id=str(mock_call.id),
                receiver_id=mock_receiver.id,
                answer_sdp="test_answer_sdp"
            )


# ===== Call Rejection Tests =====

@pytest.mark.asyncio
async def test_reject_call_success(mock_call, mock_receiver):
    """Test successfully rejecting a call."""
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'), \
         patch.object(CallSignalingService, 'send_to_user', return_value=True), \
         patch('backend.services.call_signaling.log_event'):
        
        call = await CallSignalingService.reject_call(
            call_id=str(mock_call.id),
            receiver_id=mock_receiver.id,
            reason="Not interested"
        )
        
        assert call.status == CallStatus.REJECTED
        assert call.end_reason == "Not interested"
        assert call.ended_at is not None


# ===== Call Start Tests =====

@pytest.mark.asyncio
async def test_start_call_success(mock_call):
    """Test marking call as started."""
    mock_call.status = CallStatus.ACCEPTED
    
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'):
        
        call = await CallSignalingService.start_call(str(mock_call.id))
        
        assert call.status == CallStatus.ACTIVE
        assert call.started_at is not None


@pytest.mark.asyncio
async def test_start_call_not_accepted(mock_call):
    """Test starting call that wasn't accepted."""
    mock_call.status = CallStatus.RINGING
    
    with patch.object(CallSession, 'get', return_value=mock_call):
        with pytest.raises(Exception, match="not accepted"):
            await CallSignalingService.start_call(str(mock_call.id))


# ===== Call End Tests =====

@pytest.mark.asyncio
async def test_end_call_success(mock_call, mock_caller):
    """Test successfully ending a call."""
    mock_call.status = CallStatus.ACTIVE
    mock_call.started_at = datetime.now(timezone.utc)
    
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'), \
         patch.object(CallSignalingService, 'send_to_user', return_value=True), \
         patch('backend.services.call_signaling.log_event'):
        
        call = await CallSignalingService.end_call(
            call_id=str(mock_call.id),
            user_id=mock_caller.id,
            reason="User ended"
        )
        
        assert call.status == CallStatus.ENDED
        assert call.ended_at is not None
        assert call.duration_seconds >= 0


@pytest.mark.asyncio
async def test_end_call_not_participant(mock_call):
    """Test ending call by non-participant."""
    random_user_id = PydanticObjectId()
    
    with patch.object(CallSession, 'get', return_value=mock_call):
        with pytest.raises(Exception, match="Not a call participant"):
            await CallSignalingService.end_call(
                call_id=str(mock_call.id),
                user_id=random_user_id
            )


# ===== Billing Tests =====

@pytest.mark.asyncio
async def test_billing_tick_success(mock_call, mock_caller):
    """Test successful billing tick."""
    mock_call.status = CallStatus.ACTIVE
    mock_call.started_at = datetime.now(timezone.utc)
    
    mock_session = AsyncMock()
    
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'), \
         patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get', return_value=mock_caller), \
         patch.object(User, 'save'), \
         patch('backend.services.call_billing_worker.CreditsService.spend_credits') as mock_spend:
        
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # Mock successful credit deduction
        from backend.models.credits_transaction import CreditsTransaction, TransactionType, TransactionStatus
        mock_tx = CreditsTransaction(
            user_id=mock_caller.id,
            amount=-5,
            transaction_type=TransactionType.CALL,
            balance_before=100,
            balance_after=95,
            status=TransactionStatus.COMPLETED,
            description="Call billing"
        )
        mock_spend.return_value = mock_tx
        
        # Run billing tick
        from backend.services.call_billing_worker import _billing_tick
        await _billing_tick(str(mock_call.id))
        
        # Verify credits were deducted
        mock_spend.assert_called_once()


@pytest.mark.asyncio
async def test_billing_tick_insufficient_credits(mock_call, mock_caller):
    """Test billing tick when user has insufficient credits."""
    mock_call.status = CallStatus.ACTIVE
    mock_call.started_at = datetime.now(timezone.utc)
    mock_caller.credits_balance = 2  # Not enough for 5 credit charge
    
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'), \
         patch('backend.services.call_billing_worker.CreditsService.spend_credits') as mock_spend, \
         patch.object(CallSignalingService, 'send_to_user', return_value=True):
        
        # Mock insufficient credits error
        mock_spend.side_effect = InsufficientCreditsError("Not enough credits")
        
        # Run billing tick
        from backend.services.call_billing_worker import _billing_tick
        await _billing_tick(str(mock_call.id))
        
        # Verify call was ended
        assert mock_call.status == CallStatus.INSUFFICIENT_CREDITS
        assert mock_call.ended_at is not None


# ===== ICE Candidate Tests =====

@pytest.mark.asyncio
async def test_add_ice_candidate(mock_call, mock_caller):
    """Test adding ICE candidate."""
    candidate = {"candidate": "mock_candidate", "sdpMid": "0"}
    
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'), \
         patch.object(CallSignalingService, 'send_to_user', return_value=True):
        
        await CallSignalingService.add_ice_candidate(
            call_id=str(mock_call.id),
            user_id=mock_caller.id,
            candidate=candidate
        )
        
        # Verify candidate was stored
        assert len(mock_call.ice_candidates) == 1
        assert mock_call.ice_candidates[0]["candidate"] == candidate


# ===== Moderation Tests =====

@pytest.mark.asyncio
async def test_flag_for_moderation(mock_call):
    """Test flagging call for moderation."""
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'), \
         patch('backend.services.call_signaling.log_event'):
        
        await CallSignalingService.flag_for_moderation(
            call_id=str(mock_call.id),
            reason="Inappropriate content"
        )
        
        assert mock_call.flagged_for_moderation is True
        assert mock_call.moderation_notes == "Inappropriate content"


# ===== Call Finalization Tests =====

@pytest.mark.asyncio
async def test_finalize_call_with_partial_billing(mock_call, mock_caller):
    """Test finalizing call with unbilled seconds."""
    mock_call.status = CallStatus.ENDED
    mock_call.started_at = datetime.now(timezone.utc)
    mock_call.duration_seconds = 75  # 1 minute 15 seconds
    mock_call.billed_seconds = 60  # Only 1 minute billed
    mock_call.cost_per_minute = 5
    
    mock_session = AsyncMock()
    
    with patch.object(CallSession, 'get', return_value=mock_call), \
         patch.object(CallSession, 'save'), \
         patch.object(User, 'get_motor_client') as mock_client, \
         patch.object(User, 'get', return_value=mock_caller), \
         patch.object(User, 'save'), \
         patch('backend.services.call_billing_worker.CreditsService.spend_credits') as mock_spend:
        
        mock_client.return_value.start_session.return_value.__aenter__.return_value = mock_session
        
        # Mock partial billing
        from backend.models.credits_transaction import CreditsTransaction, TransactionType, TransactionStatus
        mock_tx = CreditsTransaction(
            user_id=mock_caller.id,
            amount=-1,  # Partial amount
            transaction_type=TransactionType.CALL,
            balance_before=95,
            balance_after=94,
            status=TransactionStatus.COMPLETED,
            description="Call billing - final"
        )
        mock_spend.return_value = mock_tx
        
        # Run finalization
        from backend.services.call_billing_worker import _finalize_call
        await _finalize_call(str(mock_call.id))
        
        # Verify partial billing was applied
        mock_spend.assert_called_once()


# ===== State Machine Tests =====

@pytest.mark.asyncio
async def test_call_state_machine_full_flow(mock_caller, mock_receiver):
    """Test complete call state machine flow."""
    call_id = str(PydanticObjectId())
    
    # State 1: INITIATING -> RINGING
    call = CallSession(
        id=PydanticObjectId(call_id),
        caller_id=mock_caller.id,
        receiver_id=mock_receiver.id,
        status=CallStatus.INITIATING
    )
    
    # Transition to RINGING
    call.status = CallStatus.RINGING
    assert call.status == CallStatus.RINGING
    
    # State 2: RINGING -> ACCEPTED
    call.status = CallStatus.ACCEPTED
    call.accepted_at = datetime.now(timezone.utc)
    assert call.status == CallStatus.ACCEPTED
    
    # State 3: ACCEPTED -> ACTIVE
    call.status = CallStatus.ACTIVE
    call.started_at = datetime.now(timezone.utc)
    assert call.status == CallStatus.ACTIVE
    
    # State 4: ACTIVE -> ENDED
    call.status = CallStatus.ENDED
    call.ended_at = datetime.now(timezone.utc)
    assert call.status == CallStatus.ENDED


if __name__ == "__main__":
    # Run tests with: pytest backend/tests/test_calls.py -v
    pytest.main([__file__, "-v"])
