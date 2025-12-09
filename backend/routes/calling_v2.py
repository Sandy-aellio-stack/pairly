from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime, timezone
from backend.models.user import User
from backend.models.call_session_v2 import CallSessionV2, CallStatus
from backend.services.calling_service_v2 import get_calling_service_v2, CallingServiceV2
from backend.services.token_utils import verify_token
from backend.routes.auth import get_current_user

logger = logging.getLogger('routes.calling_v2')

router = APIRouter(prefix="/api/v2/calls", tags=["Calling V2"])

# Mock WebSocket connection manager for call signaling
class CallSignalingManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"Call WebSocket connected: {user_id}")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        logger.info(f"Call WebSocket disconnected: {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send signaling message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {user_id}: {e}")

signaling_manager = CallSignalingManager()

# Pydantic models
class InitiateCallRequest(BaseModel):
    receiver_id: str
    sdp_offer: Optional[str] = None

class AcceptCallRequest(BaseModel):
    sdp_answer: Optional[str] = None

class RejectCallRequest(BaseModel):
    reason: Optional[str] = "User rejected"

class EndCallRequest(BaseModel):
    reason: Optional[str] = "User ended call"

class ICECandidateRequest(BaseModel):
    candidate: Dict[str, Any]

class CallResponse(BaseModel):
    id: str
    caller_id: str
    receiver_id: str
    status: str
    initiated_at: str
    duration_seconds: int = 0
    credits_spent: int = 0

# HTTP Endpoints
@router.post("/initiate", response_model=CallResponse)
async def initiate_call(
    request: InitiateCallRequest,
    user: User = Depends(get_current_user),
    service: CallingServiceV2 = Depends(get_calling_service_v2)
):
    """Initiate a new call"""
    try:
        call_session = await service.initiate_call(
            caller_id=str(user.id),
            receiver_id=request.receiver_id,
            sdp_offer=request.sdp_offer
        )
        
        # Notify receiver via WebSocket
        await signaling_manager.send_to_user(request.receiver_id, {
            "type": "call_incoming",
            "call_id": call_session.id,
            "caller_id": str(user.id),
            "sdp_offer": request.sdp_offer
        })
        
        return CallResponse(
            id=call_session.id,
            caller_id=call_session.caller_id,
            receiver_id=call_session.receiver_id,
            status=call_session.status.value,
            initiated_at=call_session.initiated_at.isoformat(),
            duration_seconds=call_session.duration_seconds,
            credits_spent=call_session.credits_spent
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error initiating call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to initiate call")

@router.post("/{call_id}/accept", response_model=CallResponse)
async def accept_call(
    call_id: str,
    request: AcceptCallRequest,
    user: User = Depends(get_current_user),
    service: CallingServiceV2 = Depends(get_calling_service_v2)
):
    """Accept an incoming call"""
    try:
        call_session = await service.accept_call(
            call_id=call_id,
            receiver_id=str(user.id),
            sdp_answer=request.sdp_answer
        )
        
        # Notify caller via WebSocket
        await signaling_manager.send_to_user(call_session.caller_id, {
            "type": "call_accepted",
            "call_id": call_id,
            "receiver_id": str(user.id),
            "sdp_answer": request.sdp_answer
        })
        
        return CallResponse(
            id=call_session.id,
            caller_id=call_session.caller_id,
            receiver_id=call_session.receiver_id,
            status=call_session.status.value,
            initiated_at=call_session.initiated_at.isoformat(),
            duration_seconds=call_session.duration_seconds,
            credits_spent=call_session.credits_spent
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error accepting call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to accept call")

@router.post("/{call_id}/reject")
async def reject_call(
    call_id: str,
    request: RejectCallRequest,
    user: User = Depends(get_current_user),
    service: CallingServiceV2 = Depends(get_calling_service_v2)
):
    """Reject an incoming call"""
    try:
        call_session = await service.reject_call(
            call_id=call_id,
            receiver_id=str(user.id),
            reason=request.reason
        )
        
        # Notify caller via WebSocket
        await signaling_manager.send_to_user(call_session.caller_id, {
            "type": "call_rejected",
            "call_id": call_id,
            "receiver_id": str(user.id),
            "reason": request.reason
        })
        
        return {"success": True, "call_id": call_id, "status": "rejected"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reject call")

@router.post("/{call_id}/end")
async def end_call(
    call_id: str,
    request: EndCallRequest,
    user: User = Depends(get_current_user),
    service: CallingServiceV2 = Depends(get_calling_service_v2)
):
    """End an active call"""
    try:
        call_session = await service.end_call(
            call_id=call_id,
            user_id=str(user.id),
            reason=request.reason
        )
        
        # Notify other party via WebSocket
        other_user_id = call_session.receiver_id if str(user.id) == call_session.caller_id else call_session.caller_id
        await signaling_manager.send_to_user(other_user_id, {
            "type": "call_ended",
            "call_id": call_id,
            "ended_by": str(user.id),
            "reason": request.reason,
            "duration_seconds": call_session.duration_seconds
        })
        
        return {
            "success": True,
            "call_id": call_id,
            "status": "ended",
            "duration_seconds": call_session.duration_seconds,
            "credits_spent": call_session.credits_spent
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error ending call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to end call")

@router.post("/{call_id}/ice")
async def add_ice_candidate(
    call_id: str,
    request: ICECandidateRequest,
    user: User = Depends(get_current_user),
    service: CallingServiceV2 = Depends(get_calling_service_v2)
):
    """Add ICE candidate for WebRTC signaling (mock)"""
    try:
        call_session = await service.add_ice_candidate(
            call_id=call_id,
            user_id=str(user.id),
            candidate=request.candidate
        )
        
        # Forward ICE candidate to other party
        other_user_id = call_session.receiver_id if str(user.id) == call_session.caller_id else call_session.caller_id
        await signaling_manager.send_to_user(other_user_id, {
            "type": "ice_candidate",
            "call_id": call_id,
            "from_user_id": str(user.id),
            "candidate": request.candidate
        })
        
        return {"success": True, "message": "ICE candidate added"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding ICE candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add ICE candidate")

@router.get("/history")
async def get_call_history(
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    service: CallingServiceV2 = Depends(get_calling_service_v2)
):
    """Get call history for current user"""
    calls = await service.get_call_history(
        user_id=str(user.id),
        limit=limit,
        skip=skip
    )
    
    return {
        "calls": [
            {
                "id": call.id,
                "caller_id": call.caller_id,
                "receiver_id": call.receiver_id,
                "status": call.status.value,
                "initiated_at": call.initiated_at.isoformat(),
                "duration_seconds": call.duration_seconds,
                "credits_spent": call.credits_spent,
                "disconnect_reason": call.disconnect_reason
            }
            for call in calls
        ],
        "total": len(calls)
    }

@router.get("/stats")
async def get_call_stats(
    user: User = Depends(get_current_user),
    service: CallingServiceV2 = Depends(get_calling_service_v2)
):
    """Get calling statistics for current user"""
    stats = await service.get_call_stats(str(user.id))
    return stats

@router.get("/{call_id}")
async def get_call_details(
    call_id: str,
    user: User = Depends(get_current_user)
):
    """Get details of a specific call"""
    call = await CallSessionV2.find_one(CallSessionV2.id == call_id)
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Verify user is part of the call
    if str(user.id) not in [call.caller_id, call.receiver_id]:
        raise HTTPException(status_code=403, detail="Unauthorized to view this call")
    
    return {
        "id": call.id,
        "caller_id": call.caller_id,
        "receiver_id": call.receiver_id,
        "status": call.status.value,
        "initiated_at": call.initiated_at.isoformat(),
        "connected_at": call.connected_at.isoformat() if call.connected_at else None,
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
        "duration_seconds": call.duration_seconds,
        "credits_spent": call.credits_spent,
        "disconnect_reason": call.disconnect_reason
    }

# WebSocket endpoint for call signaling
@router.websocket("/ws")
async def websocket_call_signaling(websocket: WebSocket):
    """WebSocket endpoint for real-time call signaling"""
    user_id = None
    try:
        # Wait for authentication
        await websocket.accept()
        auth_data = await websocket.receive_text()
        auth_json = json.loads(auth_data)
        
        token = auth_json.get("token")
        if not token:
            await websocket.send_json({"type": "error", "message": "No token provided"})
            await websocket.close(code=1008)
            return
        
        # Verify token
        try:
            payload = verify_token(token, "access")
            user_id = payload.get("sub")
        except Exception as e:
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close(code=1008)
            return
        
        # Register connection
        await signaling_manager.connect(user_id, websocket)
        await websocket.send_json({"type": "connected", "user_id": user_id})
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            msg_type = message_data.get("type")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                logger.debug(f"Received call signaling message: {msg_type}")
    
    except WebSocketDisconnect:
        if user_id:
            signaling_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Call WebSocket error: {e}", exc_info=True)
        if user_id:
            signaling_manager.disconnect(user_id)
        try:
            await websocket.close(code=1011)
        except:
            pass
