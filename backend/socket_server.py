"""
Real-Time WebSocket Server for TrueBond
Handles real-time messaging, presence, and typing indicators
"""
import socketio
from datetime import datetime, timezone
import os
import jwt
import logging

from backend.models.tb_user import TBUser
from backend.models.tb_message import TBMessage, TBConversation
from backend.models.tb_credit import TransactionReason
from backend.services.tb_credit_service import CreditService
from backend.utils.token_blacklist import token_blacklist

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

# Connected users: {sid: {'user_id': str, 'connected_at': str}}
connected_users = {}

# User to socket mapping: {user_id: set(sid)}
user_sockets = {}


async def verify_token(token: str) -> dict:
    """
    Verify JWT token and check blacklist
    Returns payload if valid, None otherwise
    """
    try:
        # Decode token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        if payload.get("type") != "access":
            logger.warning("Invalid token type for WebSocket")
            return None

        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti:
            is_blacklisted = await token_blacklist.is_blacklisted(jti)
            if is_blacklisted:
                logger.warning("Blacklisted token used for WebSocket")
                return None

        # Check if all user tokens are blacklisted
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
    Verify user has access to conversation with other user
    Users can only access conversations they are part of
    """
    if user_id == other_user_id:
        return False

    # Check if both users exist
    try:
        user = await TBUser.get(user_id)
        other_user = await TBUser.get(other_user_id)

        if not user or not other_user:
            return False

        # Both users must be active
        if not user.is_active or not other_user.is_active:
            return False

        return True
    except Exception as e:
        logger.error(f"Error verifying conversation access: {e}")
        return False


@sio.event
async def connect(sid, environ, auth):
    """
    Handle WebSocket connection with JWT authentication
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

    # Store connection
    connected_users[sid] = {
        'user_id': user_id,
        'connected_at': datetime.now(timezone.utc).isoformat()
    }

    # Track user sockets for multiple connections
    if user_id not in user_sockets:
        user_sockets[user_id] = set()
    user_sockets[user_id].add(sid)

    # Join user's personal room for direct messages
    await sio.enter_room(sid, f"user_{user_id}")

    # Update presence to online
    await update_user_presence(user_id, True)

    # Emit user online event to their contacts
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

        # If no more sockets for this user, mark offline
        if not user_sockets[user_id]:
            del user_sockets[user_id]
            await update_user_presence(user_id, False)

            # Emit user offline event
            await sio.emit('user_offline', {
                'user_id': user_id,
                'last_seen': datetime.now(timezone.utc).isoformat()
            })

    logger.info(f"User {user_id} disconnected")


@sio.event
async def join_conversation(sid, data):
    """
    Join a conversation room
    Client sends: {other_user_id: 'user_id'}
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}

    other_user_id = data.get('other_user_id')
    if not other_user_id:
        return {'error': 'Invalid user ID'}

    # Verify access
    has_access = await verify_conversation_access(user_id, other_user_id)
    if not has_access:
        logger.warning(f"User {user_id} denied access to conversation with {other_user_id}")
        return {'error': 'Access denied'}

    # Create room ID (sorted to ensure consistency)
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
    Real-time message sending through WebSocket
    This is a convenience method - REST API should be used for guaranteed delivery

    Client sends: {
        receiver_id: 'user_id',
        content: 'message text'
    }

    Note: For production use, clients should use REST API POST /api/messages/send
    which guarantees credit deduction and database persistence, then listen for
    the 'new_message' event for real-time delivery.
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}

    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or not content:
        return {'error': 'Invalid message data'}

    # Verify conversation access
    has_access = await verify_conversation_access(user_id, receiver_id)
    if not has_access:
        return {'error': 'Access denied'}

    try:
        # Check receiver exists and is active
        receiver = await TBUser.get(receiver_id)
        if not receiver or not receiver.is_active:
            return {'error': 'Receiver not found'}

        # Check sender has credits
        can_send = await CreditService.can_send_message(user_id)
        if not can_send:
            return {
                'error': 'Insufficient credits',
                'code': 402
            }

        # Create message in database
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
        conversation = await TBConversation.find_one(
            TBConversation.participants == participants
        )

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

        # Emit to conversation room (both users)
        room_id = f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
        await sio.emit('new_message', message_data, room=room_id)

        # Also emit to receiver's personal room (for notifications)
        await sio.emit('new_message_notification', {
            'message_id': str(message.id),
            'sender_id': user_id,
            'content_preview': content[:50],
            'created_at': message.created_at.isoformat()
        }, room=f"user_{receiver_id}")

        logger.info(f"Message sent from {user_id} to {receiver_id}")
        return {'success': True, 'message_id': str(message.id)}

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {'error': 'Failed to send message'}


@sio.event
async def typing(sid, data):
    """
    User started typing
    Client sends: {receiver_id: 'user_id'}
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return

    receiver_id = data.get('receiver_id')
    if not receiver_id:
        return

    # Verify access
    has_access = await verify_conversation_access(user_id, receiver_id)
    if not has_access:
        return

    # Emit to receiver only
    await sio.emit('user_typing', {
        'user_id': user_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, room=f"user_{receiver_id}")

    logger.debug(f"User {user_id} typing to {receiver_id}")


@sio.event
async def stop_typing(sid, data):
    """
    User stopped typing
    Client sends: {receiver_id: 'user_id'}
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return

    receiver_id = data.get('receiver_id')
    if not receiver_id:
        return

    # Verify access
    has_access = await verify_conversation_access(user_id, receiver_id)
    if not has_access:
        return

    # Emit to receiver only
    await sio.emit('user_stopped_typing', {
        'user_id': user_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, room=f"user_{receiver_id}")

    logger.debug(f"User {user_id} stopped typing to {receiver_id}")


@sio.event
async def mark_delivered(sid, data):
    """
    Mark message as delivered
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
            # Emit back to sender
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
    Mark messages as read in real-time
    Client sends: {other_user_id: 'user_id'}
    """
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}

    other_user_id = data.get('other_user_id')
    if not other_user_id:
        return {'error': 'Invalid user ID'}

    try:
        # Update unread messages
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

        # Notify sender that messages were read
        await sio.emit('messages_read', {
            'reader_id': user_id,
            'count': result.modified_count if result else 0,
            'read_at': datetime.now(timezone.utc).isoformat()
        }, room=f"user_{other_user_id}")

        return {'success': True, 'marked_read': result.modified_count if result else 0}

    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        return {'error': 'Failed to mark as read'}


async def emit_message_to_user(receiver_id: str, message_data: dict):
    """
    Helper function to emit message to user (called from REST API)
    """
    try:
        await sio.emit('new_message', message_data, room=f"user_{receiver_id}")
        logger.info(f"Message emitted to user {receiver_id}")
    except Exception as e:
        logger.error(f"Failed to emit message: {e}")


def create_socket_app(app):
    """Create ASGI app with Socket.IO"""
    return socketio.ASGIApp(sio, other_asgi_app=app)
