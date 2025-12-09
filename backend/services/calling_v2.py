import logging
import secrets
from datetime import datetime, timezone
from backend.models.call_session_v2 import CallSessionV2, CallStatus
from backend.services.credits_service_v2 import CreditsServiceV2

logger = logging.getLogger('service.calling_v2')

class CallingServiceV2:
    def __init__(self):
        self.credits_service = CreditsServiceV2()
    
    async def start_call(self, caller_id: str, receiver_id: str) -> CallSessionV2:
        call = CallSessionV2(
            id=f"call_{secrets.token_hex(12)}",
            caller_id=caller_id,
            receiver_id=receiver_id,
            status=CallStatus.RINGING
        )
        await call.insert()
        logger.info(f"Call started: {call.id}")
        return call
    
    async def accept_call(self, call_id: str) -> CallSessionV2:
        call = await CallSessionV2.find_one(CallSessionV2.id == call_id)
        if call:
            call.status = CallStatus.ACCEPTED
            call.started_at = datetime.now(timezone.utc)
            await call.save()
        return call
    
    async def end_call(self, call_id: str) -> CallSessionV2:
        call = await CallSessionV2.find_one(CallSessionV2.id == call_id)
        if call:
            call.status = CallStatus.ENDED
            call.ended_at = datetime.now(timezone.utc)
            
            if call.started_at:
                call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())
                call.credits_spent = call.calculate_cost()
                
                # Deduct credits
                if call.credits_spent > 0:
                    try:
                        await self.credits_service.deduct_credits(
                            user_id=call.caller_id,
                            amount=call.credits_spent,
                            description=f"Call {call.id}",
                            transaction_type="call"
                        )
                    except Exception as e:
                        logger.error(f"Failed to deduct call credits: {e}")
            
            await call.save()
        return call

_calling_service_v2 = None

def get_calling_service_v2():
    global _calling_service_v2
    if _calling_service_v2 is None:
        _calling_service_v2 = CallingServiceV2()
    return _calling_service_v2
