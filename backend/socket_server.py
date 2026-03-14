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
    if not channel.startswith("truebond:"):
        return
    parts = channel.split(":")
    if len(parts) >= 3:
        user_id = parts[2]
        if user_id in user_sockets:
            try:
                await sio.emit(event, data, room=f"user_{user_id}")
            except Exception as e:
                logger.error(f"PubSub emit failed: {e}")

@sio.event
async def connect(sid, environ, auth):
    try:
        token = auth.get('token') if auth else None
        if not token:
            return False

        payload = await verify_token(token)
        if not payload:
            return False

        user_id = payload.get('sub')
        connected_users[sid] = {'user_id': user_id, 'connected_at': datetime.now(timezone.utc).isoformat()}
        
        if user_id not in user_sockets:
            user_sockets[user_id] = set()
        user_sockets[user_id].add(sid)

        await sio.enter_room(sid, f"user_{user_id}")
        
        if redis_pubsub.is_connected():
            await redis_pubsub.subscribe_user(user_id, handle_pubsub_message)
            await redis_pubsub.publish_presence(user_id, is_online=True)
        
        await update_user_presence(user_id, True)

        # Notify others only if show_online_status is enabled
        try:
            user_doc = await TBUser.get(user_id)
            show_online = True
            if user_doc and user_doc.settings and user_doc.settings.privacy:
                show_online = user_doc.settings.privacy.show_online
            if show_online:
                await sio.emit('user_online', {'user_id': user_id}, skip_sid=sid)
        except Exception:
            pass
        logger.info(f"User {user_id} connected (sid: {sid})")
        return True
    except Exception as e:
        logger.error(f"Connect error: {e}")
        return False

@sio.event
async def disconnect(sid):
    try:
        if sid not in connected_users:
            return
        
        user_id = connected_users[sid]['user_id']
        del connected_users[sid]
        
        if user_id in user_sockets:
            user_sockets[user_id].discard(sid)
            if not user_sockets[user_id]:
                del user_sockets[user_id]
                
                # Safe cleanup
                if redis_pubsub.is_connected():
                    await redis_pubsub.unsubscribe_user(user_id)
                    await redis_pubsub.publish_presence(user_id, is_online=False)
                
                await update_user_presence(user_id, False)
                
                # Clear location on fully offline
                try:
                    from backend.services.tb_location_service import LocationService
                    await LocationService.mark_location_stale(user_id)
                except Exception as loc_err:
                    logger.warning(f"Could not clear location on disconnect for {user_id}: {loc_err}")
                
                await sio.emit('user_offline', {
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

@sio.event
async def send_message(sid, data):
    """frontend: socket.emit('send_message', { receiver_id, content, type })"""
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id: return {'error': 'Unauthorized'}

    receiver_id = data.get('receiver_id')
    content = data.get('content')
    msg_type = data.get('type', 'text')

    if not receiver_id or not content:
        return {'error': 'Missing content or receiver'}

    try:
        # 1. Credits Check
        can_send = await CreditService.can_send_message(user_id)
        if not can_send:
            return {'error': 'Insufficient credits', 'code': 402}

        # 2. Persist Message
        message = TBMessage(sender_id=user_id, receiver_id=receiver_id, content=content)
        await message.insert()

        # 3. Deduct Credits
        tx = await CreditService.deduct_credits(
            user_id=user_id, amount=1, reason=TransactionReason.MESSAGE_SENT, 
            reference_id=str(message.id), description=f"Message to {receiver_id}"
        )
        # Notify sender of updated balance
        await sio.emit('balance_updated', {'credits': tx.balance_after}, room=f"user_{user_id}")

        # 4. Update Conversation
        participants = sorted([user_id, receiver_id])
        await TBConversation.find_one({"participants": participants}).upsert(
            {
                "$set": {
                    "last_message": content[:100],
                    "last_message_at": message.created_at,
                    "last_sender_id": user_id,
                    "updated_at": datetime.now(timezone.utc)
                },
                "$inc": {f"unread_count.{receiver_id}": 1}
            },
            on_insert=TBConversation(
                participants=participants, last_message=content[:100],
                last_message_at=message.created_at, last_sender_id=user_id,
                unread_count={receiver_id: 1}
            )
        )

        message_data = {
            'id': str(message.id), 'sender_id': user_id, 'receiver_id': receiver_id,
            'content': content, 'type': msg_type, 'created_at': message.created_at.isoformat()
        }

        # 5. Create notification for offline receiver (respects notifications_messages setting)
        if receiver_id not in user_sockets:
            try:
                from backend.models.notification import Notification
                receiver_doc = await TBUser.get(receiver_id)
                notify_ok = True
                if receiver_doc and receiver_doc.settings and receiver_doc.settings.notifications:
                    notify_ok = receiver_doc.settings.notifications.messages
                if notify_ok:
                    sender = await TBUser.get(user_id)
                    sender_name = sender.name if sender else "Someone"
                    notif = Notification(
                        user_id=receiver_id,
                        title="New message",
                        body=f"{sender_name} sent you a message",
                        type="message_received",
                        meta={"sender_id": user_id, "message_id": str(message.id)}
                    )
                    await notif.insert()
            except Exception as notif_err:
                logger.warning(f"Failed to create offline notification: {notif_err}")

        # 6. Broadcast
        await redis_pubsub.publish_new_message(receiver_id, message_data)
        room_id = f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
        await sio.emit('new_message', message_data, room=room_id)
        
        return {'success': True, 'message_id': str(message.id)}
    except Exception as e:
        logger.error(f"Send message failed: {e}")
        return {'error': 'Internal server error'}

@sio.event
async def typing(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    receiver_id = data.get('receiver_id')
    if user_id and receiver_id:
        await redis_pubsub.publish_typing(receiver_id, user_id, is_typing=True)
        await sio.emit('user_typing', {'user_id': user_id}, room=f"user_{receiver_id}")

@sio.event
async def stop_typing(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    receiver_id = data.get('receiver_id')
    if user_id and receiver_id:
        await redis_pubsub.publish_typing(receiver_id, user_id, is_typing=False)
        await sio.emit('user_stopped_typing', {'user_id': user_id}, room=f"user_{receiver_id}")

# ============================================
# CALLING EVENTS (Aligned with socket.js)
# ============================================

@sio.event
async def call_user(sid, data):
    """frontend: socket.emit('call_user', { receiver_id, call_type, offer })"""
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id: return {'error': 'Unauthorized'}

    receiver_id = data.get('receiver_id')
    call_type = data.get('call_type', 'voice')
    offer = data.get('offer') # SDP Offer

    try:
        service = await get_calling_service_v2()
        call_session = await service.initiate_call(
            caller_id=user_id, receiver_id=receiver_id, 
            call_type=call_type, sdp_offer=offer
        )
        
        # Notify receiver
        call_data = {
            "type": "call_incoming", "call_id": call_session.id,
            "caller_id": user_id, "call_type": call_type, "offer": offer
        }
        await redis_pubsub.publish("user", receiver_id, "incoming_call", call_data)
        await sio.emit('incoming_call', call_data, room=f"user_{receiver_id}")
        
        return {'success': True, 'call_id': call_session.id}
    except Exception as e:
        logger.error(f"Call initiation failed: {e}")
        return {'error': str(e)}

@sio.event
async def answer_call(sid, data):
    """frontend: socket.emit('answer_call', { call_id, answer })"""
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    answer = data.get('answer') # SDP Answer

    try:
        service = await get_calling_service_v2()
        call_session = await service.accept_call(call_id=call_id, receiver_id=user_id, sdp_answer=answer)
        
        # Notify caller
        ans_data = {"call_id": call_id, "receiver_id": user_id, "answer": answer}
        await redis_pubsub.publish("user", call_session.caller_id, "call_answered", ans_data)
        await sio.emit('call_answered', ans_data, room=f"user_{call_session.caller_id}")
        
        return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.event
async def reject_call(sid, data):
    """frontend: socket.emit('reject_call', { call_id, reason })"""
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    reason = data.get('reason', 'rejected')

    try:
        service = await get_calling_service_v2()
        call_session = await service.reject_call(call_id=call_id, receiver_id=user_id, reason=reason)
        
        rej_data = {"call_id": call_id, "reason": reason}
        await redis_pubsub.publish("user", call_session.caller_id, "call_rejected", rej_data)
        await sio.emit('call_rejected', rej_data, room=f"user_{call_session.caller_id}")
        
        return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.event
async def end_call(sid, data):
    """frontend: socket.emit('end_call', { call_id })"""
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')

    try:
        service = await get_calling_service_v2()
        call_session = await service.end_call(call_id=call_id, user_id=user_id)
        
        other_id = call_session.receiver_id if user_id == call_session.caller_id else call_session.caller_id
        end_data = {"call_id": call_id, "ended_by": user_id}
        await redis_pubsub.publish("user", other_id, "call_ended", end_data)
        await sio.emit('call_ended', end_data, room=f"user_{other_id}")

        # Emit updated balance to caller after billing deduction
        try:
            new_balance = await CreditService.get_balance(user_id)
            await sio.emit('balance_updated', {'credits': new_balance}, room=f"user_{user_id}")
        except Exception:
            pass

        return {'success': True}
    except Exception as e:
        return {'error': str(e)}

@sio.event
async def ice_candidate(sid, data):
    """frontend: socket.emit('ice_candidate', { call_id, candidate })"""
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    candidate = data.get('candidate')

    try:
        call_session = await CallSessionV2.get(call_id)
        if call_session:
            other_id = call_session.receiver_id if user_id == call_session.caller_id else call_session.caller_id
            ice_data = {"call_id": call_id, "candidate": candidate, "from_user_id": user_id}
            await redis_pubsub.publish("user", other_id, "ice_candidate", ice_data)
            await sio.emit('ice_candidate', ice_data, room=f"user_{other_id}")
    except Exception:
        pass

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
                           room=f"user_{user_id}")
            await sio.emit('new_match', {**match_data, "matched_with": user_id, "name": liker_name},
                           room=f"user_{liked_user_id}")

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
                       room=f"user_{user_id_a}")
        await sio.emit('new_match', {"matched_with": user_id_a, "name": name_a},
                       room=f"user_{user_id_b}")

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
        await sio.emit('new_message', message_data, room=f"user_{receiver_id}")
    except Exception as e:
        logger.error(f"Failed to emit message to {receiver_id}: {e}")

async def emit_notification_to_user(user_id: str, event: str, data: dict):
    """
    Production-safe notification emitter.
    frontend: socket.on(event, (data) => { ... })
    """
    try:
        if not user_id: return
        await sio.emit(event, data, room=f"user_{user_id}")
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
    await redis_pubsub.start_subscriber(handle_pubsub_message)
