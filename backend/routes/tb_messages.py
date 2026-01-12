from fastapi import APIRouter, Depends, Query
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_message_service import MessageService, SendMessageRequest
from backend.socket_server import sio

router = APIRouter(prefix="/api/messages", tags=["TrueBond Messages"])


@router.post("/send")
async def send_message(data: SendMessageRequest, user: TBUser = Depends(get_current_user)):
    """
    Send a message to another user.
    - Costs 1 credit per message
    - Returns 402 if insufficient credits
    - Emits real-time event to receiver if connected via WebSocket
    """
    result = await MessageService.send_message(
        sender_id=str(user.id),
        data=data
    )

    # Emit real-time event to receiver
    try:
        message_data = {
            'id': result['message_id'],
            'sender_id': str(user.id),
            'receiver_id': data.receiver_id,
            'content': data.content,
            'is_read': False,
            'created_at': result['created_at']
        }

        # Emit to receiver's room
        await sio.emit('new_message', message_data, room=f"user_{data.receiver_id}")

        # Also emit notification
        await sio.emit('new_message_notification', {
            'message_id': result['message_id'],
            'sender_id': str(user.id),
            'sender_name': user.name,
            'content_preview': data.content[:50],
            'created_at': result['created_at']
        }, room=f"user_{data.receiver_id}")

    except Exception as e:
        # Don't fail the request if WebSocket emit fails
        import logging
        logger = logging.getLogger("messages")
        logger.error(f"Failed to emit WebSocket event: {e}")

    return result


@router.get("/conversations")
async def get_conversations(user: TBUser = Depends(get_current_user)):
    """Get all conversations for current user"""
    conversations = await MessageService.get_conversations(str(user.id))
    return {
        "conversations": conversations,
        "count": len(conversations)
    }


@router.get("/{other_user_id}")
async def get_messages(
    other_user_id: str,
    limit: int = Query(50, ge=1, le=100),
    user: TBUser = Depends(get_current_user)
):
    """Get messages with a specific user"""
    messages = await MessageService.get_messages(
        user_id=str(user.id),
        other_user_id=other_user_id,
        limit=limit
    )
    return {
        "messages": messages,
        "count": len(messages)
    }


@router.post("/read/{other_user_id}")
async def mark_messages_read(other_user_id: str, user: TBUser = Depends(get_current_user)):
    """
    Mark all messages from a user as read
    - Emits real-time event to sender if connected
    """
    result = await MessageService.mark_messages_read(
        user_id=str(user.id),
        other_user_id=other_user_id
    )

    # Emit real-time read receipt to sender
    try:
        from datetime import datetime, timezone
        await sio.emit('messages_read', {
            'reader_id': str(user.id),
            'count': result['marked_read'],
            'read_at': datetime.now(timezone.utc).isoformat()
        }, room=f"user_{other_user_id}")
    except Exception as e:
        import logging
        logger = logging.getLogger("messages")
        logger.error(f"Failed to emit read receipt: {e}")

    return result
