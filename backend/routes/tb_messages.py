from fastapi import APIRouter, Depends, Query
from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user
from backend.services.tb_message_service import MessageService, SendMessageRequest

router = APIRouter(prefix="/api/messages", tags=["TrueBond Messages"])


@router.post("/send")
async def send_message(data: SendMessageRequest, user: TBUser = Depends(get_current_user)):
    """
    Send a message to another user.
    - Costs 1 credit per message
    - Returns 402 if insufficient credits
    """
    return await MessageService.send_message(
        sender_id=str(user.id),
        data=data
    )


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
    """Mark all messages from a user as read"""
    return await MessageService.mark_messages_read(
        user_id=str(user.id),
        other_user_id=other_user_id
    )
