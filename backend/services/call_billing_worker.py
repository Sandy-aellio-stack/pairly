"""
Call Billing Worker - Celery tasks for per-minute credit deduction.
"""

import os
from celery import Celery
from datetime import datetime
from beanie import PydanticObjectId

from backend.models.call_session import CallSession, CallStatus
from backend.services.credits_service import CreditsService, InsufficientCreditsError
from backend.models.credits_transaction import TransactionType
from backend.services.call_signaling import CallSignalingService

# Celery setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
celery_app = Celery(
    "call_billing_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="call_billing.tick")
def billing_tick_task(call_id: str):
    """
    Billing tick - Deduct credits for ongoing call.
    
    Called every 60 seconds for active calls.
    """
    import asyncio
    asyncio.run(_billing_tick(call_id))


async def _billing_tick(call_id: str):
    """Async implementation of billing tick."""
    try:
        print(f"💰 Billing tick for call {call_id}")
        
        # Get call session
        call = await CallSession.get(call_id)
        if not call:
            print(f"⚠️  Call {call_id} not found")
            return
        
        # Only bill active calls
        if call.status != CallStatus.ACTIVE:
            print(f"⚠️  Call {call_id} is not active (status: {call.status})")
            return
        
        # Calculate billing amount (cost per minute)
        cost = call.cost_per_minute
        
        # Try to deduct credits from caller
        try:
            tx = await CreditsService.spend_credits(
                user_id=call.caller_id,
                amount=cost,
                transaction_type=TransactionType.CALL,
                description=f"Call billing - minute {call.billed_seconds // 60 + 1}",
                idempotency_key=f"call_{call_id}_minute_{call.billed_seconds // 60 + 1}",
                related_user_id=call.receiver_id,
                related_entity_type="call",
                related_entity_id=call_id
            )
            
            # Update call billing info
            call.billed_seconds += 60
            call.total_cost += cost
            call.updated_at = datetime.utcnow()
            await call.save()
            
            print(f"✅ Billed {cost} credits for call {call_id} (total: {call.total_cost})")
            
            # Schedule next tick (60 seconds)
            billing_tick_task.apply_async(args=[call_id], countdown=60)
        
        except InsufficientCreditsError:
            # Caller ran out of credits - end call
            print(f"❌ Insufficient credits for call {call_id} - ending call")
            
            # Update call status
            call.status = CallStatus.INSUFFICIENT_CREDITS
            call.ended_at = datetime.utcnow()
            call.end_reason = "Insufficient credits"
            
            # Calculate final duration
            if call.started_at:
                duration = (datetime.utcnow() - call.started_at).total_seconds()
                call.duration_seconds = int(duration)
            
            call.updated_at = datetime.utcnow()
            await call.save()
            
            # Notify both participants
            await CallSignalingService.send_to_user(str(call.caller_id), {
                "type": "call_ended",
                "call_id": call_id,
                "reason": "Insufficient credits",
                "duration": call.duration_seconds
            })
            
            await CallSignalingService.send_to_user(str(call.receiver_id), {
                "type": "call_ended",
                "call_id": call_id,
                "reason": "Caller insufficient credits",
                "duration": call.duration_seconds
            })
            
            # Remove from active calls
            if call_id in CallSignalingService.active_calls:
                del CallSignalingService.active_calls[call_id]
    
    except Exception as e:
        print(f"❌ Error in billing tick for call {call_id}: {e}")


@celery_app.task(name="call_billing.finalize")
def finalize_call_task(call_id: str):
    """
    Finalize call after it ends.
    
    - Calculate final billing
    - Update statistics
    - Send notifications
    """
    import asyncio
    asyncio.run(_finalize_call(call_id))


async def _finalize_call(call_id: str):
    """Async implementation of call finalization."""
    try:
        print(f"📊 Finalizing call {call_id}")
        
        call = await CallSession.get(call_id)
        if not call:
            return
        
        # Calculate any remaining unbilled seconds
        if call.started_at and call.status == CallStatus.ENDED:
            total_seconds = call.duration_seconds
            unbilled_seconds = total_seconds - call.billed_seconds
            
            if unbilled_seconds > 0:
                # Bill remaining seconds (partial minute)
                partial_cost = int((unbilled_seconds / 60) * call.cost_per_minute)
                
                if partial_cost > 0:
                    try:
                        tx = await CreditsService.spend_credits(
                            user_id=call.caller_id,
                            amount=partial_cost,
                            transaction_type=TransactionType.CALL,
                            description=f"Call billing - final {unbilled_seconds}s",
                            idempotency_key=f"call_{call_id}_final",
                            related_user_id=call.receiver_id,
                            related_entity_type="call",
                            related_entity_id=call_id
                        )
                        
                        call.total_cost += partial_cost
                        call.billed_seconds = total_seconds
                        await call.save()
                        
                        print(f"✅ Final billing {partial_cost} credits for call {call_id}")
                    
                    except InsufficientCreditsError:
                        print(f"⚠️  Insufficient credits for final billing of call {call_id}")
        
        # TODO: Update user call statistics
        # TODO: Send post-call notifications
        # TODO: Queue for quality review if needed
        
        print(f"✅ Call {call_id} finalized - Total cost: {call.total_cost} credits")
    
    except Exception as e:
        print(f"❌ Error finalizing call {call_id}: {e}")


@celery_app.task(name="call_billing.fraud_check")
def fraud_check_task(call_id: str):
    """
    Fraud/abuse detection for calls.
    
    Check for:
    - Unusually long calls
    - Rapid sequential calls
    - Suspicious patterns
    """
    import asyncio
    asyncio.run(_fraud_check(call_id))


async def _fraud_check(call_id: str):
    """Async implementation of fraud check."""
    try:
        call = await CallSession.get(call_id)
        if not call:
            return
        
        # Stub: Implement fraud detection logic
        # Examples:
        # - Call duration > 2 hours → Flag
        # - User making > 10 calls/hour → Flag
        # - High cost in short time → Flag
        
        if call.duration_seconds > 7200:  # > 2 hours
            await CallSignalingService.flag_for_moderation(
                call_id=call_id,
                reason="Unusually long call (> 2 hours)"
            )
            print(f"🚨 Call {call_id} flagged - unusually long")
        
        # TODO: Implement more sophisticated fraud detection
    
    except Exception as e:
        print(f"❌ Error in fraud check for call {call_id}: {e}")


# Celery beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # No periodic tasks needed - billing ticks are scheduled per-call
}
