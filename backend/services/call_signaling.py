"""Call Signaling Service - Manages WebRTC signaling state."""

from typing import Dict, Optional
from datetime import datetime
from beanie import PydanticObjectId
from fastapi import HTTPException, WebSocket
import json

from backend.models.call_session import CallSession, CallStatus
from backend.models.user import User
from backend.services.audit import log_event


class CallSignalingService:
    """Service for managing call signaling and state."""
    
    # Track active WebSocket connections
    # Format: {user_id: websocket}
    active_connections: Dict[str, WebSocket] = {}
    
    # Track active call sessions
    # Format: {call_id: CallSession}
    active_calls: Dict[str, CallSession] = {}
    
    @classmethod
    async def register_connection(cls, user_id: str, websocket: WebSocket):
        """Register a WebSocket connection for a user."""
        cls.active_connections[user_id] = websocket
        print(f"📞 User {user_id} connected to call signaling")
    
    @classmethod
    async def unregister_connection(cls, user_id: str):
        """Unregister a user's WebSocket connection."""
        if user_id in cls.active_connections:
            del cls.active_connections[user_id]
            print(f"📞 User {user_id} disconnected from call signaling")
    
    @classmethod
    async def send_to_user(cls, user_id: str, message: dict):
        """Send a message to a specific user via WebSocket."""
        if user_id in cls.active_connections:
            try:
                await cls.active_connections[user_id].send_json(message)
                return True
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                await cls.unregister_connection(user_id)
                return False
        return False
    
    @classmethod
    async def initiate_call(
        cls,
        caller_id: PydanticObjectId,
        receiver_id: PydanticObjectId,
        offer_sdp: str,
        caller_ip: Optional[str] = None
    ) -> CallSession:
        """Initiate a new call."""
        # Check if receiver is online
        if str(receiver_id) not in cls.active_connections:
            raise HTTPException(400, "Receiver is not online")
        
        # Check if either user is already in a call
        for call in cls.active_calls.values():
            if call.status in [CallStatus.ACTIVE, CallStatus.RINGING, CallStatus.ACCEPTED]:
                if call.caller_id == caller_id or call.receiver_id == caller_id:
                    raise HTTPException(400, "Caller is already in a call")
                if call.caller_id == receiver_id or call.receiver_id == receiver_id:
                    raise HTTPException(400, "Receiver is already in a call")
        
        # Create call session
        call = CallSession(
            caller_id=caller_id,
            receiver_id=receiver_id,
            status=CallStatus.RINGING,
            offer_sdp=offer_sdp,
            caller_ip=caller_ip,
            initiated_at=datetime.utcnow()
        )
        await call.insert()
        
        cls.active_calls[str(call.id)] = call
        
        # Notify receiver via WebSocket
        await cls.send_to_user(str(receiver_id), {
            "type": "call_incoming",
            "call_id": str(call.id),
            "caller_id": str(caller_id),
            "offer_sdp": offer_sdp,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Audit log
        await log_event(
            actor_user_id=caller_id,
            actor_ip=caller_ip,
            action="call_initiated",
            details={
                "call_id": str(call.id),
                "receiver_id": str(receiver_id)
            },
            severity="info"
        )
        
        return call
    
    @classmethod
    async def accept_call(
        cls,
        call_id: str,
        receiver_id: PydanticObjectId,
        answer_sdp: str,
        receiver_ip: Optional[str] = None
    ) -> CallSession:
        """Accept an incoming call."""
        call = await CallSession.get(call_id)
        if not call:
            raise HTTPException(404, "Call not found")
        
        if call.receiver_id != receiver_id:
            raise HTTPException(403, "Not the call receiver")
        
        if call.status != CallStatus.RINGING:
            raise HTTPException(400, f"Call is not ringing (status: {call.status})")
        
        # Update call
        call.status = CallStatus.ACCEPTED
        call.answer_sdp = answer_sdp
        call.accepted_at = datetime.utcnow()
        call.receiver_ip = receiver_ip
        call.updated_at = datetime.utcnow()
        await call.save()
        
        cls.active_calls[call_id] = call
        
        # Notify caller
        await cls.send_to_user(str(call.caller_id), {
            "type": "call_accepted",
            "call_id": call_id,
            "answer_sdp": answer_sdp,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Audit log
        await log_event(
            actor_user_id=receiver_id,
            actor_ip=receiver_ip,
            action="call_accepted",
            details={"call_id": call_id},
            severity="info"
        )
        
        return call
    
    @classmethod
    async def reject_call(
        cls,
        call_id: str,
        receiver_id: PydanticObjectId,
        reason: Optional[str] = None
    ) -> CallSession:
        """Reject an incoming call."""
        call = await CallSession.get(call_id)
        if not call:
            raise HTTPException(404, "Call not found")
        
        if call.receiver_id != receiver_id:
            raise HTTPException(403, "Not the call receiver")
        
        if call.status != CallStatus.RINGING:
            raise HTTPException(400, "Call is not ringing")
        
        # Update call
        call.status = CallStatus.REJECTED
        call.ended_at = datetime.utcnow()
        call.end_reason = reason or "Receiver rejected"
        call.updated_at = datetime.utcnow()
        await call.save()
        
        # Remove from active calls
        if call_id in cls.active_calls:
            del cls.active_calls[call_id]
        
        # Notify caller
        await cls.send_to_user(str(call.caller_id), {
            "type": "call_rejected",
            "call_id": call_id,
            "reason": call.end_reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Audit log
        await log_event(
            actor_user_id=receiver_id,
            actor_ip=None,
            action="call_rejected",
            details={"call_id": call_id, "reason": reason},
            severity="info"
        )
        
        return call
    
    @classmethod
    async def start_call(cls, call_id: str) -> CallSession:
        """Mark call as started (media flowing)."""
        call = await CallSession.get(call_id)
        if not call:
            raise HTTPException(404, "Call not found")
        
        if call.status != CallStatus.ACCEPTED:
            raise HTTPException(400, "Call not accepted yet")
        
        call.status = CallStatus.ACTIVE
        call.started_at = datetime.utcnow()
        call.updated_at = datetime.utcnow()
        await call.save()
        
        cls.active_calls[call_id] = call
        
        return call
    
    @classmethod
    async def end_call(
        cls,
        call_id: str,
        user_id: PydanticObjectId,
        reason: Optional[str] = None
    ) -> CallSession:
        """End an active call."""
        call = await CallSession.get(call_id)
        if not call:
            raise HTTPException(404, "Call not found")
        
        # Verify user is participant
        if call.caller_id != user_id and call.receiver_id != user_id:
            raise HTTPException(403, "Not a call participant")
        
        if call.status == CallStatus.ENDED:
            return call  # Already ended
        
        # Calculate duration
        if call.started_at:
            duration = (datetime.utcnow() - call.started_at).total_seconds()
            call.duration_seconds = int(duration)
        
        # Update call
        call.status = CallStatus.ENDED
        call.ended_at = datetime.utcnow()
        call.end_reason = reason or "User ended call"
        call.updated_at = datetime.utcnow()
        await call.save()
        
        # Remove from active calls
        if call_id in cls.active_calls:
            del cls.active_calls[call_id]
        
        # Notify other participant
        other_user_id = str(call.receiver_id if call.caller_id == user_id else call.caller_id)
        await cls.send_to_user(other_user_id, {
            "type": "call_ended",
            "call_id": call_id,
            "reason": call.end_reason,
            "duration": call.duration_seconds,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Audit log
        await log_event(
            actor_user_id=user_id,
            actor_ip=None,
            action="call_ended",
            details={
                "call_id": call_id,
                "duration_seconds": call.duration_seconds,
                "reason": reason
            },
            severity="info"
        )
        
        return call
    
    @classmethod
    async def add_ice_candidate(
        cls,
        call_id: str,
        user_id: PydanticObjectId,
        candidate: dict
    ):
        """Add ICE candidate to call and forward to other participant."""
        call = await CallSession.get(call_id)
        if not call:
            raise HTTPException(404, "Call not found")
        
        # Verify user is participant
        if call.caller_id != user_id and call.receiver_id != user_id:
            raise HTTPException(403, "Not a call participant")
        
        # Store candidate
        call.ice_candidates.append({
            "from_user_id": str(user_id),
            "candidate": candidate,
            "timestamp": datetime.utcnow().isoformat()
        })
        await call.save()
        
        # Forward to other participant
        other_user_id = str(call.receiver_id if call.caller_id == user_id else call.caller_id)
        await cls.send_to_user(other_user_id, {
            "type": "ice_candidate",
            "call_id": call_id,
            "candidate": candidate,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @classmethod
    async def flag_for_moderation(
        cls,
        call_id: str,
        reason: str,
        moderator_id: Optional[PydanticObjectId] = None
    ):
        """Flag a call for moderation review."""
        call = await CallSession.get(call_id)
        if not call:
            raise HTTPException(404, "Call not found")
        
        call.flagged_for_moderation = True
        call.moderation_notes = reason
        call.updated_at = datetime.utcnow()
        await call.save()
        
        # Audit log
        await log_event(
            actor_user_id=moderator_id,
            actor_ip=None,
            action="call_flagged_moderation",
            details={"call_id": call_id, "reason": reason},
            severity="warning"
        )
