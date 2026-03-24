"""
Luveloop Messages API
REST endpoints for messaging with WebSocket integration.

IMPORTANT: REST API is the PRIMARY method for sending messages.
It guarantees:
- Database persistence (source of truth)
- Credit deduction
- Transaction logging

WebSocket is used for:
- Real-time delivery notifications
- Typing indicators
- Read receipts

Fallback Behavior:
- If WebSocket is unavailable, messages are still sent via REST
- Client polls /api/messages/{user_id} for message history
- Unread counts available via /api/messages/conversations
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Body, UploadFile, File, Form
from pydantic import BaseModel, Field
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_message_service import MessageService, SendMessageRequest
from backend.socket_server import sio, emit_message_to_user, emit_notification_to_user, emit_read_receipt
from backend.core.redis_pubsub import redis_pubsub
import logging
import base64
import time
import traceback

router = APIRouter(prefix="/api/messages", tags=["Messages"])
logger = logging.getLogger("messages")



@router.post("/start-conversation")
async def start_conversation(
    body: dict = Body(...), 
    user: TBUser = Depends(get_current_user)
):
    """Initialize a conversation with another user"""
    receiver_id = body.get("receiver_id")
    if not receiver_id:
        raise HTTPException(status_code=400, detail="receiver_id is required")
    return await MessageService.start_conversation(str(user.id), receiver_id)


class CreateConversationRequest(BaseModel):
    target_user_id: str = Field(..., description="ID of user to create conversation with")


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify routing works"""
    return {"message": "Messages router is working", "status": "ok"}


@router.post("/create-or-get")
async def create_or_get_conversation(
    request: CreateConversationRequest,
    user: TBUser = Depends(get_current_user)
):
    """
    Create a new conversation or get existing one between current user and target user.
    This is the CENTRAL API for all conversation creation.
    """
    from backend.utils.objectid_utils import validate_object_id
    from backend.models.tb_message import TBConversation, TBUser
    from datetime import datetime, timezone
    import logging
    
    logger.info(f"=== CONVERSATION CREATION REQUEST ===")
    logger.info(f"Current user: {str(user.id)}")
    logger.info(f"Target user: {request.target_user_id}")
    logger.info(f"Request method: POST")
    logger.info(f"Request body: {request}")
    
    # Validate target user ID
    target_user_oid = validate_object_id(request.target_user_id, "Target user")
    current_user_oid = user.id
    
    if target_user_oid == current_user_oid:
        logger.warning("User tried to create conversation with themselves")
        raise HTTPException(status_code=400, detail="Cannot chat with yourself")
    
    # Check if target user exists
    target_user = await TBUser.get(target_user_oid)
    if not target_user:
        logger.error(f"Target user not found: {target_user_oid}")
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Check if conversation already exists using $all query
    existing_conversation = await TBConversation.find_one({
        "participants": {
            "$all": [current_user_oid, target_user_oid]
        }
    })
    
    logger.info(f"Existing conversation found: {existing_conversation is not None}")
    
    if existing_conversation:
        logger.info(f"Returning existing conversation: {str(existing_conversation.id)}")
        return {
            "_id": str(existing_conversation.id),
            "conversation_id": str(existing_conversation.id),
            "participants": [str(p) for p in existing_conversation.participants],
            "last_message": existing_conversation.last_message,
            "last_message_at": existing_conversation.last_message_at.isoformat() if existing_conversation.last_message_at else None,
            "created_at": existing_conversation.created_at.isoformat(),
            "updated_at": existing_conversation.updated_at.isoformat(),
            "existing": True,
            "user": {
                "id": str(target_user.id),
                "name": target_user.name,
                "profile_picture": target_user.profile_pictures[0] if target_user.profile_pictures else None,
                "is_online": target_user.is_online,
                "status": "suspended" if target_user.is_suspended else "active"
            }
        }
    else:
        # Create new conversation
        new_conversation = TBConversation(
            participants=sorted([current_user_oid, target_user_oid]),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_message="",
            last_message_at=None
        )
        await new_conversation.insert()
        
        logger.info(f"New conversation created: {str(new_conversation.id)}")
        
        return {
            "_id": str(new_conversation.id),
            "conversation_id": str(new_conversation.id),
            "participants": [str(current_user_oid), str(target_user_oid)],
            "last_message": "",
            "last_message_at": None,
            "created_at": new_conversation.created_at.isoformat(),
            "updated_at": new_conversation.updated_at.isoformat(),
            "existing": False,
            "user": {
                "id": str(target_user.id),
                "name": target_user.name,
                "profile_picture": target_user.profile_pictures[0] if target_user.profile_pictures else None,
                "is_online": target_user.is_online,
                "status": "suspended" if target_user.is_suspended else "active"
            }
        }


@router.post("/send")
async def send_message(data: SendMessageRequest, user: TBUser = Depends(get_current_user)):
    """
    Send a message to another user.
    
    This is the PRIMARY method for sending messages.
    - Costs 1 credit per message
    - Returns 402 if insufficient credits
    - Database is the source of truth
    - Real-time delivery via WebSocket/Redis (if available)
    
    Fallback: If WebSocket fails, message is still persisted.
    Client should poll GET /api/messages/{other_user_id} as backup.
    """
    result = await MessageService.send_message(
        sender_id=str(user.id),
        data=data
    )

    # Attempt real-time delivery (non-blocking, fail-safe)
    try:
        message_data = {
            'id': result['message_id'],
            'sender_id': str(user.id),
            'receiver_id': data.receiver_id,
            'content': data.content,
            'is_read': False,
            'created_at': result['created_at']
        }

        notification_data = {
            'message_id': result['message_id'],
            'sender_id': str(user.id),
            'sender_name': user.name,
            'content_preview': data.content[:50],
            'created_at': result['created_at']
        }

        # Publish via Redis Pub/Sub for cross-server delivery
        await redis_pubsub.publish_new_message(data.receiver_id, message_data)
        # await redis_pubsub.publish_message_notification(data.receiver_id, notification_data)

        # Also emit locally via Socket.IO - SYNCED to user:{id}
        await sio.emit('message:new', message_data, room=f"user:{data.receiver_id}")
        await sio.emit('message:new', message_data, room=f"user:{str(user.id)}")
        # await sio.emit('message:new-notification', notification_data, room=f"user_{data.receiver_id}")

        logger.debug(f"Message {result['message_id']} delivered in real-time")

    except Exception as e:
        # Don't fail the request if WebSocket/Redis fails
        # Message is already persisted in database
        logger.warning(f"Real-time delivery failed (message persisted): {e}")

    # Create DB notification if receiver is offline and has notifications enabled
    try:
        receiver = await TBUser.get(data.receiver_id)
        if receiver and not receiver.is_online:
            notify_msgs = True
            if receiver.settings and receiver.settings.notifications:
                notify_msgs = receiver.settings.notifications.messages
            if notify_msgs:
                from backend.routes.tb_notifications import create_notification
                await create_notification(
                    user_id=data.receiver_id,
                    title=f"New message from {user.name}",
                    body=data.content[:100],
                    notification_type="message"
                )
    except Exception as e:
        logger.debug(f"Notification creation failed (non-critical): {e}")

    return result


@router.get("/conversation/{conversation_id}")
async def get_single_conversation(conversation_id: str, user: TBUser = Depends(get_current_user)):
    """Fetch a single conversation by ID to get the other user's ID for direct chat links"""
    from backend.models.tb_message import TBConversation
    from backend.utils.objectid_utils import validate_object_id
    from beanie import PydanticObjectId
    
    try:
        conv_oid = PydanticObjectId(conversation_id)
        conv = await TBConversation.get(conv_oid)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        user_oid = user.id
        if user_oid not in conv.participants:
            raise HTTPException(status_code=403, detail="Not authorized to view this conversation")
            
        # Get the other user
        other_user_oids = [p for p in conv.participants if p != user_oid]
        if not other_user_oids:
            return {"conversation": None}
            
        other_user = await TBUser.get(other_user_oids[0])
        
        return {
            "conversation_id": str(conv.id),
            "user": {
                "id": str(other_user.id) if other_user else None,
                "name": other_user.name if other_user else "Unknown User",
                "profile_picture": (other_user.profile_pictures[0] if other_user.profile_pictures else None) if other_user else None,
            }
        }
    except Exception as e:
        logger.error(f"Error fetching conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation")


@router.get("/conversations")
async def get_conversations(user: TBUser = Depends(get_current_user)):
    """
    Get all conversations for current user.
    """
    print(f"[GET CONVERSATIONS] userId: {str(user.id)}")
    
    try:
        conversations = await MessageService.get_conversations(str(user.id))
        logger.info(f"[GET CONVERSATIONS] Returning {len(conversations)} conversations for user {str(user.id)}")
        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        logger.error(f"[CONV API ERROR] Backend failure: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load conversations: {str(e)}")


@router.get("/{other_user_id}")
async def get_messages(
    other_user_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: str = Query(None, description="Message ID to fetch before (for pagination)"),
    user: TBUser = Depends(get_current_user)
):
    """
    Get messages with a specific user.
    
    This is the FALLBACK method for receiving messages.
    Use when WebSocket is unavailable or for initial load.
    
    Pagination:
    - Use 'before' parameter with last message_id for older messages
    - Returns messages in reverse chronological order
    """
    messages = await MessageService.get_messages(
        user_id=str(user.id),
        other_user_id=other_user_id,
        limit=limit
    )
    return {
        "messages": messages,
        "count": len(messages),
        "has_more": len(messages) == limit
    }


@router.post("/read/{other_user_id}")
async def mark_messages_read(other_user_id: str, user: TBUser = Depends(get_current_user)):
    """
    Mark all messages from a user as read.
    
    This is the PRIMARY method for read receipts.
    - Updates database (source of truth)
    - Emits real-time event to sender (if connected)
    
    Fallback: If WebSocket fails, database is still updated.
    """
    result = await MessageService.mark_messages_read(
        user_id=str(user.id),
        other_user_id=other_user_id
    )

    # Attempt real-time notification (non-blocking)
    try:
        from datetime import datetime, timezone
        
        # Publish via Redis for cross-server delivery
        await redis_pubsub.publish_read_receipt(
            other_user_id,
            str(user.id),
            result['marked_read']
        )

        # Also emit locally - SYNCED to user:{id}
        await sio.emit('message:read', {
            'reader_id': str(user.id),
            'sender_id': other_user_id,
            'count': result['marked_read'],
            'read_at': datetime.now(timezone.utc).isoformat()
        }, room=f"user:{other_user_id}")

    except Exception as e:
        logger.warning(f"Failed to emit read receipt (database updated): {e}")

    return result


@router.get("/unread/count")
async def get_unread_count(user: TBUser = Depends(get_current_user)):
    """
    Get total unread message count across all conversations.
    
    Used for:
    - Badge count on messages tab
    - Fallback when WebSocket unavailable
    """
    from backend.models.tb_message import TBConversation
    
    total_unread = 0
    # FIX: Query with PydanticObjectId, not string
    from beanie import PydanticObjectId
    conversations = await TBConversation.find(
        {"participants": PydanticObjectId(user.id)}
    ).to_list()
    
    for conv in conversations:
        unread = conv.unread_count.get(str(user.id), 0)
        total_unread += unread
    
    return {
        "total_unread": total_unread
    }


@router.post("/typing/{receiver_id}")
async def send_typing_indicator(receiver_id: str, user: TBUser = Depends(get_current_user)):
    """
    Send typing indicator via REST API.
    
    Alternative to WebSocket typing event.
    Use when WebSocket is unavailable.
    """
    try:
        # Publish via Redis
        await redis_pubsub.publish_typing(receiver_id, str(user.id), is_typing=True)
        
        # Also emit via Socket.IO - SYNCED to user:{id}
        from datetime import datetime, timezone
        await sio.emit('message:typing', {
            'user_id': str(user.id),
            'receiver_id': receiver_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=f"user:{receiver_id}")
        
        return {"success": True}
    except Exception as e:
        logger.warning(f"Failed to send typing indicator: {e}")
        return {"success": False, "error": "Failed to send"}


@router.post("/stop-typing/{receiver_id}")
async def send_stop_typing_indicator(receiver_id: str, user: TBUser = Depends(get_current_user)):
    """
    Send stop typing indicator via REST API.
    
    Alternative to WebSocket stop_typing event.
    """
    try:
        # Publish via Redis
        await redis_pubsub.publish_typing(receiver_id, str(user.id), is_typing=False)
        
        # Also emit via Socket.IO - SYNCED to user:{id}
        from datetime import datetime, timezone
        await sio.emit('message:stop-typing', {
            'user_id': str(user.id),
            'receiver_id': receiver_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=f"user:{receiver_id}")
        
        return {"success": True}
    except Exception as e:
        logger.warning(f"Failed to send stop typing indicator: {e}")
        return {"success": False, "error": "Failed to send"}


@router.post("/{other_user_id}/read")
async def mark_messages_read_by_path(other_user_id: str, user: TBUser = Depends(get_current_user)):
    """Mark messages from a specific user as read"""
    from backend.models.tb_message import TBMessage
    from datetime import datetime, timezone
    try:
        await TBMessage.find(
            {"sender_id": user.id, "receiver_id": user.id, "is_read": False}
        ).update_many({"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}})
        return await MessageService.mark_messages_read(str(user.id), other_user_id)
    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark messages as read")


@router.post("/{other_user_id}")
async def mark_messages_read_post(other_user_id: str, user: TBUser = Depends(get_current_user)):
    """Mark messages from a specific user as read - POST version"""
    return await MessageService.mark_messages_read(str(user.id), other_user_id)


@router.post("/upload-image")
async def upload_image_message(
    receiver_id: str = Body(...),
    file: UploadFile = File(...),
    user: TBUser = Depends(get_current_user)
):
    """
    Upload an image and send it as a message.
    Accepts multipart/form-data with 'file' (the image) and 'receiver_id'.
    Returns the saved message with image_url.
    """
    # Validate content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    content = await file.read()

    # 5 MB limit
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be less than 5MB")

    # Reset file pointer
    await file.seek(0)
    
    # Upload to S3/R2/Supabase
    from backend.services.storage_service import StorageService
    image_url = await StorageService.upload_file(file, directory="messages")

    # Save as a message with type="image"
    from backend.services.tb_message_service import SendMessageRequest
    msg_request = SendMessageRequest(
        receiver_id=receiver_id,
        content=image_url,
        message_type="image"
    )
    result = await MessageService.send_message(
        sender_id=str(user.id),
        data=msg_request
    )

    message_data = {
        "id": result["message_id"],
        "sender_id": str(user.id),
        "receiver_id": receiver_id,
        "content": image_url,
        "message_type": "image",
        "image_url": image_url,
        "is_read": False,
        "created_at": result["created_at"],
    }

    # Broadcast to both parties - SYNCED to user:{id}
    try:
        await sio.emit("message:new", message_data, room=f"user:{receiver_id}")
        await sio.emit("message:new", message_data, room=f"user:{str(user.id)}")
        await redis_pubsub.publish_new_message(receiver_id, message_data)
    except Exception as e:
        logger.warning(f"Real-time delivery of image message failed (persisted): {e}")

    return {
        "message_id": result["message_id"],
        "image_url": image_url,
        "created_at": result["created_at"],
    }


@router.post("/upload")
async def upload_image_message_new(
    receiver_id: str = Form(...),
    image: UploadFile = File(...),
    user: TBUser = Depends(get_current_user)
):
    """
    Upload an image and send it as a message (Form-based).
    Accepts multipart/form-data with 'image' and 'receiver_id'.
    Returns the saved message with image_url.
    """
    from backend.utils.objectid_utils import validate_object_id
    try:
        receiver_oid = validate_object_id(receiver_id, "Receiver")
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid receiver_id format")
        
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    content = await image.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be less than 5MB")

    await image.seek(0)
    from backend.services.storage_service import StorageService
    image_url = await StorageService.upload_file(image, directory="messages")

    from backend.services.tb_message_service import SendMessageRequest
    msg_request = SendMessageRequest(
        receiver_id=receiver_id,
        content=image_url,
        message_type="image"
    )
    result = await MessageService.send_message(
        sender_id=str(user.id),
        data=msg_request
    )

    message_data = {
        "id": result["message_id"],
        "sender_id": str(user.id),
        "receiver_id": receiver_id,
        "content": image_url,
        "message_type": "image",
        "image_url": image_url,
        "is_read": False,
        "created_at": result["created_at"],
    }

    try:
        data = { **message_data, "status": "sent" }
        await sio.emit("message:new", data, room=f"user:{receiver_id}")
        await sio.emit("message:new", data, room=f"user:{str(user.id)}")
        await redis_pubsub.publish_new_message(receiver_id, data)
    except Exception as e:
        logger.warning(f"Real-time delivery of image message failed: {e}")

    return {
        "message_id": result["message_id"],
        "image_url": image_url,
        "created_at": result["created_at"],
    }

