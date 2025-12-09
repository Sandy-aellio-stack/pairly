import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from backend.models.call_session_v2 import CallSessionV2, CallStatus
from backend.services.credits_service_v2 import CreditsServiceV2
from backend.services.ledger.ledger_service import LedgerService

logger = logging.getLogger('service.calling_v2')

class CallingServiceV2:
    def __init__(self):
        self.credits_service = CreditsServiceV2()
        self.ledger_service = LedgerService()
        self.credits_per_minute = 10  # Default rate
        self.missed_call_timeout_seconds = 25
    
    async def initiate_call(
        self,
        caller_id: str,
        receiver_id: str,
        sdp_offer: Optional[str] = None
    ) -> CallSessionV2:
        """Initiate a new call"""
        try:
            # Check if caller has enough credits for at least 1 minute
            caller_balance = await self.credits_service.get_balance(caller_id)
            if caller_balance < self.credits_per_minute:
                raise ValueError("Insufficient credits to initiate call")
            
            # Create call session
            call_session = CallSessionV2(
                id=f"call_{secrets.token_hex(12)}",
                caller_id=caller_id,
                receiver_id=receiver_id,
                status=CallStatus.INITIATED,
                credits_per_minute=self.credits_per_minute,
                sdp_offer=sdp_offer
            )
            await call_session.insert()
            
            logger.info(
                f"Call initiated",
                extra={
                    "call_id": call_session.id,
                    "caller_id": caller_id,
                    "receiver_id": receiver_id
                }
            )
            
            return call_session
            
        except ValueError as e:
            logger.error(f"Failed to initiate call: {e}", extra={"caller_id": caller_id})
            raise
        except Exception as e:
            logger.error(f"Error initiating call: {e}", extra={"caller_id": caller_id}, exc_info=True)
            raise
    
    async def accept_call(
        self,
        call_id: str,
        receiver_id: str,
        sdp_answer: Optional[str] = None
    ) -> CallSessionV2:
        """Accept an incoming call"""
        call_session = await CallSessionV2.find_one(
            CallSessionV2.id == call_id,
            CallSessionV2.receiver_id == receiver_id
        )
        
        if not call_session:
            raise ValueError("Call not found or unauthorized")
        
        if call_session.status not in [CallStatus.INITIATED, CallStatus.RINGING]:
            raise ValueError(f"Call cannot be accepted in status: {call_session.status}")
        
        # Update to connected
        call_session.update_status(CallStatus.CONNECTED)
        call_session.sdp_answer = sdp_answer
        await call_session.save()
        
        logger.info(
            f"Call accepted",
            extra={
                "call_id": call_id,
                "receiver_id": receiver_id
            }
        )
        
        return call_session
    
    async def reject_call(
        self,
        call_id: str,
        receiver_id: str,
        reason: Optional[str] = None
    ) -> CallSessionV2:
        """Reject an incoming call"""
        call_session = await CallSessionV2.find_one(
            CallSessionV2.id == call_id,
            CallSessionV2.receiver_id == receiver_id
        )
        
        if not call_session:
            raise ValueError("Call not found or unauthorized")
        
        if call_session.status not in [CallStatus.INITIATED, CallStatus.RINGING]:
            raise ValueError(f"Call cannot be rejected in status: {call_session.status}")
        
        call_session.update_status(CallStatus.REJECTED)
        call_session.disconnect_reason = reason or "User rejected"
        await call_session.save()
        
        logger.info(
            f"Call rejected",
            extra={
                "call_id": call_id,
                "receiver_id": receiver_id,
                "reason": reason
            }
        )
        
        return call_session
    
    async def end_call(
        self,
        call_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> CallSessionV2:
        """End an active call and process billing"""
        call_session = await CallSessionV2.find_one(CallSessionV2.id == call_id)
        
        if not call_session:
            raise ValueError("Call not found")
        
        # Verify user is part of the call
        if user_id not in [call_session.caller_id, call_session.receiver_id]:
            raise ValueError("Unauthorized to end this call")
        
        if call_session.status == CallStatus.ENDED:
            return call_session  # Already ended
        
        # Update status
        call_session.update_status(CallStatus.ENDED)
        call_session.disconnect_reason = reason or "User ended call"
        
        # Process billing if call was connected
        if call_session.status == CallStatus.ENDED and call_session.duration_seconds > 0:
            try:
                # Deduct credits from caller
                transaction_id = await self.credits_service.deduct_credits(
                    user_id=call_session.caller_id,
                    amount=call_session.credits_spent,
                    description=f"Call to {call_session.receiver_id} ({call_session.duration_seconds}s)",
                    transaction_type="call"
                )
                call_session.credits_transaction_id = transaction_id
                
                # Record in ledger
                await self.ledger_service.record_entry(
                    debit_account=f"user:{call_session.caller_id}",
                    credit_account="revenue:calls",
                    amount=call_session.credits_spent,
                    description=f"Call billing: {call_id}",
                    reference_type="call",
                    reference_id=call_id
                )
                
                logger.info(
                    f"Call billing processed",
                    extra={
                        "call_id": call_id,
                        "caller_id": call_session.caller_id,
                        "duration_seconds": call_session.duration_seconds,
                        "credits_spent": call_session.credits_spent
                    }
                )
            except Exception as e:
                logger.error(f"Failed to process call billing: {e}", extra={"call_id": call_id}, exc_info=True)
                # Continue even if billing fails - log for manual reconciliation
        
        await call_session.save()
        
        logger.info(
            f"Call ended",
            extra={
                "call_id": call_id,
                "user_id": user_id,
                "duration": call_session.duration_seconds
            }
        )
        
        return call_session
    
    async def add_ice_candidate(
        self,
        call_id: str,
        user_id: str,
        candidate: Dict[str, Any]
    ) -> CallSessionV2:
        """Add ICE candidate for WebRTC (mock)"""
        call_session = await CallSessionV2.find_one(CallSessionV2.id == call_id)
        
        if not call_session:
            raise ValueError("Call not found")
        
        # Determine which side the candidate is from
        if user_id == call_session.caller_id:
            call_session.ice_candidates_caller.append(candidate)
        elif user_id == call_session.receiver_id:
            call_session.ice_candidates_receiver.append(candidate)
        else:
            raise ValueError("Unauthorized to add ICE candidate")
        
        call_session.updated_at = datetime.now(timezone.utc)
        await call_session.save()
        
        logger.debug(f"ICE candidate added for call {call_id}")
        return call_session
    
    async def mark_missed(self, call_id: str) -> CallSessionV2:
        """Mark a call as missed (timeout logic)"""
        call_session = await CallSessionV2.find_one(CallSessionV2.id == call_id)
        
        if not call_session:
            raise ValueError("Call not found")
        
        if call_session.status in [CallStatus.INITIATED, CallStatus.RINGING]:
            call_session.update_status(CallStatus.MISSED)
            call_session.disconnect_reason = "No answer - timeout"
            await call_session.save()
            
            logger.info(
                f"Call marked as missed",
                extra={
                    "call_id": call_id,
                    "caller_id": call_session.caller_id,
                    "receiver_id": call_session.receiver_id
                }
            )
        
        return call_session
    
    async def check_missed_calls(self):
        """Check for calls that should be marked as missed (background task simulation)"""
        timeout_threshold = datetime.now(timezone.utc) - timedelta(seconds=self.missed_call_timeout_seconds)
        
        # Find calls that are still ringing/initiated but past timeout
        missed_calls = await CallSessionV2.find(
            {
                "status": {"$in": [CallStatus.INITIATED, CallStatus.RINGING]},
                "initiated_at": {"$lt": timeout_threshold}
            }
        ).to_list()
        
        for call in missed_calls:
            await self.mark_missed(call.id)
        
        return len(missed_calls)
    
    async def get_call_history(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> list:
        """Get call history for a user"""
        calls = await CallSessionV2.find(
            {
                "$or": [
                    {"caller_id": user_id},
                    {"receiver_id": user_id}
                ]
            }
        ).sort("-created_at").skip(skip).limit(limit).to_list()
        
        return calls
    
    async def get_call_stats(self, user_id: str) -> Dict[str, Any]:
        """Get calling statistics for a user"""
        # Outgoing calls
        outgoing = await CallSessionV2.find(CallSessionV2.caller_id == user_id).count()
        outgoing_answered = await CallSessionV2.find(
            CallSessionV2.caller_id == user_id,
            CallSessionV2.status == CallStatus.ENDED
        ).count()
        
        # Incoming calls
        incoming = await CallSessionV2.find(CallSessionV2.receiver_id == user_id).count()
        incoming_answered = await CallSessionV2.find(
            CallSessionV2.receiver_id == user_id,
            CallSessionV2.status == CallStatus.ENDED
        ).count()
        
        # Total credits spent
        user_calls = await CallSessionV2.find(CallSessionV2.caller_id == user_id).to_list()
        total_credits_spent = sum(call.credits_spent for call in user_calls)
        total_minutes = sum(call.duration_seconds // 60 for call in user_calls)
        
        return {
            "outgoing_calls": outgoing,
            "outgoing_answered": outgoing_answered,
            "incoming_calls": incoming,
            "incoming_answered": incoming_answered,
            "total_credits_spent": total_credits_spent,
            "total_minutes": total_minutes
        }

_calling_service_v2 = None

def get_calling_service_v2():
    global _calling_service_v2
    if _calling_service_v2 is None:
        _calling_service_v2 = CallingServiceV2()
    return _calling_service_v2
