"""
Luveloop - Unified Real-Time WebSocket Server
Aligned with frontend/src/services/socket.js
"""
import socketio
import asyncio
from datetime import datetime, timezone
import os
import jwt
import json
import logging
from typing import Optional, Dict, Set, Any

from backend.models.tb_user import TBUser
from backend.models.tb_message import TBMessage, TBConversation
from backend.models.tb_credit import TransactionReason
from backend.models.call_session_v2 import CallSessionV2, CallStatus
from backend.services.tb_credit_service import CreditService
from backend.services.calling_service_v2 import get_calling_service_v2
from backend.utils.token_blacklist import token_blacklist
from backend.core.redis_client import redis_client
from backend.core.redis_pubsub import redis_pubsub

logger = logging.getLogger("websocket")

JWT_SECRET = os.getenv("JWT_SECRET", "truebond-secret-key")
JWT_ALGORITHM = "HS256"

# Socket.IO server configuration
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

# Local connection tracking
connected_users: Dict[str, dict] = {}
user_sockets: Dict[str, Set[str]] = {}

async def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        
        jti = payload.get("jti")
        if jti and await token_blacklist.is_blacklisted(jti):
            return None
            
        user_id = payload.get("sub")
        if user_id and await token_blacklist.is_user_blacklisted(user_id):
            return None
            
        return payload
    except Exception:
        return None

async def update_user_presence(user_id: str, is_online: bool):
    """
    Update user online status and last_seen_at timestamp.
    Production-safe: Handles missing fields and DB errors.
    """
    try:
        user = await TBUser.get(user_id)
        if user:
            user.is_online = is_online
            if not is_online:
                # Add/Update presence fields
                now = datetime.now(timezone.utc)
                user.last_seen_at = now
                user.last_seen = now # compatibility
            await user.save()
            logger.info(f"User {user_id} presence updated to {'online' if is_online else 'offline'}")
    except Exception as e:
        logger.error(f"Presence update failed for user {user_id}: {e}")

async def handle_pubsub_message(channel: str, event: str, data: dict):
    """
    Unified handle for all Redis Pub/Sub messages across the 3 core channels.
    Routes events to local Socket.IO rooms.
    """
    try:
        # 1. Determine the target for the event
        receiver_id = data.get('receiver_id')
        sender_id = data.get('sender_id') # For receipts (read/delivered)
        
        target_room = None
        if receiver_id:
            target_room = f"user_{receiver_id}"
        elif sender_id and (event.startswith("message:") or event.startswith("call:")):
            # Receipts for messages/calls are often sent back to the sender
            target_room = f"user_{sender_id}"
        
        # 2. Emit to the room (or globally for presence)
        if target_room:
            await sio.emit(event, data, room=target_room)
        elif event in ['user:online', 'user:offline']:
            # Global status broadcast
            await sio.emit(event, data)
            
    except Exception as e:
        logger.error(f"Error handling pubsub message from Redis: {e}")

@sio.event
async def connect(sid, environ, auth):
    try:
        # Auth token can be in auth dict (Socket.IO v4) or query params
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get('token')
        
        # [BACKEND SOCKET DEBUG]
        logger.info(f"[BACKEND SOCKET] Connect Attempt - SID={sid}, Auth={bool(auth)}, Token={bool(token)}")

        if not token:
            # Fallback to query string
            from urllib.parse import parse_qs
            query_string = environ.get('QUERY_STRING', '')
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

        if not token:
            logger.warning(f"[BACKEND SOCKET] Auth Failed - SID={sid} (No token provided)")
            return False

        payload = await verify_token(token)
        if not payload:
            logger.warning(f"[BACKEND SOCKET] Auth Failed - SID={sid} (Invalid token)")
            return False

        user_id = payload.get('sub')
        logger.info(f"[BACKEND SOCKET] Auth Success - SID={sid}, UserID={user_id}")
        connected_users[sid] = {'user_id': user_id, 'connected_at': datetime.now(timezone.utc).isoformat()}
        
        if user_id not in user_sockets:
            user_sockets[user_id] = set()
        user_sockets[user_id].add(sid)

        await sio.enter_room(sid, f"user:{user_id}")
        
        if redis_pubsub.is_connected:
            await redis_pubsub.publish_presence(user_id, is_online=True)
        
        await update_user_presence(user_id, True)

        # Notify others only if show_online_status is enabled
        try:
            user_doc = await TBUser.get(user_id)
            show_online = True
            if user_doc and user_doc.settings and user_doc.settings.privacy:
                show_online = user_doc.settings.privacy.show_online
            if show_online:
                await sio.emit('user:online', {'user_id': user_id}, skip_sid=sid)
        except Exception:
            pass
        logger.info(f"[BACKEND SOCKET] User {user_id} fully connected (sid: {sid})")
        return True
    except Exception as e:
        logger.error(f"[BACKEND SOCKET] Connect error for sid {sid}: {e}")
        return False

@sio.event
async def disconnect(sid):
    try:
        if sid not in connected_users:
            logger.info(f"[BACKEND SOCKET] Disconnect - SID={sid} (Unknown user or already processed)")
            return
        
        user_id = connected_users[sid]['user_id']
        logger.info(f"[BACKEND SOCKET] Disconnect - SID={sid}, UserID={user_id}")
        
        del connected_users[sid]
        
        if user_id in user_sockets:
            user_sockets[user_id].discard(sid)
            if not user_sockets[user_id]:
                del user_sockets[user_id]
                
                # Safe cleanup
                if redis_pubsub.is_connected:
                    await redis_pubsub.unsubscribe_user(user_id)
                    await redis_pubsub.publish_presence(user_id, is_online=False)
                
                await update_user_presence(user_id, False)
                
                # Clear location on fully offline
                try:
                    from backend.services.tb_location_service import LocationService
                    await LocationService.mark_location_stale(user_id)
                except Exception as loc_err:
                    logger.warning(f"Could not clear location on disconnect for {user_id}: {loc_err}")
                
                await sio.emit('user:offline', {
                    'user_id': user_id, 
                    'last_seen': datetime.now(timezone.utc).isoformat()
                })
        
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"Disconnect error: {e}")

# ============================================
# CHAT EVENTS (Aligned with socket.js)
# ============================================

@sio.event
async def join_chat(sid, data):
    """frontend: socket.emit('join_chat', { user_id: userId })"""
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id: return {'error': 'Unauthorized'}
    
    other_user_id = data.get('user_id') # Note: frontend uses user_id for the person to chat with
    if not other_user_id: return {'error': 'Invalid user ID'}

    room_id = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    await sio.enter_room(sid, room_id)
    return {'success': True, 'room_id': room_id}

@sio.event
async def leave_chat(sid, data):
    """frontend: socket.emit('leave_chat', { room_id: roomId })"""
    room_id = data.get('room_id')
    if room_id:
        await sio.leave_room(sid, room_id)
    return {'success': True}
@sio.on('message:send')
async def message_send(sid, data):
    """Handle sending a message via WebSocket."""
    # Extract and validate data
    receiver_id = data.get('receiver_id')
    conversation_id = data.get('conversation_id')
    content = data.get('content')
    temp_id = data.get('temp_id')  # Capture temp_id for optimistic UI
    msg_type = data.get('type', 'text')
    
    if not content:
        await sio.emit('error', {'message': 'Message content is required'}, room=sid)
        return
    
    # Get sender from session
    user_id_from_session = await sio.get_session(sid)
    sender_id = user_id_from_session.get('user_id')
    
    if not sender_id:
        return {'error': 'Unauthorized'}

    # 1. Resolve conversation_id if missing (Task 6)
    from beanie import PydanticObjectId
    conversation = None
    
    if conversation_id:
        try:
            conversation_oid = PydanticObjectId(conversation_id)
            conversation = await TBConversation.get(conversation_oid)
        except Exception as e:
            logger.error(f"Invalid conversation_id format: {e}")
            pass  # Invalid conversation_id format

    if not conversation and receiver_id:
        try:
            receiver_oid = PydanticObjectId(receiver_id)
            sender_oid = PydanticObjectId(sender_id)
            # Fallback 1: Create or get by participants
            conversation = await TBConversation.find_one({
                "participants": {"$all": [sender_oid, receiver_oid]}
            })
            if conversation:
                pass
            else:
                # Fallback 2: Create new conversation
                conversation = TBConversation(
                    participants=sorted([sender_oid, receiver_oid]),
                    last_message="",
                    last_message_at=datetime.now(timezone.utc),
                    unread_count={str(receiver_id): 0, str(sender_id): 0}
                )
                await conversation.insert()
        except Exception as e:
            pass

    if not conversation:
        return {'error': 'Could not resolve conversation context'}
    
    # Re-extract receiver_id from conversation to be safe
    receiver_oid = [p for p in conversation.participants if str(p) != sender_id]
    if not receiver_oid:
        # Self-chat case
        receiver_oid = PydanticObjectId(sender_id)
    else:
        receiver_oid = receiver_oid[0]
    
    receiver_id = str(receiver_oid)
    sender_oid = PydanticObjectId(sender_id)

    # 2. Persist Message

    message = TBMessage(
        conversation_id=conversation.id,
        sender_id=sender_oid, 
        receiver_id=receiver_oid, 
        content=content,
        message_type=msg_type
    )
    try:
        await message.insert()
    except Exception as insert_err:
        raise

    try:
        # 3. Deduct Coins
        tx = await CreditService.deduct_credits(
            user_id=sender_id, amount=1, reason=TransactionReason.MESSAGE_SENT, 
            reference_id=str(message.id), description=f"Message to {receiver_id}"
        )
        # Notify sender of updated balance
        await sio.emit('balance_updated', {'coins': tx.balance_after}, room=f"user:{sender_id}")
    except Exception as credit_err:
        pass  # Non-fatal

    # 4. Update Conversation
    if conversation:
        await conversation.update({
            "$set": {
                "last_message": content[:100],
                "last_message_at": message.created_at,
                "last_sender_id": sender_oid,
                "updated_at": datetime.now(timezone.utc)
            }
        })

    message_data = {
        'id': str(message.id), 
        'sender_id': sender_id, 
        'receiver_id': receiver_id, 
        'content': content, 
        'type': msg_type, 
        'created_at': message.created_at.isoformat(),
        'status': "delivered",  # Delivered to recipient socket
        'conversation_id': str(conversation.id)
    }
    
    # Include temp_id in broadcast if provided for optimistic UI matching
    if temp_id:
        message_data['temp_id'] = temp_id

    try:
        # 5. Broadcast via Pub/Sub and local emit with delivered status
        delivered_data = {**message_data, 'status': 'delivered'}
        if redis_pubsub.is_connected:
            await redis_pubsub.publish_new_message(receiver_id, delivered_data)
        
        # Local emit
        await sio.emit('message:new', delivered_data, room=f"user:{receiver_id}")
        await sio.emit('message:new', message_data, room=f"user:{sender_id}")  # sender sees 'delivered'
    except Exception as broadcast_err:
        logger.warning(f"Broadcast failed: {broadcast_err}")
        pass  # Non-fatal
    ack_payload = {
        'success': True, 
        'message_id': str(message.id), 
        'status': 'delivered',
        'message': message_data, 
        'conversation_id': str(conversation.id),
        'error': None
    }

    
    # Include temp_id in ack for immediate frontend replacement
    if temp_id:
        ack_payload['temp_id'] = temp_id
        
    # End-to-end example logged by frontend
    return ack_payload

@sio.on('message:typing')
async def typing(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    receiver_id = data.get('receiver_id')
    if user_id and receiver_id:
        await redis_pubsub.publish_typing(receiver_id, user_id, is_typing=True)
        await sio.emit('message:typing', {'user_id': user_id, 'receiver_id': receiver_id}, room=f"user:{receiver_id}")

@sio.on('message:stop-typing')
async def stop_typing(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    receiver_id = data.get('receiver_id')
    if user_id and receiver_id:
        await redis_pubsub.publish_typing(receiver_id, user_id, is_typing=False)
        await sio.emit('message:stop-typing', {'user_id': user_id, 'receiver_id': receiver_id}, room=f"user:{receiver_id}")

@sio.on('message:read')
async def message_read(sid, data):
    """Mark messages as read via Socket → emit 'seen' status"""
    user_id = connected_users.get(sid, {}).get('user_id')
    sender_id = data.get('sender_id') # sender whose messages are read
    if user_id and sender_id:
        # 1. Update DB
        from backend.services.tb_message_service import MessageService
        result = await MessageService.mark_messages_read(user_id, sender_id)
        
        # 2. Notify sender: message seen/read by recipient
        read_data = {
            'reader_id': user_id,
            'sender_id': sender_id,
            'count': result['marked_read'],
            'read_at': datetime.now(timezone.utc).isoformat(),
            'status': 'seen'  # Frontend expects this for pink ticks
        }
        try:
            if redis_pubsub.is_connected:
                await redis_pubsub.publish_read_receipt(sender_id, user_id, result['marked_read'])
            
            # Emit to sender (status update their outgoing messages)
            await sio.emit('message:read', read_data, room=f"user:{sender_id}")
            # Emit to reader (sync status)
            await sio.emit('message:read', read_data, room=f"user:{user_id}")
        except Exception as emit_err:
            logger.warning(f"Read receipt emit failed: {emit_err}")
        
        logger.info(f"[{user_id}] marked {result['marked_read']} msgs from {sender_id} as read")
        return {'success': True, 'count': result['marked_read']}


# ============================================
# CALLING EVENTS (Aligned with socket.js)
# ============================================

@sio.on("call:initiate")
async def initiate_call_socket(sid, data):
    """Handle frontend socket.emit('call:initiate', { targetUserId, type })"""
    print("🔥 CALL INITIATE RECEIVED:", data)
    
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Unauthorized'}
    
    target_user_id = data.get('targetUserId') or data.get('receiver_id') or data.get('user_id')
    raw_call_type = data.get('type', 'audio')
    
    # Normalize call_type: frontend sends 'audio', backend expects 'voice'
    call_type = 'voice' if raw_call_type in ['audio', 'voice'] else 'video'
    
    if not target_user_id:
        print("[ERROR] No target_user_id found in data:", data)
        return {'error': 'Missing target user ID (targetUserId)'}
    
    try:
        from backend.services.calling_service_v2 import get_calling_service_v2
        service = await get_calling_service_v2()
        call_session = await service.initiate_call(
            caller_id=user_id,
            receiver_id=target_user_id,
            call_type=call_type
        )
        
        print(f"✅ Call session created: {call_session.id}")
        
        # Notify caller (ack)
        await sio.emit('call:created', {
            'success': True,
            'call_id': call_session.id,
            'status': call_session.status.value
        }, room=sid)
        
        # Notify receiver about incoming call
        caller = await TBUser.get(user_id)
        await sio.emit('incoming_call', {
            'caller_id': user_id,
            'call_id': call_session.id,
            'call_type': call_type,
            'caller_name': caller.name if caller else 'Someone'
        }, room=f"user:{target_user_id}")
        
        return {'success': True, 'call_id': call_session.id}
        
    except Exception as e:
        print(f"❌ CALL INITIATE ERROR: {e}")
        logger.error(f"Call initiate failed: {e}")
        return {'error': str(e)}

@sio.on("call_user")
async def call_user(sid, data):
    print("🔥 CALL EVENT RECEIVED:", data)
    
    try:
        target_user = data.get("user_id")
        
        if not target_user:
            raise Exception("No target user")
        
        # Send incoming call event
        await sio.emit(
            "incoming_call",
            {
                "from": sid,
                "type": data.get("call_type", "audio"),
                "offer": data.get("offer")
            },
            room=f"user:{target_user}"
        )
        
        print("✅ Call event sent to:", target_user)
        
    except Exception as e:
        print("❌ CALL ERROR:", str(e))
        
        await sio.emit(
            "call_failed",
            {"error": str(e)},
            room=sid
        )

@sio.on("call:accept")
async def answer_call(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    try:
        service = await get_calling_service_v2()
        call_session = await service.accept_call(call_id=call_id, receiver_id=user_id)
        ans_data = {"call_id": call_id, "receiver_id": user_id, "sender_id": call_session.caller_id}
        if redis_pubsub.is_connected:
            await redis_pubsub.publish("calls", "", "call:accept", ans_data)
        await sio.emit('call:accept', ans_data, room=f"user:{call_session.caller_id}")
        return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.on("call:reject")
async def reject_call(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    reason = data.get('reason', 'rejected')
    try:
        service = await get_calling_service_v2()
        call_session = await service.reject_call(call_id=call_id, receiver_id=user_id, reason=reason)
        rej_data = {"call_id": call_id, "reason": reason, "sender_id": call_session.caller_id}
        if redis_pubsub.is_connected:
            await redis_pubsub.publish("calls", "", "call:reject", rej_data)
        await sio.emit('call:reject', rej_data, room=f"user:{call_session.caller_id}")
        return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.on("call:end")
async def end_call(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    try:
        service = await get_calling_service_v2()
        call_session = await service.end_call(call_id=call_id, user_id=user_id)
        other_id = call_session.receiver_id if user_id == str(call_session.caller_id) else call_session.caller_id
        end_data = {"call_id": call_id, "ended_by": user_id, "receiver_id": str(other_id)}
        if redis_pubsub.is_connected:
            await redis_pubsub.publish("calls", "", "call:end", end_data)
        await sio.emit('call:end', end_data, room=f"user:{other_id}")
        return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.on("webrtc:offer")
async def webrtc_offer(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    offer = data.get('offer')
    try:
        call_session = await CallSessionV2.get(call_id)
        if call_session:
            other_id = call_session.receiver_id if user_id == str(call_session.caller_id) else call_session.caller_id
            offer_data = {"call_id": call_id, "offer": offer, "from_user_id": user_id, "receiver_id": str(other_id)}
            if redis_pubsub.is_connected:
                await redis_pubsub.publish("calls", "", "webrtc:offer", offer_data)
            await sio.emit('webrtc:offer', offer_data, room=f"user:{other_id}")
            return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.on("webrtc:answer")
async def webrtc_answer(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    answer = data.get('answer')
    try:
        call_session = await CallSessionV2.get(call_id)
        if call_session:
            other_id = call_session.receiver_id if user_id == str(call_session.caller_id) else call_session.caller_id
            ans_data = {"call_id": call_id, "answer": answer, "from_user_id": user_id, "receiver_id": str(other_id)}
            if redis_pubsub.is_connected:
                await redis_pubsub.publish("calls", "", "webrtc:answer", ans_data)
            await sio.emit('webrtc:answer', ans_data, room=f"user:{other_id}")
            return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.on("webrtc:ice-candidate")
async def ice_candidate(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    candidate = data.get('candidate')
    try:
        call_session = await CallSessionV2.get(call_id)
        if call_session:
            other_id = call_session.receiver_id if user_id == str(call_session.caller_id) else call_session.caller_id
            ice_data = {"call_id": call_id, "candidate": candidate, "from_user_id": user_id, "receiver_id": str(other_id)}
            if redis_pubsub.is_connected:
                await redis_pubsub.publish("calls", "", "webrtc:ice-candidate", ice_data)
            await sio.emit('webrtc:ice-candidate', ice_data, room=f"user:{other_id}")
            return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.on("call:media-state")
async def media_state(sid, data):
    """
    Handle camera/mic toggle signaling.
    payload: { call_id, type: "video"|"audio", enabled: bool }
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    media_type = data.get('type')
    enabled = data.get('enabled')
    
    try:
        call_session = await CallSessionV2.get(call_id)
        if call_session:
            other_id = call_session.receiver_id if user_id == str(call_session.caller_id) else call_session.caller_id
            state_data = {
                "call_id": call_id, 
                "user_id": user_id, 
                "type": media_type, 
                "enabled": enabled
            }
            if redis_pubsub.is_connected:
                await redis_pubsub.publish("calls", "", "call:media-state", state_data)
            await sio.emit('call:media-state', state_data, room=f"user:{other_id}")
            return {'success': True}
    except Exception as e:
        return {'error': str(e)}

# ============================================
# MATCH EVENTS
# ============================================

@sio.event
async def like_user(sid, data):
    """
    frontend: socket.emit('like_user', { liked_user_id })
    When both users like each other a match is created and new_match is emitted.
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Unauthorized'}

    liked_user_id = data.get('liked_user_id')
    if not liked_user_id:
        return {'error': 'Missing liked_user_id'}

    try:
        from backend.routes.tb_notifications import TBNotification
        import json

        likes_key_forward = f"like:{user_id}:{liked_user_id}"
        likes_key_reverse = f"like:{liked_user_id}:{user_id}"

        if redis_pubsub.is_connected():
            r = redis_pubsub.redis_pub
            await r.setex(likes_key_forward, 7 * 24 * 3600, "1")
            mutual = await r.exists(likes_key_reverse)
        else:
            mutual = False

        if mutual:
            liker = await TBUser.get(user_id)
            liked = await TBUser.get(liked_user_id)
            liker_name = liker.name if liker else "Someone"
            liked_name = liked.name if liked else "Someone"

            match_data = {
                "user_id_a": user_id,
                "user_id_b": liked_user_id,
                "name_a": liker_name,
                "name_b": liked_name,
            }

            await sio.emit('new_match', {**match_data, "matched_with": liked_user_id, "name": liked_name},
                           room=f"user:{user_id}")
            await sio.emit('new_match', {**match_data, "matched_with": user_id, "name": liker_name},
                           room=f"user:{liked_user_id}")

            for uid, partner_name in [(user_id, liked_name), (liked_user_id, liker_name)]:
                try:
                    from backend.models.notification import Notification
                    notif = Notification(
                        user_id=uid,
                        title="New Match!",
                        body=f"You and {partner_name} liked each other",
                        type="match_created",
                        meta={"matched_with": liked_user_id if uid == user_id else user_id}
                    )
                    await notif.insert()
                except Exception:
                    pass

            return {'matched': True}

        return {'matched': False}
    except Exception as e:
        logger.error(f"like_user error: {e}")
        return {'error': 'Internal server error'}


async def emit_match_notification(user_id_a: str, user_id_b: str):
    """
    Utility: Call this whenever a mutual match is recorded outside the socket event.
    Emits new_match to both users and creates DB notifications.
    """
    try:
        from backend.routes.tb_notifications import TBNotification
        from backend.models.notification import Notification

        user_a = await TBUser.get(user_id_a)
        user_b = await TBUser.get(user_id_b)
        name_a = user_a.name if user_a else "Someone"
        name_b = user_b.name if user_b else "Someone"

        await sio.emit('new_match', {"matched_with": user_id_b, "name": name_b},
                       room=f"user:{user_id_a}")
        await sio.emit('new_match', {"matched_with": user_id_a, "name": name_a},
                       room=f"user:{user_id_b}")

        for uid, partner_name in [(user_id_a, name_b), (user_id_b, name_a)]:
            notif = Notification(
                user_id=uid,
                title="New Match!",
                body=f"You and {partner_name} liked each other",
                type="match_created",
                meta={"matched_with": user_id_b if uid == user_id_a else user_id_a}
            )
            await notif.insert()
    except Exception as e:
        logger.error(f"emit_match_notification failed: {e}")


# ============================================
# APP UTILS
# ============================================

async def emit_message_to_user(receiver_id: str, message_data: dict):
    """Emit message to a specific user via Redis or local Socket.IO"""
    try:
        if redis_pubsub.is_connected():
            await redis_pubsub.publish_new_message(receiver_id, message_data)
        await sio.emit('message:new', message_data, room=f"user:{receiver_id}")
    except Exception as e:
        logger.error(f"Failed to emit message to {receiver_id}: {e}")

async def emit_notification_to_user(user_id: str, event: str, data: dict):
    """
    Production-safe notification emitter.
    frontend: socket.on(event, (data) => { ... })
    """
    try:
        if not user_id: return
        await sio.emit(event, data, room=f"user:{user_id}")
        logger.debug(f"Notification '{event}' emitted to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to emit notification '{event}' to {user_id}: {e}")

async def emit_read_receipt(user_id: str, data: dict):
    """Emit read receipt notification to user"""
    await emit_notification_to_user(user_id, 'messages_read', data)

def create_socket_app(app):
    return socketio.ASGIApp(sio, other_asgi_app=app)

async def init_websocket_pubsub():
    await redis_pubsub.connect()
    if redis_pubsub.is_connected:
        await redis_pubsub.subscribe_app_channels(handle_pubsub_message)
        await redis_pubsub.start_subscriber(handle_pubsub_message)
