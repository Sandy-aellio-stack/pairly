from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
import logging
from backend.models.user import User
from backend.models.message import Message
from backend.models.profile import Profile
from backend.routes.profiles import get_current_user
from backend.services.ws_rate_limiter import WSRateLimiter
from backend.services.audit import log_event
from backend.services.credits_service import CreditsService
from backend.services.token_utils import verify_token
from typing import Dict
import json
from datetime import datetime, timezone
from beanie import PydanticObjectId

logger = logging.getLogger('routes.messaging')

router = APIRouter(prefix="/api/legacy/messages", tags=["Legacy Messaging"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
ws_rate_limiter = WSRateLimiter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connection_id = f"ws_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    logger.info(
        "WebSocket connection initiated",
        extra={"event": "ws_connect", "user_id": user_id, "connection_id": connection_id}
    )
    
    try:
        # Authenticate via first message
        auth_data = await websocket.receive_text()
        auth_json = json.loads(auth_data)
        token = auth_json.get("token")
        
        if not token:
            logger.warning("WebSocket auth failed: no token", extra={"user_id": user_id})
            await websocket.close(code=1008)
            return
        
        # Verify JWT token properly
        try:
            payload = verify_token(token, "access")
            token_user_id = payload.get("sub")
            
            # Match token user_id to websocket user_id
            if token_user_id != user_id:
                logger.warning(
                    "WebSocket auth failed: user_id mismatch",
                    extra={"token_user_id": token_user_id, "ws_user_id": user_id}
                )
                await websocket.close(code=1008)
                return
        except HTTPException as e:
            logger.warning(f"WebSocket auth failed: {e.detail}", extra={"user_id": user_id})
            await websocket.close(code=1008)
            return
        
        # Get user from database
        user = await User.get(PydanticObjectId(user_id))
        if not user:
            logger.warning("WebSocket auth failed: user not found", extra={"user_id": user_id})
            await websocket.close(code=1008)
            return
        
        # Store connection
        active_connections[user_id] = websocket
        
        logger.info(
            "WebSocket authenticated successfully",
            extra={"event": "ws_authenticated", "user_id": user_id, "connection_id": connection_id}
        )
        
        # Send confirmation
        await websocket.send_json({"type": "connected", "user_id": user_id})
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Rate limit check
            if not await ws_rate_limiter.allow_message(user_id):
                logger.warning("WebSocket rate limit exceeded", extra={"user_id": user_id})
                await websocket.send_json({
                    "type": "error",
                    "message": "Rate limit exceeded"
                })
                continue
            
            # Process message
            if message_data.get("type") == "chat_message":
                recipient_id = message_data.get("recipient_id")
                content = message_data.get("content")
                
                # Use CreditsService for credit handling
                success = await CreditsService.charge_for_message(
                    PydanticObjectId(user_id),
                    PydanticObjectId(recipient_id)
                )
                
                if not success:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Insufficient credits"
                    })
                    continue
                
                # Save message
                message = Message(
                    sender_id=PydanticObjectId(user_id),
                    recipient_id=PydanticObjectId(recipient_id),
                    content=content,
                    sent_at=datetime.now(timezone.utc)
                )
                await message.insert()
                
                logger.info(
                    "Message sent",
                    extra={
                        "event": "message_sent",
                        "sender_id": user_id,
                        "recipient_id": recipient_id,
                        "message_id": str(message.id)
                    }
                )
                
                # Send to recipient if online
                if recipient_id in active_connections:
                    recipient_ws = active_connections[recipient_id]
                    await recipient_ws.send_json({
                        "type": "new_message",
                        "message_id": str(message.id),
                        "sender_id": user_id,
                        "content": content,
                        "sent_at": message.sent_at.isoformat()
                    })
                
                # Confirm to sender
                await websocket.send_json({
                    "type": "message_sent",
                    "message_id": str(message.id)
                })
                
                await log_event(
                    actor_user_id=PydanticObjectId(user_id),
                    action="message_sent",
                    details={"recipient_id": recipient_id},
                    severity="info"
                )
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", extra={"user_id": user_id})
        if user_id in active_connections:
            del active_connections[user_id]
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", extra={"user_id": user_id}, exc_info=True)
        if user_id in active_connections:
            del active_connections[user_id]
        await websocket.close(code=1011)

@router.get("/history/{other_user_id}")
async def get_message_history(
    other_user_id: str,
    user: User = Depends(get_current_user)
):
    """Get message history with another user"""
    messages = await Message.find(
        {
            "$or": [
                {"sender_id": user.id, "recipient_id": PydanticObjectId(other_user_id)},
                {"sender_id": PydanticObjectId(other_user_id), "recipient_id": user.id}
            ]
        }
    ).sort("+sent_at").to_list()
    
    return [{"id": str(m.id), "sender_id": str(m.sender_id), "recipient_id": str(m.recipient_id), "content": m.content, "sent_at": m.sent_at.isoformat()} for m in messages]

@router.get("/conversations")
async def get_conversations(user: User = Depends(get_current_user)):
    """Get list of conversations"""
    # Get unique users the current user has messaged with
    messages = await Message.find(
        {
            "$or": [
                {"sender_id": user.id},
                {"recipient_id": user.id}
            ]
        }
    ).to_list()
    
    # Extract unique user IDs
    user_ids = set()
    for msg in messages:
        if msg.sender_id != user.id:
            user_ids.add(msg.sender_id)
        if msg.recipient_id != user.id:
            user_ids.add(msg.recipient_id)
    
    # Get profiles
    profiles = await Profile.find({"user_id": {"$in": list(user_ids)}}).to_list()
    
    return [{"user_id": str(p.user_id), "display_name": p.display_name, "profile_picture_url": p.profile_picture_url, "is_online": p.is_online} for p in profiles]
