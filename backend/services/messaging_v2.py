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
                credits_transaction_id=transaction.id if transaction else None,
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
        """List all conversations for a user with metadata"""
        # Get all messages involving the user
        messages = await MessageV2.find(
            {
                "is_deleted": False,
                "$or": [
                    {"sender_id": user_id},
                    {"receiver_id": user_id}
                ]
            }
        ).to_list()
        
        # Group by conversation partner
        partners = {}
        for msg in messages:
            partner_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
            
            if partner_id not in partners:
                partners[partner_id] = {
                    "messages": [],
                    "partner_id": partner_id
                }
            partners[partner_id]["messages"].append(msg)
        
        # Build conversation list
        conversations = []
        for partner_id, data in partners.items():
            msgs = data["messages"]
            last_msg = max(msgs, key=lambda m: m.created_at)
            
            # Count unread from this partner
            unread = sum(
                1 for m in msgs
                if m.receiver_id == user_id and m.status != MessageStatus.READ
            )
            
            conversations.append({
                "partner_id": partner_id,
                "last_message": {
                    "content": last_msg.content[:100],
                    "type": last_msg.message_type.value,
                    "sender_id": last_msg.sender_id,
                    "created_at": last_msg.created_at.isoformat()
                },
                "unread_count": unread,
                "total_messages": len(msgs)
            })
        
        # Sort by most recent
        conversations.sort(key=lambda c: c["last_message"]["created_at"], reverse=True)
        return conversations
    
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
