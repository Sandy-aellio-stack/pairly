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
from fastapi import APIRouter, Depends, Query
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_message_service import MessageService, SendMessageRequest
from backend.socket_server import sio, emit_message_to_user, emit_notification_to_user, emit_read_receipt
from backend.core.redis_pubsub import redis_pubsub
import logging

router = APIRouter(prefix="/api/messages", tags=["Luveloop Messages"])
logger = logging.getLogger("messages")


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
        await redis_pubsub.publish_message_notification(data.receiver_id, notification_data)

        # Also emit locally via Socket.IO for backwards compatibility
        await sio.emit('new_message', message_data, room=f"user_{data.receiver_id}")
        await sio.emit('new_message_notification', notification_data, room=f"user_{data.receiver_id}")

        logger.debug(f"Message {result['message_id']} delivered in real-time")

    except Exception as e:
        # Don't fail the request if WebSocket/Redis fails
        # Message is already persisted in database
        logger.warning(f"Real-time delivery failed (message persisted): {e}")

    return result


@router.get("/conversations")
async def get_conversations(user: TBUser = Depends(get_current_user)):
    """
    Get all conversations for current user.
    
    Used for:
    - Conversation list UI
    - Unread count badges
    - Fallback when WebSocket unavailable
    
    Returns conversations sorted by last_message_at descending.
    """
    conversations = await MessageService.get_conversations(str(user.id))
    return {
        "conversations": conversations,
        "count": len(conversations)
    }


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

        # Also emit locally for backwards compatibility
        await sio.emit('messages_read', {
            'reader_id': str(user.id),
            'count': result['marked_read'],
            'read_at': datetime.now(timezone.utc).isoformat()
        }, room=f"user_{other_user_id}")

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
    conversations = await TBConversation.find(
        {"participants": str(user.id)}
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
        
        # Also emit via Socket.IO
        from datetime import datetime, timezone
        await sio.emit('user_typing', {
            'user_id': str(user.id),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=f"user_{receiver_id}")
        
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
        
        # Also emit via Socket.IO
        from datetime import datetime, timezone
        await sio.emit('user_stopped_typing', {
            'user_id': str(user.id),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=f"user_{receiver_id}")
        
        return {"success": True}
    except Exception as e:
        logger.warning(f"Failed to send stop typing indicator: {e}")
        return {"success": False, "error": "Failed to send"}
