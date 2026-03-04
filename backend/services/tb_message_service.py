from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from pydantic import BaseModel, Field
import asyncio
import logging
from bson import ObjectId
from beanie import PydanticObjectId

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
        """Send a message - costs 1 credit - uses transaction for atomicity"""
        from backend.utils.objectid_utils import validate_object_id
        sender_oid = validate_object_id(sender_id, "Sender")
        receiver_oid = validate_object_id(data.receiver_id, "Receiver")

        if sender_oid == receiver_oid:
            raise HTTPException(status_code=400, detail="Cannot send message to yourself")

        # Start MongoDB transaction
        async with await TBUser.get_motor_client().start_session() as session:
            async with session.start_transaction():
                # Check receiver exists
                receiver = await TBUser.get(receiver_oid, session=session)
                if not receiver:
                    raise HTTPException(status_code=404, detail="Receiver not found")

                # Get sender for name
                sender = await TBUser.get(sender_oid, session=session)
                sender_name = sender.name if sender else "Someone"

                # Deduct credits
                await CreditService.deduct_credits(
                    user_id=str(sender_oid),
                    amount=1,
                    reason=TransactionReason.MESSAGE_SENT,
                    description=f"Message to user {str(receiver_oid)[:8]}...",
                    session=session
                )

                # Create message
                message = TBMessage(
                    sender_id=sender_oid,
                    receiver_id=receiver_oid,
                    content=data.content
                )
                await message.insert(session=session)

                # Update or create conversation
                conversation = await TBConversation.find_one({
                    "participants": {
                        "$all": [sender_oid, receiver_oid]
                    }
                }, session=session)

                if conversation:
                    conversation.last_message = data.content[:100]
                    conversation.last_message_at = message.created_at
                    conversation.last_sender_id = sender_oid
                    receiver_id_str = str(receiver_oid)
                    conversation.unread_count[receiver_id_str] = conversation.unread_count.get(receiver_id_str, 0) + 1
                    conversation.updated_at = datetime.now(timezone.utc)
                    await conversation.save(session=session)
                else:
                    conversation = TBConversation(
                        participants=sorted([sender_oid, receiver_oid]),
                        last_message=data.content[:100],
                        last_message_at=message.created_at,
                        last_sender_id=sender_oid,
                        unread_count={str(receiver_oid): 1}
                    )
                    await conversation.insert(session=session)

                # Send push notification (outside transaction logic but after SUCCESS)
                asyncio.create_task(
                    fcm_service.notify_new_message(
                        receiver_id=str(receiver_oid),
                        sender_name=sender_name,
                        message_preview=data.content[:100],
                        message_id=str(message.id),
                        sender_id=str(sender_oid)
                    )
                )

                return {
                    "message_id": str(message.id),
                    "status": "sent",
                    "created_at": message.created_at.isoformat()
                }

    @staticmethod
    async def start_conversation(sender_id: str, receiver_id: str) -> dict:
        """Initialize a conversation without sending a message"""
        from backend.utils.objectid_utils import validate_object_id
        sender_oid = validate_object_id(sender_id, "Sender")
        
        # Robust lookup using strict ObjectId as requested
        receiver_oid = validate_object_id(receiver_id, "Receiver")
            
        if sender_oid == receiver_oid:
            raise HTTPException(status_code=400, detail="Cannot chat with yourself")
            
        receiver = await TBUser.get(receiver_oid)
        if not receiver:
            print(f"ERROR: Receiver with ID '{receiver_id}' not found in database")
            raise HTTPException(status_code=404, detail="User not found")
            
        # Use $all with ObjectIds
        conversation = await TBConversation.find_one({
            "participants": {
                "$all": [sender_oid, receiver_oid]
            }
        })
        
        if not conversation:
            conversation = TBConversation(
                participants=sorted([sender_oid, receiver_oid]),
                unread_count={str(sender_oid): 0, str(receiver_oid): 0}
            )
            await conversation.insert()
            
        return {
            "conversation_id": str(conversation.id),
            "status": "success",
            "user": {
                "id": str(receiver.id),
                "name": receiver.name,
                "profile_picture": receiver.profile_pictures[0] if receiver.profile_pictures else None,
                "is_online": receiver.is_online,
                "status": "suspended" if receiver.is_suspended else "active"
            }
        }

    @staticmethod
    async def get_conversations(user_id: str) -> List[dict]:
        """Get all conversations for a user"""
        from backend.utils.objectid_utils import validate_object_id
        user_oid = validate_object_id(user_id)
        
        # Use $in operator with ObjectId
        conversations = await TBConversation.find(
            {"participants": {"$in": [user_oid]}}
        ).sort(-TBConversation.last_message_at).to_list()

        result = []
        for conv in conversations:
            if len(conv.participants) < 2:
                continue
            
            other_user_oid = [p for p in conv.participants if p != user_oid]
            if not other_user_oid:
                continue
            
            other_user_oid = other_user_oid[0]
            other_user = await TBUser.get(other_user_oid)

            if other_user:
                result.append({
                    "conversation_id": str(conv.id),
                    "user": {
                        "id": str(other_user.id),
                        "name": other_user.name,
                        "profile_picture": other_user.profile_pictures[0] if other_user.profile_pictures else None,
                        "is_online": other_user.is_online,
                        "status": "suspended" if other_user.is_suspended else "active"
                    },
                    "last_message": conv.last_message,
                    "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                    "unread_count": conv.unread_count.get(user_id, 0),
                    "is_my_last_message": conv.last_sender_id == user_oid
                })

        return result

    @staticmethod
    async def get_messages(user_id: str, other_user_id: str, limit: int = 50, before: str = None) -> List[dict]:
        """Get messages between two users"""
        from backend.utils.objectid_utils import validate_object_id
        user_oid = validate_object_id(user_id)
        other_user_oid = validate_object_id(other_user_id, "Other User")
        
        query = {
            "$or": [
                {"sender_id": user_oid, "receiver_id": other_user_oid},
                {"sender_id": other_user_oid, "receiver_id": user_oid}
            ]
        }

        messages = await TBMessage.find(query).sort(-TBMessage.created_at).limit(limit).to_list()

        return [
            {
                "id": str(m.id),
                "sender_id": str(m.sender_id),
                "receiver_id": str(m.receiver_id),
                "content": m.content,
                "is_mine": m.sender_id == user_oid,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat()
            }
            for m in reversed(messages)
        ]

    @staticmethod
    async def mark_messages_read(user_id: str, other_user_id: str) -> dict:
        """Mark all messages from other user as read"""
        from backend.utils.objectid_utils import validate_object_id
        user_oid = validate_object_id(user_id)
        other_user_oid = validate_object_id(other_user_id, "Other User")
        
        result = await TBMessage.find(
            TBMessage.sender_id == other_user_oid,
            TBMessage.receiver_id == user_oid,
            TBMessage.is_read == False
        ).update_many({
            "$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc)
            }
        })

        # Update conversation unread count
        conversation = await TBConversation.find_one({
            "participants": {
                "$all": [user_oid, other_user_oid]
            }
        })
        if conversation:
            conversation.unread_count[user_id] = 0
            await conversation.save()

        return {"marked_read": result.modified_count if result else 0}
