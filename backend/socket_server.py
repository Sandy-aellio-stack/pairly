"""
Real-Time WebSocket Server for TrueBond
Production-ready implementation with Redis Pub/Sub.

Architecture:
- WebSocket layer is STATELESS
- All real-time fan-out happens via Redis Pub/Sub
- Database is the source of truth
- Automatic fallback to REST APIs when WebSocket unavailable

Socket Events (Client → Server):
- connect: Authenticate with JWT token
- disconnect: Clean up resources
- join_conversation: Join a chat room
- leave_conversation: Leave a chat room
- send_message_realtime: Send message (prefer REST API)
- typing: Start typing indicator
- stop_typing: Stop typing indicator
- mark_delivered: Mark message as delivered
- mark_read_realtime: Mark messages as read

Socket Events (Server → Client):
- new_message: New message received
- new_message_notification: Message notification (for badge updates)
- user_typing: User started typing
- user_stopped_typing: User stopped typing
- messages_read: Messages were read by recipient
- message_delivered: Message was delivered
- user_online: User came online
- user_offline: User went offline
"""
import socketio
import asyncio
from datetime import datetime, timezone
import os
import jwt
import json
import logging
from typing import Optional, Dict, Set

from backend.models.tb_user import TBUser
from backend.models.tb_message import TBMessage, TBConversation
from backend.models.tb_credit import TransactionReason
from backend.services.tb_credit_service import CreditService
from backend.utils.token_blacklist import token_blacklist
from backend.core.redis_client import redis_client
from backend.core.redis_pubsub import redis_pubsub

logger = logging.getLogger("websocket")

JWT_SECRET = os.getenv("JWT_SECRET", "truebond-secret-key")
JWT_ALGORITHM = "HS256"

# Socket.IO server configuration
# Using Redis adapter for horizontal scaling when Redis is available
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

# Local connection tracking (per server instance)
# Maps session_id → user info
connected_users: Dict[str, dict] = {}

# User to socket mapping for local delivery
# Maps user_id → set of session_ids on this server instance
user_sockets: Dict[str, Set[str]] = {}


async def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token and check blacklist.
    Returns payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        if payload.get("type") != "access":
            logger.warning("Invalid token type for WebSocket")
            return None

        jti = payload.get("jti")
        if jti:
            is_blacklisted = await token_blacklist.is_blacklisted(jti)
            if is_blacklisted:
                logger.warning("Blacklisted token used for WebSocket")
                return None

        user_id = payload.get("sub")
        if user_id:
            is_user_blacklisted = await token_blacklist.is_user_blacklisted(user_id)
            if is_user_blacklisted:
                logger.warning(f"User {user_id} tokens blacklisted")
                return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Expired token used for WebSocket")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token for WebSocket: {e}")
        return None


async def update_user_presence(user_id: str, is_online: bool):
    """Update user online/offline status in database"""
    try:
        user = await TBUser.get(user_id)
        if user:
            user.is_online = is_online
            if not is_online:
                user.last_seen_at = datetime.now(timezone.utc)
            await user.save()
    except Exception as e:
        logger.error(f"Failed to update presence for user {user_id}: {e}")


async def verify_conversation_access(user_id: str, other_user_id: str) -> bool:
    """
    Verify user has access to conversation with other user.
    Users can only access conversations they are part of.
    """
    if user_id == other_user_id:
        return False

    try:
        user = await TBUser.get(user_id)
        other_user = await TBUser.get(other_user_id)

        if not user or not other_user:
            return False

        if not user.is_active or not other_user.is_active:
            return False

        return True
    except Exception as e:
        logger.error(f"Error verifying conversation access: {e}")
        return False


async def handle_pubsub_message(channel: str, event: str, data: dict):
    """
    Handle incoming messages from Redis Pub/Sub.
    Routes messages to appropriate local WebSocket connections.
    """
    try:
        # Extract user_id from channel (format: truebond:user:{user_id})
        parts = channel.split(":")
        if len(parts) < 3:
            return
        
        user_id = parts[2]
        
        # Check if user has local connections
        if user_id in user_sockets and user_sockets[user_id]:
            # Emit to user's personal room
            await sio.emit(event, data, room=f"user_{user_id}")
            logger.debug(f"Delivered {event} to user {user_id} via pub/sub")
    except Exception as e:
        logger.error(f"Error handling pub/sub message: {e}")


async def setup_redis_pubsub():
    """Initialize Redis Pub/Sub for real-time messaging"""
    if not redis_client.is_connected():
        logger.warning("Redis not connected - running without pub/sub")
        return False
    
    connected = await redis_pubsub.connect()
    if connected:
        await redis_pubsub.start_subscriber(handle_pubsub_message)
        logger.info("Redis Pub/Sub initialized for WebSocket")
        return True
    return False


# ============================================
# Socket.IO Event Handlers
# ============================================

@sio.event
async def connect(sid, environ, auth):
    """
    Handle WebSocket connection with JWT authentication.
    Client must send: {auth: {token: 'jwt_token_here'}}
    """
    token = auth.get('token') if auth else None
    if not token:
        logger.warning(f"Connection rejected - no token provided")
        return False

    payload = await verify_token(token)
    if not payload:
        logger.warning(f"Connection rejected - invalid token")
        return False

    user_id = payload.get('sub')

    # Store connection locally
    connected_users[sid] = {
        'user_id': user_id,
        'connected_at': datetime.now(timezone.utc).isoformat()
    }

    # Track user sockets
    if user_id not in user_sockets:
        user_sockets[user_id] = set()
    user_sockets[user_id].add(sid)

    # Join user's personal room for direct messages
    await sio.enter_room(sid, f"user_{user_id}")

    # Subscribe to user's Redis channels
    await redis_pubsub.subscribe_user(user_id, handle_pubsub_message)

    # Update presence to online
    await update_user_presence(user_id, True)

    # Publish user online via Redis (fan-out to all server instances)
    await redis_pubsub.publish_presence(user_id, is_online=True)

    # Local emit for backwards compatibility
    await sio.emit('user_online', {'user_id': user_id}, skip_sid=sid)

    logger.info(f"User {user_id} connected with sid {sid}")
    return True


@sio.event
async def disconnect(sid):
    """Handle WebSocket disconnection"""
    if sid not in connected_users:
        return

    user_id = connected_users[sid]['user_id']
    del connected_users[sid]

    # Remove from user sockets
    if user_id in user_sockets:
        user_sockets[user_id].discard(sid)

        # If no more sockets for this user on this server
        if not user_sockets[user_id]:
            del user_sockets[user_id]
            
            # Unsubscribe from Redis channels
            await redis_pubsub.unsubscribe_user(user_id)
            
            # Update presence to offline
            await update_user_presence(user_id, False)
            
            # Mark location as stale for privacy
            try:
                from backend.services.tb_location_service import LocationService
                await LocationService.mark_location_stale(user_id)
            except Exception as e:
                logger.warning(f"Failed to mark location stale: {e}")

            # Publish user offline via Redis
            await redis_pubsub.publish_presence(user_id, is_online=False)

            # Local emit for backwards compatibility
            await sio.emit('user_offline', {
                'user_id': user_id,
                'last_seen': datetime.now(timezone.utc).isoformat()
            })

    logger.info(f"User {user_id} disconnected")


@sio.event
async def join_conversation(sid, data):
    """
    Join a conversation room.
    Client sends: {other_user_id: 'user_id'}
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}

    other_user_id = data.get('other_user_id')
    if not other_user_id:
        return {'error': 'Invalid user ID'}

    has_access = await verify_conversation_access(user_id, other_user_id)
    if not has_access:
        logger.warning(f"User {user_id} denied access to conversation with {other_user_id}")
        return {'error': 'Access denied'}

    # Create deterministic room ID
    room_id = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    await sio.enter_room(sid, room_id)

    logger.info(f"User {user_id} joined conversation with {other_user_id}")
    return {'success': True, 'room_id': room_id}


@sio.event
async def leave_conversation(sid, data):
    """Leave a conversation room"""
    room_id = data.get('room_id')
    if room_id:
        await sio.leave_room(sid, room_id)
        logger.info(f"User left room {room_id}")
    return {'success': True}


@sio.event
async def send_message_realtime(sid, data):
    """
    Real-time message sending through WebSocket.
    
    NOTE: For guaranteed delivery, clients should use REST API:
    POST /api/messages/send
    
    This WebSocket method provides instant delivery but REST is
    the primary method for credit deduction and persistence.
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}

    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or not content:
        return {'error': 'Invalid message data'}

    has_access = await verify_conversation_access(user_id, receiver_id)
    if not has_access:
        return {'error': 'Access denied'}

    try:
        # Check receiver exists
        receiver = await TBUser.get(receiver_id)
        if not receiver or not receiver.is_active:
            return {'error': 'Receiver not found'}

        # Check credits
        can_send = await CreditService.can_send_message(user_id)
        if not can_send:
            return {
                'error': 'Insufficient credits',
                'code': 402,
                'fallback': 'Use GET /api/credits/balance to check balance'
            }

        # Create message in database (source of truth)
        message = TBMessage(
            sender_id=user_id,
            receiver_id=receiver_id,
            content=content
        )
        await message.insert()

        # Deduct credit
        await CreditService.deduct_credits(
            user_id=user_id,
            amount=1,
            reason=TransactionReason.MESSAGE_SENT,
            reference_id=str(message.id),
            description=f"Message to user {receiver_id[:8]}..."
        )

        # Update conversation
        participants = sorted([user_id, receiver_id])
        conversation = await TBConversation.find_one({"participants": participants})

        if conversation:
            conversation.last_message = content[:100]
            conversation.last_message_at = message.created_at
            conversation.last_sender_id = user_id
            conversation.unread_count[receiver_id] = conversation.unread_count.get(receiver_id, 0) + 1
            conversation.updated_at = datetime.now(timezone.utc)
            await conversation.save()
        else:
            conversation = TBConversation(
                participants=participants,
                last_message=content[:100],
                last_message_at=message.created_at,
                last_sender_id=user_id,
                unread_count={receiver_id: 1}
            )
            await conversation.insert()

        # Prepare message data
        message_data = {
            'id': str(message.id),
            'sender_id': user_id,
            'receiver_id': receiver_id,
            'content': content,
            'is_read': False,
            'created_at': message.created_at.isoformat()
        }

        # Publish via Redis for fan-out to all server instances
        await redis_pubsub.publish_new_message(receiver_id, message_data)
        
        # Publish notification
        await redis_pubsub.publish_message_notification(
            receiver_id,
            {
                'message_id': str(message.id),
                'sender_id': user_id,
                'content_preview': content[:50],
                'created_at': message.created_at.isoformat()
            }
        )

        # Local room emit for backwards compatibility
        room_id = f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
        await sio.emit('new_message', message_data, room=room_id)

        logger.info(f"Message sent from {user_id} to {receiver_id}")
        return {'success': True, 'message_id': str(message.id)}

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {
            'error': 'Failed to send message',
            'fallback': 'Use POST /api/messages/send for guaranteed delivery'
        }


@sio.event
async def typing(sid, data):
    """
    User started typing.
    Client sends: {receiver_id: 'user_id'}
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return

    receiver_id = data.get('receiver_id')
    if not receiver_id:
        return

    has_access = await verify_conversation_access(user_id, receiver_id)
    if not has_access:
        return

    # Publish via Redis
    await redis_pubsub.publish_typing(receiver_id, user_id, is_typing=True)

    # Local emit for backwards compatibility
    await sio.emit('user_typing', {
        'user_id': user_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, room=f"user_{receiver_id}")

    logger.debug(f"User {user_id} typing to {receiver_id}")


@sio.event
async def stop_typing(sid, data):
    """
    User stopped typing.
    Client sends: {receiver_id: 'user_id'}
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return

    receiver_id = data.get('receiver_id')
    if not receiver_id:
        return

    has_access = await verify_conversation_access(user_id, receiver_id)
    if not has_access:
        return

    # Publish via Redis
    await redis_pubsub.publish_typing(receiver_id, user_id, is_typing=False)

    # Local emit for backwards compatibility
    await sio.emit('user_stopped_typing', {
        'user_id': user_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, room=f"user_{receiver_id}")

    logger.debug(f"User {user_id} stopped typing to {receiver_id}")


@sio.event
async def mark_delivered(sid, data):
    """
    Mark message as delivered.
    Client sends: {message_id: 'msg_id'}
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}

    message_id = data.get('message_id')
    if not message_id:
        return {'error': 'Invalid message ID'}

    try:
        message = await TBMessage.get(message_id)
        if message and message.receiver_id == user_id:
            # Publish via Redis
            await redis_pubsub.publish_message_delivered(
                message.sender_id,
                message_id
            )

            # Local emit for backwards compatibility
            await sio.emit('message_delivered', {
                'message_id': message_id,
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }, room=f"user_{message.sender_id}")

            return {'success': True}
    except Exception as e:
        logger.error(f"Error marking message as delivered: {e}")

    return {'error': 'Failed to mark delivered'}


@sio.event
async def mark_read_realtime(sid, data):
    """
    Mark messages as read in real-time.
    Client sends: {other_user_id: 'user_id'}
    
    NOTE: Prefer REST API POST /api/messages/read/{other_user_id}
    for guaranteed persistence.
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}

    other_user_id = data.get('other_user_id')
    if not other_user_id:
        return {'error': 'Invalid user ID'}

    try:
        # Update unread messages in database
        result = await TBMessage.find(
            {"sender_id": other_user_id, "receiver_id": user_id, "is_read": False}
        ).update_many({
            "$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc)
            }
        })

        # Update conversation unread count
        participants = sorted([user_id, other_user_id])
        conversation = await TBConversation.find_one({"participants": participants})
        if conversation:
            conversation.unread_count[user_id] = 0
            await conversation.save()

        count = result.modified_count if result else 0

        # Publish via Redis
        await redis_pubsub.publish_read_receipt(
            other_user_id,
            user_id,
            count
        )

        # Local emit for backwards compatibility
        await sio.emit('messages_read', {
            'reader_id': user_id,
            'count': count,
            'read_at': datetime.now(timezone.utc).isoformat()
        }, room=f"user_{other_user_id}")

        return {'success': True, 'marked_read': count}

    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        return {
            'error': 'Failed to mark as read',
            'fallback': 'Use POST /api/messages/read/{other_user_id}'
        }


# ============================================
# Helper Functions for REST API Integration
# ============================================

async def emit_message_to_user(receiver_id: str, message_data: dict):
    """
    Emit message to user from REST API.
    Uses Redis Pub/Sub for cross-server delivery.
    """
    try:
        # Publish via Redis (primary method)
        published = await redis_pubsub.publish_new_message(receiver_id, message_data)
        
        # Also emit locally for backwards compatibility
        await sio.emit('new_message', message_data, room=f"user_{receiver_id}")
        
        if published:
            logger.info(f"Message published via Redis to user {receiver_id}")
        else:
            logger.info(f"Message emitted locally to user {receiver_id}")
    except Exception as e:
        logger.error(f"Failed to emit message: {e}")


async def emit_notification_to_user(receiver_id: str, notification_data: dict):
    """Emit notification to user from REST API"""
    try:
        await redis_pubsub.publish_message_notification(receiver_id, notification_data)
        await sio.emit('new_message_notification', notification_data, room=f"user_{receiver_id}")
    except Exception as e:
        logger.error(f"Failed to emit notification: {e}")


async def emit_read_receipt(sender_id: str, reader_id: str, count: int):
    """Emit read receipt from REST API"""
    try:
        await redis_pubsub.publish_read_receipt(sender_id, reader_id, count)
        await sio.emit('messages_read', {
            'reader_id': reader_id,
            'count': count,
            'read_at': datetime.now(timezone.utc).isoformat()
        }, room=f"user_{sender_id}")
    except Exception as e:
        logger.error(f"Failed to emit read receipt: {e}")


def create_socket_app(app):
    """Create ASGI app with Socket.IO"""
    return socketio.ASGIApp(sio, other_asgi_app=app)


# Initialize Redis Pub/Sub when module loads
async def init_websocket_pubsub():
    """Initialize WebSocket Redis Pub/Sub - call from app startup"""
    await setup_redis_pubsub()
