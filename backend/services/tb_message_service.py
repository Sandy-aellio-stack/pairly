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
    content: str = Field(min_length=1, max_length=2000000)
    message_type: Optional[str] = "text"
    conversation_id: Optional[str] = None  # Optional - if provided, validates against existing


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
        # Note: Removed transaction wrapper for single-instance MongoDB compatibility
        # Check receiver exists
        receiver = await TBUser.get(receiver_oid)
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")

        # Get sender for name
        sender = await TBUser.get(sender_oid)
        sender_name = sender.name if sender else "Someone"

        # Deduct credits
        await CreditService.deduct_credits(
            user_id=str(sender_oid),
            amount=1,
            reason=TransactionReason.MESSAGE_SENT,
            description=f"Message to user {str(receiver_oid)[:8]}..."
        )

        # Update or create conversation
        conversation = None
        
        # If conversation_id provided, validate it exists
        if data.conversation_id:
            from beanie import PydanticObjectId
            try:
                conv_oid = PydanticObjectId(data.conversation_id)
                conversation = await TBConversation.get(conv_oid)
                print(f"[SERVICE DEBUG] Using provided conversation_id: {data.conversation_id}, found: {conversation is not None}")
            except Exception as e:
                print(f"[SERVICE DEBUG] Invalid conversation_id provided: {data.conversation_id}, error: {e}")
        
        # If no valid conversation found, find/create by participants
        if not conversation:
            conversation = await TBConversation.find_one({
                "participants": {
                    "$all": [sender_oid, receiver_oid]
                }
            })
            print(f"[SERVICE DEBUG] Found conversation by participants: {conversation is not None}")

        if conversation:
            conversation.last_message = data.content[:100]
            conversation.last_message_at = datetime.now(timezone.utc)
            conversation.last_sender_id = sender_oid
            receiver_id_str = str(receiver_oid)
            conversation.unread_count[receiver_id_str] = conversation.unread_count.get(receiver_id_str, 0) + 1
            conversation.updated_at = datetime.now(timezone.utc)
            await conversation.save()
        else:
            conversation = TBConversation(
                participants=sorted([sender_oid, receiver_oid]),
                last_message=data.content[:100],
                last_message_at=datetime.now(timezone.utc),
                last_sender_id=sender_oid,
                unread_count={str(receiver_oid): 1}
            )
            await conversation.insert()
            print(f"[SERVICE DEBUG] Created new conversation: {conversation.id}")

        print(f"[SERVICE DEBUG] Initializing TBMessage constructor")
        print(f"[SERVICE DEBUG] TBMessage Params:")
        print(f"[SERVICE DEBUG]   conversation_id: {conversation.id} ({type(conversation.id)})")
        print(f"[SERVICE DEBUG]   sender_id: {sender_oid} ({type(sender_oid)})")
        print(f"[SERVICE DEBUG]   receiver_id: {receiver_oid} ({type(receiver_oid)})")
        print(f"[SERVICE DEBUG]   content: {data.content[:50]}...")
        
        message = TBMessage(
            conversation_id=conversation.id,
            sender_id=sender_oid, 
            receiver_id=receiver_oid, 
            content=data.content,
            message_type=getattr(data, 'message_type', 'text') or 'text'
        )
        await message.insert()
        print(f"[SERVICE DEBUG] TBMessage inserted: {message.id}")

        # Send push notification (wrapped in try/except to never block message flow)
        async def _safe_notify():
            try:
                # Use getattr to safely check if method exists if needed, 
                # but we've added it to FCMService now.
                if hasattr(fcm_service, 'notify_new_message'):
                    await fcm_service.notify_new_message(
                        receiver_id=str(receiver_oid),
                        sender_name=sender_name,
                        message_preview=data.content[:100],
                        message_id=str(message.id),
                        sender_id=str(sender_oid)
                    )
                else:
                    logger.warning("[FCM WARN] notify_new_message missing in FCMService")
            except Exception as e:
                logger.warning("[FCM WARN] Push notification failed: %s", e)

        asyncio.create_task(_safe_notify())

                # Publish exact payload matching User request
        message_dict = {
            "id": str(message.id),
            "sender_id": str(sender_oid),
            "receiver_id": str(receiver_oid),
            "content": data.content,
            "type": message.message_type,
            "created_at": message.created_at.isoformat(),
            "status": "sent"
        }
        from backend.core.redis_pubsub import redis_pubsub
        asyncio.create_task(
            redis_pubsub.publish_new_message(str(receiver_oid), message_dict)
        )

        print(f"[SEND RESULT] REST Success: message_id={message.id}")
        return {
            "success": True,
            "message_id": str(message.id),
            "status": "sent",
            "created_at": message.created_at.isoformat(),
            "message": message_dict, # Nest for front-end consistency
            "conversation_id": str(conversation.id),
            "error": None,
            **message_dict
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
        """Get all conversations for a user - DEDUPED by participant pair"""
        import time
        from backend.utils.objectid_utils import validate_object_id
        from beanie import PydanticObjectId
        method_start = time.time()
        
        print(f"[CONV DEBUG] Raw query for user: {user_id}")
        
        try:
            user_oid = validate_object_id(user_id)
            
            # AGGREGATE: Group by sorted participant pair, keep latest conv per pair
            conv_query_start = time.time()
            pair_convs = await TBConversation.aggregate([
                {"$match": {"participants": {"$in": [user_oid]}}},
                {"$addFields": {
                    "pair_key": {
                        "$arrayElemAt": [
                            {
                                "$map": {
                                    "input": {
                                        "$setDifference": ["$participants", [user_oid]]
                                    },
                                    "as": "other",
                                    "in": "$$other"
                                }
                            },
                            0
                        ]
                    }
                }},
                {"$group": {
                    "_id": "$pair_key",
                    "latest_conv": {"$last": "$$ROOT"},
                    "count": {"$sum": 1}
                }},
                {"$replaceRoot": {"newRoot": "$latest_conv"}},
                {"$sort": {"last_message_at": -1}},
                {"$limit": 20}
            ]).to_list()
            
            conv_query_end = time.time()
            print(f"[CONV DEBUG] Raw pair_convs count: {len(pair_convs)} in {((conv_query_end - conv_query_start)*1000):.2f}ms")

            result = []
            # Collect all other user IDs for batch lookup
            other_user_ids = []
            for conv in pair_convs:
                if len(conv.participants) < 2:
                    continue
                
                other_user_oid = [p for p in conv.participants if p != user_oid]
                if not other_user_oid:
                    continue
                
                other_user_oid = other_user_oid[0]
                other_user_ids.append(other_user_oid)
            
            print(f"[CONV DEBUG] Unique other users: {len(set(other_user_ids))}")
            
            # [CONV USERS START] Batch lookup
            print(f"[CONV USERS START] Batch fetching {len(set(other_user_ids))} unique users...")
            user_query_start = time.time()
            users_map = {}
            if other_user_ids:
                try:
                    users = await TBUser.find(
                        {"_id": {"$in": list(set(other_user_ids))}}
                    ).to_list()
                    for u in users:
                        users_map[str(u.id)] = u
                except Exception as user_err:
                    print(f"[CONV USERS ERROR] Failed to fetch users: {user_err}")
            user_query_end = time.time()
            print(f"[CONV USERS END] Fetched {len(users_map)} user records in {((user_query_end - user_query_start)*1000):.2f}ms")
            
            # [CONV SERIALIZE] Build response from deduped convs
            serialization_start = time.time()
            for conv in pair_convs:
                try:
                    if len(conv.participants) < 2:
                        continue
                    
                    other_user_oid = [p for p in conv.participants if p != user_oid]
                    if not other_user_oid:
                        continue
                    
                    other_user_oid = other_user_oid[0]
                    other_user = users_map.get(str(other_user_oid))
             
                    if other_user:
                        u_name = getattr(other_user, 'name', 'Unknown')
                        u_pics = getattr(other_user, 'profile_pictures', [])
                        u_online = getattr(other_user, 'is_online', False)
                        u_suspended = getattr(other_user, 'is_suspended', False)
                        
                        last_msg_at = None
                        if conv.last_message_at:
                            last_msg_at = conv.last_message_at.isoformat() if hasattr(conv.last_message_at, 'isoformat') else str(conv.last_message_at)
                        
                        unread = 0
                        if conv.unread_count and isinstance(conv.unread_count, dict):
                            unread = int(conv.unread_count.get(user_id, 0))
                        
                        result.append({
                            "conversation_id": str(conv.id),
                            "user": {
                                "id": str(other_user_oid),
                                "name": u_name,
                                "profile_picture": u_pics[0] if u_pics else None,
                                "is_online": u_online,
                                "status": "suspended" if u_suspended else "active"
                            },
                            "last_message": str(conv.last_message) if conv.last_message else None,
                            "last_message_at": last_msg_at,
                            "unread_count": unread,
                            "is_my_last_message": conv.last_sender_id == user_oid,
                            "has_messages": bool(conv.last_message and str(conv.last_message).strip())
                        })
                except Exception as conv_err:
                    print(f"[CONV SERIALIZE ERROR] Error processing conversation {conv.id}: {conv_err}")
                    continue
             
            serialization_end = time.time()
            print(f"[CONV DEBUG] Deduped result count: {len(result)}")
            
            method_end = time.time()
            # FINAL DE DUPE: Ensure one entry per unique user (latest conv)
            user_deduped = {}
            for conv in result:
                user_id = conv['user']['id']
                if user_id not in user_deduped or conv.get('last_message_at', '') > user_deduped[user_id].get('last_message_at', ''):
                    user_deduped[user_id] = conv
            
            final_result = list(user_deduped.values())
            final_result.sort(key=lambda x: x.get('last_message_at', ''), reverse=True)
            
            print(f"[LIVE CONV] backend raw count: {len(result)}")
            print(f"[LIVE CONV] backend return count: {len(final_result)}")
            for conv in final_result[:3]:  # First 3 for sample
                print(f"[LIVE CONV] sample - id: {conv.get('conversation_id')}, participant: {conv.get('user', {}).get('id')}, preview: {conv.get('last_message', '')[:30]}, time: {conv.get('last_message_at')}")
            print(f"[LIVE CONV] backend return count: {len(final_result)}")
            return final_result
            
        except Exception as e:
            print(f"[CONV FATAL ERROR] get_conversations failed: {e}")
            import traceback
            traceback.print_exc()
            return []


    @staticmethod
    async def get_messages(user_id: str, other_user_id: str, limit: int = 50, before: str = None) -> List[dict]:
        """Get messages between two users"""
        from backend.utils.objectid_utils import validate_object_id
        user_oid = validate_object_id(user_id)
        other_user_oid = validate_object_id(other_user_id, "Other User")
        
        # First find the conversation
        conversation = await TBConversation.find_one({
            "participants": {
                "$all": [user_oid, other_user_oid]
            }
        })
        
        if not conversation:
            return []
        
        # Use conversation_id for efficient querying
        query = {"conversation_id": conversation.id}
        
        if before:
            before_oid = validate_object_id(before, "Before timestamp")
            query["created_at"] = {"$lt": before_oid.generation_time}

        messages = await TBMessage.find(query).sort(-TBMessage.created_at).limit(limit).to_list()

        return [
            {
                "id": str(m.id),
                "sender_id": str(m.sender_id),
                "receiver_id": str(m.receiver_id),
                "content": m.content,
                "message_type": getattr(m, 'message_type', 'text') or 'text',
                "image_url": m.content if (getattr(m, 'message_type', 'text') == 'image') else None,
                "is_mine": m.sender_id == user_oid,
                "is_read": m.is_read,
                "status": m.status,
                "created_at": m.created_at.isoformat(),
                "conversation_id": str(conversation.id) # Task 3: Ensure consistency
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
                "status": "read",
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

