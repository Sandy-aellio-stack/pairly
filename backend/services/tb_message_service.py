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
            
            # ROBUST QUERY: Fetch all recent conversations and dedupe in Python 
            # This avoids any MongoDB aggregation/grouping pitfalls with ObjectIds/Arrays
            conv_query_start = time.time()
            
            # 1. Fetch all conversations matching this user (up to a reasonable limit)
            all_raw_convs = await TBConversation.find(
                {"participants": {"$in": [user_oid]}}
            ).sort("-last_message_at", "-updated_at", "-created_at").limit(200).to_list()
            
            total_matches = len(all_raw_convs)
            print(f"[CONV API DEBUG] Raw DB results count: {total_matches} for user {user_id}")
            
            if total_matches == 0:
                print(f"[CONV API DEBUG] No conversations found in DB for {user_id}. Checking for string IDs...")
                string_matches = await TBConversation.find(
                    {"participants": {"$in": [str(user_id)]}}
                ).to_list()
                print(f"[CONV API DEBUG] found {len(string_matches)} string participant matches")
                all_raw_convs = string_matches
                total_matches = len(all_raw_convs)

            # 2. Dedupe by participant pair (using a string-based set for absolute safety)
            seen_pairs = set()
            pair_convs = []
            
            for conv in all_raw_convs:
                try:
                    # Create a deterministic key for the pair (sorted string IDs)
                    p_ids = sorted([str(p) for p in conv.participants])
                    pair_key = ":".join(p_ids)
                    
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        pair_convs.append(conv)
                except Exception as e:
                    print(f"[CONV API DEBUG] Error processing raw conv {getattr(conv, 'id', 'unknown')}: {e}")
            
            conv_query_end = time.time()
            print(f"[CONV API DEBUG] Deduped count: {len(pair_convs)} in {((conv_query_end - conv_query_start)*1000):.2f}ms")

            result = []
            # Batch fetch all other users
            other_user_ids = []
            for conv in pair_convs:
                if not conv or not conv.get('participants'): continue
                # Explicit string comparison for robustness
                others = [p for p in conv.get('participants', []) if str(p) != str(user_oid)]
                if others:
                    other_user_ids.append(others[0])
            
            # Batch lookup users
            users_map = {}
            if other_user_ids:
                users = await TBUser.find({"_id": {"$in": list(set(other_user_ids))}}).to_list()
                for u in users:
                    users_map[str(u.id)] = u
            
            # Serialization loop
            for conv_data in pair_convs:
                try:
                    # Convert dict to object context if needed or handle as dict
                    # Since it came from aggregate().to_list(), it's a dict
                    c_id = conv_data.get('_id')
                    participants = conv_data.get('participants', [])
                    others = [p for p in participants if str(p) != str(user_oid)]
                    if not others: continue
                    
                    target_oid = others[0]
                    other_user = users_map.get(str(target_oid))
                    
                    if not other_user:
                        print(f"[CONV WARN] Participant {target_oid} not found in DB for conv {c_id}")
                        continue
                        
                    # Build entry
                    last_msg_at = conv_data.get('last_message_at')
                    if last_msg_at:
                        last_msg_at = last_msg_at.isoformat() if hasattr(last_msg_at, 'isoformat') else str(last_msg_at)
                    
                    unread = 0
                    if conv_data.get('unread_count'):
                        unread = conv_data['unread_count'].get(user_id, 0)
                        
                    result.append({
                        "conversation_id": str(c_id),
                        "user": {
                            "id": str(target_oid),
                            "name": getattr(other_user, 'name', 'Unknown'),
                            "profile_picture": other_user.profile_pictures[0] if getattr(other_user, 'profile_pictures') else None,
                            "is_online": getattr(other_user, 'is_online', False),
                            "status": "active"
                        },
                        "last_message": conv_data.get('last_message', ""),
                        "last_message_at": last_msg_at,
                        "unread_count": unread,
                        "is_my_last_message": str(conv_data.get('last_sender_id')) == str(user_oid),
                        "has_messages": bool(conv_data.get('last_message_at'))
                    })
                except Exception as e:
                    print(f"[CONV ERROR] Failed to serialize conversation {conv_data.get('_id')}: {e}")
            
            print(f"[CONV DEBUG] Final serialized count for {user_id}: {len(result)}")
            return result
            
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

