from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from pydantic import BaseModel, Field
import asyncio
import logging

from backend.models.tb_user import TBUser
from backend.models.tb_message import TBMessage, TBConversation
from backend.models.tb_credit import TransactionReason
from backend.services.tb_credit_service import CreditService
from backend.services.fcm_service import fcm_service

logger = logging.getLogger("message_service")


class SendMessageRequest(BaseModel):
    receiver_id: str
    content: str = Field(min_length=1, max_length=2000)


class MessageService:
    @staticmethod
    async def send_message(sender_id: str, data: SendMessageRequest) -> dict:
        """Send a message - costs 1 credit"""
        # Check receiver exists
        receiver = await TBUser.get(data.receiver_id)
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")

        if sender_id == data.receiver_id:
            raise HTTPException(status_code=400, detail="Cannot send message to yourself")

        # Check sender has credits
        can_send = await CreditService.can_send_message(sender_id)
        if not can_send:
            raise HTTPException(
                status_code=402,
                detail="Insufficient credits. Please purchase more credits to send messages."
            )

        # Get sender for notification
        sender = await TBUser.get(sender_id)
        sender_name = sender.name if sender else "Someone"

        # Create message
        message = TBMessage(
            sender_id=sender_id,
            receiver_id=data.receiver_id,
            content=data.content
        )
        await message.insert()

        # Deduct 1 credit
        await CreditService.deduct_credits(
            user_id=sender_id,
            amount=1,
            reason=TransactionReason.MESSAGE_SENT,
            reference_id=str(message.id),
            description=f"Message to user {data.receiver_id[:8]}..."
        )

        # Update or create conversation
        participants = sorted([sender_id, data.receiver_id])
        conversation = await TBConversation.find_one(
            TBConversation.participants == participants
        )

        if conversation:
            conversation.last_message = data.content[:100]
            conversation.last_message_at = message.created_at
            conversation.last_sender_id = sender_id
            conversation.unread_count[data.receiver_id] = conversation.unread_count.get(data.receiver_id, 0) + 1
            conversation.updated_at = datetime.now(timezone.utc)
            await conversation.save()
        else:
            conversation = TBConversation(
                participants=participants,
                last_message=data.content[:100],
                last_message_at=message.created_at,
                last_sender_id=sender_id,
                unread_count={data.receiver_id: 1}
            )
            await conversation.insert()

        # Send push notification (fire-and-forget, non-blocking)
        asyncio.create_task(
            fcm_service.notify_new_message(
                receiver_id=data.receiver_id,
                sender_name=sender_name,
                message_preview=data.content[:100],
                message_id=str(message.id),
                sender_id=sender_id
            )
        )

        return {
            "message_id": str(message.id),
            "status": "sent",
            "created_at": message.created_at.isoformat()
        }

    @staticmethod
    async def get_conversations(user_id: str) -> List[dict]:
        """Get all conversations for a user"""
        conversations = await TBConversation.find(
            {"participants": user_id}
        ).sort(-TBConversation.last_message_at).to_list()

        result = []
        for conv in conversations:
            # Get the other participant
            other_user_id = [p for p in conv.participants if p != user_id][0]
            other_user = await TBUser.get(other_user_id)

            if other_user:
                result.append({
                    "conversation_id": str(conv.id),
                    "user": {
                        "id": str(other_user.id),
                        "name": other_user.name,
                        "profile_picture": other_user.profile_pictures[0] if other_user.profile_pictures else None,
                        "is_online": other_user.is_online
                    },
                    "last_message": conv.last_message,
                    "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                    "unread_count": conv.unread_count.get(user_id, 0),
                    "is_my_last_message": conv.last_sender_id == user_id
                })

        return result

    @staticmethod
    async def get_messages(user_id: str, other_user_id: str, limit: int = 50, before: str = None) -> List[dict]:
        """Get messages between two users"""
        query = {
            "$or": [
                {"sender_id": user_id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": user_id}
            ]
        }

        messages = await TBMessage.find(query).sort(-TBMessage.created_at).limit(limit).to_list()

        return [
            {
                "id": str(m.id),
                "sender_id": m.sender_id,
                "receiver_id": m.receiver_id,
                "content": m.content,
                "is_mine": m.sender_id == user_id,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat()
            }
            for m in reversed(messages)
        ]

    @staticmethod
    async def mark_messages_read(user_id: str, other_user_id: str) -> dict:
        """Mark all messages from other user as read"""
        result = await TBMessage.find(
            TBMessage.sender_id == other_user_id,
            TBMessage.receiver_id == user_id,
            TBMessage.is_read == False
        ).update_many({
            "$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc)
            }
        })

        # Update conversation unread count
        participants = sorted([user_id, other_user_id])
        conversation = await TBConversation.find_one(
            TBConversation.participants == participants
        )
        if conversation:
            conversation.unread_count[user_id] = 0
            await conversation.save()

        return {"marked_read": result.modified_count if result else 0}
