from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime, timezone
from backend.models.user import User
from backend.models.message_v2 import MessageV2, MessageType, MessageStatus
from backend.services.messaging_v2 import get_messaging_service_v2, MessagingServiceV2
from backend.services.token_utils import verify_token
from backend.routes.auth import get_current_user

logger = logging.getLogger('routes.messaging_v2')

router = APIRouter(prefix="/api/v2/messages", tags=["Messaging V2"])

# WebSocket connection manager (mock mode)
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.typing_status: Dict[str, Dict[str, Any]] = {}  # {user_id: {partner_id: timestamp}}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.typing_status:
            del self.typing_status[user_id]
        logger.info(f"WebSocket disconnected: {user_id}")
    
    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
    
    async def broadcast_typing(self, sender_id: str, receiver_id: str, is_typing: bool):
        """Broadcast typing indicator"""
        if is_typing:
            self.typing_status[sender_id] = {
                "partner_id": receiver_id,
                "timestamp": datetime.now(timezone.utc)
            }
        else:
            if sender_id in self.typing_status:
                del self.typing_status[sender_id]
        
        # Send to receiver
        await self.send_personal_message(receiver_id, {
            "type": "typing_indicator",
            "sender_id": sender_id,
            "is_typing": is_typing
        })

manager = ConnectionManager()

# Pydantic models
class SendMessageRequest(BaseModel):
    receiver_id: str
    content: str
    message_type: MessageType = MessageType.TEXT
    attachments: List[Dict[str, Any]] = []

class MarkReadRequest(BaseModel):
    message_ids: List[str]

class MessageResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    message_type: str
    status: str
    created_at: str
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None

# HTTP Endpoints
@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    user: User = Depends(get_current_user),
    service: MessagingServiceV2 = Depends(get_messaging_service_v2)
):
    """Send a message to another user"""
    try:
        message = await service.send_message(
            sender_id=str(user.id),
            receiver_id=request.receiver_id,
            content=request.content,
            message_type=request.message_type,
            attachments=request.attachments
        )
        
        # Notify receiver via WebSocket if online
        await manager.send_personal_message(request.receiver_id, {
            "type": "new_message",
            "message_id": message.id,
            "sender_id": str(user.id),
            "content": message.content,
            "message_type": message.message_type.value,
            "created_at": message.created_at.isoformat()
        })
        
        return MessageResponse(
            id=message.id,
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            content=message.content,
            message_type=message.message_type.value,
            status=message.status.value,
            created_at=message.created_at.isoformat(),
            delivered_at=message.delivered_at.isoformat() if message.delivered_at else None,
            read_at=message.read_at.isoformat() if message.read_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send message")

@router.get("/conversation/{partner_id}")
async def get_conversation(
    partner_id: str,
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    service: MessagingServiceV2 = Depends(get_messaging_service_v2)
):
    """Get conversation history with a specific user"""
    messages = await service.fetch_conversation(
        user1_id=str(user.id),
        user2_id=partner_id,
        limit=limit,
        skip=skip
    )
    
    return {
        "messages": [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "message_type": msg.message_type.value,
                "status": msg.status.value,
                "created_at": msg.created_at.isoformat(),
                "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                "read_at": msg.read_at.isoformat() if msg.read_at else None
            }
            for msg in messages
        ],
        "total": len(messages)
    }

@router.get("/conversations")
async def list_conversations(
    user: User = Depends(get_current_user),
    service: MessagingServiceV2 = Depends(get_messaging_service_v2)
):
    """List all conversations for current user"""
    conversations = await service.list_conversations(str(user.id))
    return {"conversations": conversations}

@router.post("/mark-delivered/{message_id}")
async def mark_delivered(
    message_id: str,
    user: User = Depends(get_current_user),
    service: MessagingServiceV2 = Depends(get_messaging_service_v2)
):
    """Mark a message as delivered"""
    success = await service.mark_delivered(message_id, str(user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or already delivered")
    
    # Notify sender via WebSocket
    message = await MessageV2.find_one(MessageV2.id == message_id)
    if message:
        await manager.send_personal_message(message.sender_id, {
            "type": "message_status",
            "message_id": message_id,
            "status": "delivered",
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None
        })
    
    return {"success": True, "message": "Message marked as delivered"}

@router.post("/mark-read")
async def mark_read(
    request: MarkReadRequest,
    user: User = Depends(get_current_user),
    service: MessagingServiceV2 = Depends(get_messaging_service_v2)
):
    """Mark messages as read"""
    count = await service.mark_multiple_as_read(request.message_ids, str(user.id))
    
    # Notify senders via WebSocket
    for msg_id in request.message_ids:
        message = await MessageV2.find_one(MessageV2.id == msg_id)
        if message and message.status == MessageStatus.READ:
            await manager.send_personal_message(message.sender_id, {
                "type": "message_status",
                "message_id": msg_id,
                "status": "read",
                "read_at": message.read_at.isoformat() if message.read_at else None
            })
    
    return {"success": True, "marked_count": count}

@router.get("/unread-count")
async def get_unread_count(
    sender_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    service: MessagingServiceV2 = Depends(get_messaging_service_v2)
):
    """Get unread message count"""
    count = await service.get_unread_count(str(user.id), sender_id)
    return {"unread_count": count}

@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    user: User = Depends(get_current_user),
    service: MessagingServiceV2 = Depends(get_messaging_service_v2)
):
    """Delete a message (soft delete)"""
    success = await service.delete_message(message_id, str(user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or already deleted")
    return {"success": True, "message": "Message deleted"}

@router.get("/stats")
async def get_message_stats(
    user: User = Depends(get_current_user),
    service: MessagingServiceV2 = Depends(get_messaging_service_v2)
):
    """Get messaging statistics for current user"""
    stats = await service.get_message_stats(str(user.id))
    return stats

# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time messaging features"""
    user_id = None
    try:
        # Wait for authentication message
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
        await manager.connect(user_id, websocket)
        await websocket.send_json({"type": "connected", "user_id": user_id})
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            msg_type = message_data.get("type")
            
            if msg_type == "typing":
                # Broadcast typing indicator
                receiver_id = message_data.get("receiver_id")
                is_typing = message_data.get("is_typing", False)
                if receiver_id:
                    await manager.broadcast_typing(user_id, receiver_id, is_typing)
            
            elif msg_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown WebSocket message type: {msg_type}")
    
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if user_id:
            manager.disconnect(user_id)
        try:
            await websocket.close(code=1011)
        except:
            pass
