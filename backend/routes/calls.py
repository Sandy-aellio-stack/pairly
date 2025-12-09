"""
Call Routes - WebRTC calling API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from beanie import PydanticObjectId
from datetime import datetime, timezone

from backend.models.user import User, Role
from backend.models.call_session import CallSession, CallStatus
from backend.routes.auth import get_current_user
from backend.services.call_signaling import CallSignalingService
from backend.services.call_billing_worker import billing_tick_task, finalize_call_task
import json

router = APIRouter(prefix="/api/call", tags=["calls"])


# ===== ICE Configuration =====

@router.get("/ice")
async def get_ice_config():
    """
    Get ICE server configuration for WebRTC.
    
    Returns STUN/TURN server URLs.
    """
    # Default: Public Google STUN servers
    # In production, add your own TURN server (Coturn)
    return {
        "iceServers": [
            {
                "urls": [
                    "stun:stun.l.google.com:19302",
                    "stun:stun1.l.google.com:19302"
                ]
            },
            # Uncomment when you have a TURN server
            # {
            #     "urls": "turn:your-turn-server.com:3478",
            #     "username": "turn_user",
            #     "credential": "turn_password"
            # }
        ],
        "iceTransportPolicy": "all",
        "iceCandidatePoolSize": 10
    }


# ===== Call Initiation =====

class StartCallRequest(BaseModel):
    receiver_id: str
    offer_sdp: str


@router.post("/start")
async def start_call(
    req: StartCallRequest,
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Initiate a new call to another user.
    
    Creates call session and sends offer to receiver.
    """
    receiver_oid = PydanticObjectId(req.receiver_id)
    
    # Check caller has enough credits (at least 1 minute)
    from backend.models.call_session import CallSession as CS
    min_credits = 5  # Default cost per minute
    
    if user.credits_balance < min_credits:
        raise HTTPException(400, f"Insufficient credits. Need at least {min_credits} credits to start a call.")
    
    # Check receiver exists and is not the caller
    receiver = await User.get(receiver_oid)
    if not receiver:
        raise HTTPException(404, "Receiver not found")
    
    if receiver.id == user.id:
        raise HTTPException(400, "Cannot call yourself")
    
    # Get client IP
    client_ip = request.client.host if request.client else None
    
    # Initiate call
    call = await CallSignalingService.initiate_call(
        caller_id=user.id,
        receiver_id=receiver_oid,
        offer_sdp=req.offer_sdp,
        caller_ip=client_ip
    )
    
    return {
        "call_id": str(call.id),
        "status": call.status,
        "receiver_id": req.receiver_id,
        "initiated_at": call.initiated_at.isoformat()
    }


# ===== Call Acceptance =====

class AcceptCallRequest(BaseModel):
    call_id: str
    answer_sdp: str


@router.post("/accept")
async def accept_call(
    req: AcceptCallRequest,
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Accept an incoming call.
    
    Sends answer SDP to caller and marks call as accepted.
    """
    client_ip = request.client.host if request.client else None
    
    call = await CallSignalingService.accept_call(
        call_id=req.call_id,
        receiver_id=user.id,
        answer_sdp=req.answer_sdp,
        receiver_ip=client_ip
    )
    
    return {
        "call_id": req.call_id,
        "status": call.status,
        "accepted_at": call.accepted_at.isoformat() if call.accepted_at else None
    }


# ===== Call Rejection =====

class RejectCallRequest(BaseModel):
    call_id: str
    reason: Optional[str] = None


@router.post("/reject")
async def reject_call(
    req: RejectCallRequest,
    user: User = Depends(get_current_user)
):
    """
    Reject an incoming call.
    """
    call = await CallSignalingService.reject_call(
        call_id=req.call_id,
        receiver_id=user.id,
        reason=req.reason
    )
    
    return {
        "call_id": req.call_id,
        "status": call.status,
        "rejected_at": call.ended_at.isoformat() if call.ended_at else None
    }


# ===== Call Start (Media Connected) =====

class MediaConnectedRequest(BaseModel):
    call_id: str


@router.post("/connected")
async def media_connected(
    req: MediaConnectedRequest,
    user: User = Depends(get_current_user)
):
    """
    Mark call as active (media started flowing).
    
    Starts billing ticker.
    """
    call = await CallSignalingService.start_call(req.call_id)
    
    # Start billing ticker (first tick in 60 seconds)
    billing_tick_task.apply_async(args=[req.call_id], countdown=60)
    
    return {
        "call_id": req.call_id,
        "status": call.status,
        "started_at": call.started_at.isoformat() if call.started_at else None
    }


# ===== Call End =====

class EndCallRequest(BaseModel):
    call_id: str
    reason: Optional[str] = None


@router.post("/end")
async def end_call(
    req: EndCallRequest,
    user: User = Depends(get_current_user)
):
    """
    End an active call.
    
    Finalizes billing and logs call details.
    """
    call = await CallSignalingService.end_call(
        call_id=req.call_id,
        user_id=user.id,
        reason=req.reason
    )
    
    # Queue finalization task
    finalize_call_task.apply_async(args=[req.call_id], countdown=5)
    
    return {
        "call_id": req.call_id,
        "status": call.status,
        "duration_seconds": call.duration_seconds,
        "total_cost": call.total_cost,
        "ended_at": call.ended_at.isoformat() if call.ended_at else None
    }


# ===== Call Logs =====

@router.get("/logs")
async def get_call_logs(
    limit: int = 50,
    skip: int = 0,
    user: User = Depends(get_current_user)
):
    """
    Get call history for current user.
    """
    # Get calls where user is caller or receiver
    calls_as_caller = await CallSession.find(
        CallSession.caller_id == user.id
    ).sort("-created_at").skip(skip).limit(limit).to_list()
    
    calls_as_receiver = await CallSession.find(
        CallSession.receiver_id == user.id
    ).sort("-created_at").skip(skip).limit(limit).to_list()
    
    # Merge and sort
    all_calls = calls_as_caller + calls_as_receiver
    all_calls.sort(key=lambda c: c.created_at, reverse=True)
    all_calls = all_calls[:limit]
    
    return {
        "calls": [
            {
                "call_id": str(call.id),
                "caller_id": str(call.caller_id),
                "receiver_id": str(call.receiver_id),
                "status": call.status,
                "duration_seconds": call.duration_seconds,
                "total_cost": call.total_cost,
                "initiated_at": call.initiated_at.isoformat(),
                "started_at": call.started_at.isoformat() if call.started_at else None,
                "ended_at": call.ended_at.isoformat() if call.ended_at else None,
                "end_reason": call.end_reason,
                "quality_rating": call.quality_rating
            }
            for call in all_calls
        ],
        "total": len(all_calls),
        "limit": limit,
        "skip": skip
    }


# ===== Admin: Flag for Moderation =====

class FlagCallRequest(BaseModel):
    call_id: str
    reason: str


@router.post("/admin/flag")
async def flag_call(
    req: FlagCallRequest,
    admin: User = Depends(get_current_user)
):
    """
    Flag a call for moderation review.
    
    Admin only.
    """
    if admin.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    await CallSignalingService.flag_for_moderation(
        call_id=req.call_id,
        reason=req.reason,
        moderator_id=admin.id
    )
    
    return {
        "call_id": req.call_id,
        "flagged": True,
        "reason": req.reason
    }


# ===== WebSocket Signaling =====

@router.websocket("/ws/{user_id}")
async def call_signaling_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for call signaling.
    
    Handles:
    - ICE candidate exchange
    - Call state notifications
    - Real-time signaling events
    """
    await websocket.accept()
    
    try:
        # Authenticate (simplified - in production use proper JWT)
        auth_data = await websocket.receive_text()
        auth_json = json.loads(auth_data)
        token = auth_json.get("token")
        
        if not token:
            await websocket.close(code=1008)
            return
        
        # Register connection
        await CallSignalingService.register_connection(user_id, websocket)
        
        # Send confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "ice_candidate":
                # Forward ICE candidate to other participant
                call_id = message.get("call_id")
                candidate = message.get("candidate")
                
                await CallSignalingService.add_ice_candidate(
                    call_id=call_id,
                    user_id=PydanticObjectId(user_id),
                    candidate=candidate
                )
            
            elif msg_type == "ping":
                # Keep-alive
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    except WebSocketDisconnect:
        await CallSignalingService.unregister_connection(user_id)
    
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        await CallSignalingService.unregister_connection(user_id)
        try:
            await websocket.close(code=1011)
        except:
            pass
