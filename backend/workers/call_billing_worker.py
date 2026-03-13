"""
Call Billing Worker for TrueBond/Luveloop

Runs on a 60-second tick and deducts credits from callers for active
(CONNECTED) calls. If a caller runs out of credits mid-call the call
is force-ended and both parties receive a socket notification.

Usage (start alongside the FastAPI app):
    asyncio.create_task(call_billing_worker())
"""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger("call_billing_worker")

BILLING_INTERVAL_SECONDS = 60


async def call_billing_worker():
    """
    Periodic worker: deduct 1-minute worth of credits for every active call.
    Runs indefinitely; designed to be launched as an asyncio task.
    """
    logger.info("Call billing worker started (interval=%ds)", BILLING_INTERVAL_SECONDS)

    while True:
        try:
            await asyncio.sleep(BILLING_INTERVAL_SECONDS)
            await _process_active_calls()
        except asyncio.CancelledError:
            logger.info("Call billing worker stopped")
            break
        except Exception as exc:
            logger.error("Billing worker loop error: %s", exc, exc_info=True)


async def _process_active_calls():
    """Find all CONNECTED calls and deduct 1-minute of credits."""
    try:
        from backend.models.call_session_v2 import CallSessionV2, CallStatus
        from backend.services.tb_credit_service import CreditService
        from backend.models.tb_credit import TransactionReason
        from backend.socket_server import emit_notification_to_user

        active_calls = await CallSessionV2.find(
            {"status": CallStatus.CONNECTED}
        ).to_list()

        if not active_calls:
            return

        logger.info("Billing tick: %d active call(s)", len(active_calls))

        for call in active_calls:
            try:
                await _bill_one_call(call, CreditService, TransactionReason, emit_notification_to_user)
            except Exception as exc:
                logger.error("Error billing call %s: %s", call.id, exc, exc_info=True)

    except Exception as exc:
        logger.error("_process_active_calls error: %s", exc, exc_info=True)


async def _bill_one_call(call, CreditService, TransactionReason, emit_notification_to_user):
    """Deduct one minute of credits for a single call. Force-end if insufficient."""
    from backend.models.call_session_v2 import CallStatus

    credits_needed = call.credits_per_minute
    call_type = call.metadata.get("call_type", "voice")
    tx_reason = (
        TransactionReason.VOICE_CALL
        if call_type == "voice"
        else TransactionReason.VIDEO_CALL
    )

    try:
        balance = await CreditService.get_balance(call.caller_id)

        if balance < credits_needed:
            logger.warning(
                "Caller %s has insufficient credits (%d < %d) — force-ending call %s",
                call.caller_id, balance, credits_needed, call.id
            )
            call.update_status(CallStatus.ENDED)
            call.disconnect_reason = "Insufficient credits"
            await call.save()

            for user_id in [call.caller_id, call.receiver_id]:
                try:
                    await emit_notification_to_user(
                        user_id,
                        "call_ended",
                        {
                            "call_id": call.id,
                            "reason": "Insufficient credits",
                            "credits_remaining": balance,
                        },
                    )
                except Exception:
                    pass
            return

        await CreditService.deduct_credits(
            user_id=call.caller_id,
            amount=credits_needed,
            reason=tx_reason,
            reference_id=call.id,
            description=f"Active {call_type} call (1 min billing tick)",
        )

        logger.info(
            "Billed %d credits for call %s (caller=%s, type=%s)",
            credits_needed, call.id, call.caller_id, call_type
        )

    except Exception as exc:
        logger.error("Failed to bill call %s: %s", call.id, exc, exc_info=True)
