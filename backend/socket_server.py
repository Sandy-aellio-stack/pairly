import socketio
from datetime import datetime, timezone
import os
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "truebond-secret-key")
JWT_ALGORITHM = "HS256"

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)

connected_users = {}
active_calls = {}


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.InvalidTokenError:
        return None


@sio.event
async def connect(sid, environ, auth):
    token = auth.get('token') if auth else None
    if not token:
        return False
    
    payload = verify_token(token)
    if not payload:
        return False
    
    user_id = payload.get('sub')
    connected_users[sid] = {
        'user_id': user_id,
        'connected_at': datetime.now(timezone.utc).isoformat()
    }
    
    await sio.enter_room(sid, f"user_{user_id}")
    
    print(f"User {user_id} connected with sid {sid}")
    return True


@sio.event
async def disconnect(sid):
    if sid in connected_users:
        user_id = connected_users[sid]['user_id']
        del connected_users[sid]
        
        for call_id, call in list(active_calls.items()):
            if call['caller_id'] == user_id or call['receiver_id'] == user_id:
                other_user = call['receiver_id'] if call['caller_id'] == user_id else call['caller_id']
                await sio.emit('call_ended', {'call_id': call_id, 'reason': 'disconnect'}, room=f"user_{other_user}")
                del active_calls[call_id]
        
        print(f"User {user_id} disconnected")


@sio.event
async def join_chat(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}
    
    other_user_id = data.get('user_id')
    if not other_user_id:
        return {'error': 'Invalid user ID'}
    
    room_id = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    await sio.enter_room(sid, room_id)
    
    return {'success': True, 'room_id': room_id}


@sio.event
async def leave_chat(sid, data):
    room_id = data.get('room_id')
    if room_id:
        await sio.leave_room(sid, room_id)
    return {'success': True}


@sio.event
async def send_message(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}
    
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    message_type = data.get('type', 'text')
    
    if not receiver_id or not content:
        return {'error': 'Invalid message data'}
    
    room_id = f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
    
    message_data = {
        'id': f"msg_{datetime.now(timezone.utc).timestamp()}",
        'sender_id': user_id,
        'receiver_id': receiver_id,
        'content': content,
        'type': message_type,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'is_read': False
    }
    
    await sio.emit('new_message', message_data, room=room_id)
    await sio.emit('new_message', message_data, room=f"user_{receiver_id}")
    
    return {'success': True, 'message': message_data}


@sio.event
async def typing(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return
    
    receiver_id = data.get('receiver_id')
    if receiver_id:
        await sio.emit('user_typing', {'user_id': user_id}, room=f"user_{receiver_id}")


@sio.event
async def stop_typing(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return
    
    receiver_id = data.get('receiver_id')
    if receiver_id:
        await sio.emit('user_stopped_typing', {'user_id': user_id}, room=f"user_{receiver_id}")


@sio.event
async def call_user(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}
    
    receiver_id = data.get('receiver_id')
    call_type = data.get('call_type', 'audio')
    offer = data.get('offer')
    
    if not receiver_id or not offer:
        return {'error': 'Invalid call data'}
    
    call_id = f"call_{user_id}_{receiver_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    active_calls[call_id] = {
        'caller_id': user_id,
        'receiver_id': receiver_id,
        'call_type': call_type,
        'status': 'ringing',
        'started_at': datetime.now(timezone.utc).isoformat()
    }
    
    await sio.emit('incoming_call', {
        'call_id': call_id,
        'caller_id': user_id,
        'call_type': call_type,
        'offer': offer
    }, room=f"user_{receiver_id}")
    
    return {'success': True, 'call_id': call_id}


@sio.event
async def answer_call(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}
    
    call_id = data.get('call_id')
    answer = data.get('answer')
    
    if not call_id or not answer:
        return {'error': 'Invalid answer data'}
    
    call = active_calls.get(call_id)
    if not call or call['receiver_id'] != user_id:
        return {'error': 'Invalid call'}
    
    call['status'] = 'connected'
    
    await sio.emit('call_answered', {
        'call_id': call_id,
        'answer': answer
    }, room=f"user_{call['caller_id']}")
    
    return {'success': True}


@sio.event
async def reject_call(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}
    
    call_id = data.get('call_id')
    reason = data.get('reason', 'rejected')
    
    call = active_calls.get(call_id)
    if not call:
        return {'error': 'Call not found'}
    
    caller_id = call['caller_id']
    
    del active_calls[call_id]
    
    await sio.emit('call_rejected', {
        'call_id': call_id,
        'reason': reason
    }, room=f"user_{caller_id}")
    
    return {'success': True}


@sio.event
async def end_call(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return {'error': 'Not authenticated'}
    
    call_id = data.get('call_id')
    
    call = active_calls.get(call_id)
    if not call:
        return {'error': 'Call not found'}
    
    other_user = call['receiver_id'] if call['caller_id'] == user_id else call['caller_id']
    
    del active_calls[call_id]
    
    await sio.emit('call_ended', {
        'call_id': call_id,
        'ended_by': user_id
    }, room=f"user_{other_user}")
    
    return {'success': True}


@sio.event
async def ice_candidate(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    if not user_id:
        return
    
    call_id = data.get('call_id')
    candidate = data.get('candidate')
    
    call = active_calls.get(call_id)
    if not call:
        return
    
    other_user = call['receiver_id'] if call['caller_id'] == user_id else call['caller_id']
    
    await sio.emit('ice_candidate', {
        'call_id': call_id,
        'candidate': candidate
    }, room=f"user_{other_user}")


def create_socket_app(app):
    return socketio.ASGIApp(sio, other_asgi_app=app)
