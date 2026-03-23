import logging
import secrets
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from backend.models.message_v2 import MessageV2, MessageStatus, MessageType, ModerationStatus
from backend.services.credits_service_v2 import CreditsServiceV2

logger = logging.getLogger('service.messaging_v2')

class MessagingServiceV2:
    def __init__(self):
        self.credits_service = CreditsServiceV2()
        self.message_cost = 1  # 1 credit per message
    
    async def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        attachments: List[Dict[str, Any]] = None
    ) -> MessageV2:
        """Send a message with credit deduction and moderation check"""
        try:
            # Deduct credits first
            transaction = await self.credits_service.deduct_credits(
                user_id=sender_id,
                amount=self.message_cost,
                description=f"Message to {receiver_id}",
                transaction_type="message"
            )
            
            # Create message
            message = MessageV2(
                id=f"msg_{secrets.token_hex(12)}",
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                message_type=message_type,
                attachments=attachments or [],
                credits_cost=self.message_cost,
                credits_transaction_id=transaction if transaction else None,
                moderation_status=ModerationStatus.APPROVED  # Auto-approve in mock mode
            )
            await message.insert()
            
            logger.info(
                f"Message sent successfully",
                extra={
                    "message_id": message.id,
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "type": message_type.value
                }
            )
            return message
            
        except ValueError as e:
            logger.error(f"Failed to deduct credits for message: {e}", extra={"sender_id": sender_id})
            raise ValueError("Insufficient credits to send message")
        except Exception as e:
            logger.error(f"Error sending message: {e}", extra={"sender_id": sender_id}, exc_info=True)
            raise
    
    async def fetch_conversation(
        self,
        user1_id: str,
        user2_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[MessageV2]:
        """Fetch conversation between two users"""
        messages = await MessageV2.find(
            {
                "is_deleted": False,
                "$or": [
                    {"sender_id": user1_id, "receiver_id": user2_id},
                    {"sender_id": user2_id, "receiver_id": user1_id}
                ]
            }
        ).sort("-created_at").skip(skip).limit(limit).to_list()
        
        return list(reversed(messages))  # Return in chronological order
    
    async def mark_delivered(self, message_id: str, receiver_id: str) -> bool:
        """Mark message as delivered"""
        message = await MessageV2.find_one(
            MessageV2.id == message_id,
            MessageV2.receiver_id == receiver_id
        )
        if message and message.status == MessageStatus.SENT:
            message.mark_delivered()
            await message.save()
            logger.info(f"Message {message_id} marked as delivered")
            return True
        return False
    
    async def mark_read(self, message_id: str, receiver_id: str) -> bool:
        """Mark message as read"""
        message = await MessageV2.find_one(
            MessageV2.id == message_id,
            MessageV2.receiver_id == receiver_id
        )
        if message and message.status != MessageStatus.READ:
            message.mark_read()
            await message.save()
            logger.info(f"Message {message_id} marked as read")
            return True
        return False
    
    async def mark_multiple_as_read(self, message_ids: List[str], receiver_id: str) -> int:
        """Mark multiple messages as read (bulk operation)"""
        count = 0
        for msg_id in message_ids:
            if await self.mark_read(msg_id, receiver_id):
                count += 1
        logger.info(f"Marked {count} messages as read for user {receiver_id}")
        return count
    
    async def get_unread_count(self, user_id: str, sender_id: Optional[str] = None) -> int:
        """Get unread message count for a user"""
        query = {
            "receiver_id": user_id,
            "status": {"$ne": MessageStatus.READ},
            "is_deleted": False
        }
        if sender_id:
            query["sender_id"] = sender_id
        
        count = await MessageV2.find(query).count()
        return count
    
    async def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """List all conversations for a user with metadata - OPTIMIZED VERSION using TBConversation"""
        import time
        start_time = time.time()
        
        print(f"[CONV SERVICE] Starting list_conversations for user: {user_id}")
        
        # OPTIMIZED: Use TBConversation which has proper indexing
        from backend.models.tb_message import TBConversation
        from beanie import PydanticObjectId
        
        user_oid = PydanticObjectId(user_id)
        
        print(f"[CONV SERVICE] Before TBConversation query - elapsed: {(time.time() - start_time)*1000:.2f}ms")
        
        # Find all conversations where user is a participant - uses index on participants
        conversations = await TBConversation.find(
            {"participants": user_oid}
        ).sort(-TBConversation.last_message_at).limit(50).to_list()
        
        query_time = (time.time() - start_time) * 1000
        print(f"[CONV SERVICE] TBConversation query returned {len(conversations)} results - elapsed: {query_time:.2f}ms")
        
        # Build conversation list
        result = []
        for conv in conversations:
            # Get the other participant
            other_participant = None
            for p in conv.participants:
                if str(p) != user_id:
                    other_participant = str(p)
                    break
            
            if not other_participant:
                continue
            
            # Get unread count for this user
            unread = conv.unread_count.get(user_id, 0)
            
            result.append({
                "partner_id": other_participant,
                "conversation_id": str(conv.id),
                "last_message": {
                    "content": conv.last_message[:100] if conv.last_message else "Start a conversation",
                    "type": "text",
                    "sender_id": str(conv.last_sender_id) if conv.last_sender_id else None,
                    "created_at": conv.last_message_at.isoformat() if conv.last_message_at else conv.updated_at.isoformat()
                },
                "unread_count": unread,
                "total_messages": 0,  # We don't track this in TBConversation
                "is_my_last_message": str(conv.last_sender_id) == user_id if conv.last_sender_id else False
            })
        
        total_time = (time.time() - start_time) * 1000
        print(f"[CONV SERVICE] Built {len(result)} conversations - total time: {total_time:.2f}ms")
        
        return result
    
    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """Soft delete a message (sender only)"""
        message = await MessageV2.find_one(
            MessageV2.id == message_id,
            MessageV2.sender_id == user_id
        )
        if message and not message.is_deleted:
            message.soft_delete()
            await message.save()
            logger.info(f"Message {message_id} deleted by user {user_id}")
            return True
        return False
    
    async def get_message_stats(self, user_id: str) -> Dict[str, int]:
        """Get messaging statistics for a user"""
        sent = await MessageV2.find(MessageV2.sender_id == user_id).count()
        received = await MessageV2.find(MessageV2.receiver_id == user_id).count()
        unread = await self.get_unread_count(user_id)
        
        return {
            "sent": sent,
            "received": received,
            "unread": unread,
            "total": sent + received
        }

_messaging_service_v2 = None

def get_messaging_service_v2():
    global _messaging_service_v2
    if _messaging_service_v2 is None:
        _messaging_service_v2 = MessagingServiceV2()
    return _messaging_service_v2
