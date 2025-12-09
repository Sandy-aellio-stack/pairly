import logging
import secrets
from typing import List, Optional
from datetime import datetime, timezone
from backend.models.message_v2 import MessageV2, MessageStatus, MessageType
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
        attachments: List = None
    ) -> MessageV2:
        # Deduct credits
        try:
            await self.credits_service.deduct_credits(
                user_id=sender_id,
                amount=self.message_cost,
                description=f"Message to {receiver_id}",
                transaction_type="message"
            )
        except Exception as e:
            logger.error(f"Failed to deduct credits: {e}")
            raise ValueError("Insufficient credits")
        
        # Create message
        message = MessageV2(
            id=f"msg_{secrets.token_hex(12)}",
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            attachments=attachments or [],
            credits_cost=self.message_cost
        )
        await message.insert()
        
        logger.info(f"Message sent: {message.id}")
        return message
    
    async def fetch_conversation(
        self,
        user1_id: str,
        user2_id: str,
        limit: int = 50
    ) -> List[MessageV2]:
        messages = await MessageV2.find(
            ((MessageV2.sender_id == user1_id) & (MessageV2.receiver_id == user2_id)) |
            ((MessageV2.sender_id == user2_id) & (MessageV2.receiver_id == user1_id))
        ).sort("-created_at").limit(limit).to_list()
        return messages
    
    async def mark_delivered(self, message_id: str):
        message = await MessageV2.find_one(MessageV2.id == message_id)
        if message:
            message.mark_delivered()
            await message.save()
    
    async def mark_read(self, message_id: str):
        message = await MessageV2.find_one(MessageV2.id == message_id)
        if message:
            message.mark_read()
            await message.save()
    
    async def list_conversations(self, user_id: str) -> List[dict]:
        # Get unique conversation partners
        sent = await MessageV2.find(MessageV2.sender_id == user_id).to_list()
        received = await MessageV2.find(MessageV2.receiver_id == user_id).to_list()
        
        partners = set()
        for msg in sent:
            partners.add(msg.receiver_id)
        for msg in received:
            partners.add(msg.sender_id)
        
        conversations = []
        for partner_id in partners:
            last_msg = await MessageV2.find(
                ((MessageV2.sender_id == user_id) & (MessageV2.receiver_id == partner_id)) |
                ((MessageV2.sender_id == partner_id) & (MessageV2.receiver_id == user_id))
            ).sort("-created_at").first_or_none()
            
            unread = await MessageV2.find(
                MessageV2.receiver_id == user_id,
                MessageV2.sender_id == partner_id,
                MessageV2.status != MessageStatus.READ
            ).count()
            
            if last_msg:
                conversations.append({
                    "partner_id": partner_id,
                    "last_message": last_msg.content[:50],
                    "last_message_at": last_msg.created_at.isoformat(),
                    "unread_count": unread
                })
        
        return conversations

_messaging_service_v2 = None

def get_messaging_service_v2():
    global _messaging_service_v2
    if _messaging_service_v2 is None:
        _messaging_service_v2 = MessagingServiceV2()
    return _messaging_service_v2
