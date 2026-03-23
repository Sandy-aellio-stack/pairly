import re

with open("backend/socket_server.py", "r") as f:
    code = f.read()

# Replace user online/offline
code = code.replace("await sio.emit('user_online'", "await sio.emit('user:online'")
code = code.replace("await sio.emit('user_offline'", "await sio.emit('user:offline'")

# Message send/new
code = code.replace("@sio.event\nasync def send_message(sid, data):", "@sio.on('message:send')\nasync def message_send(sid, data):")
code = code.replace("print(f\"[WS] send_message received: {data}\")", "print(f\"[WS] message:send received: {data}\")")
code = code.replace("await sio.emit('new_message'", "await sio.emit('message:new'")

# Typing
code = code.replace("@sio.event\nasync def typing(sid, data):", "@sio.on('message:typing')\nasync def typing(sid, data):")
code = code.replace("await sio.emit('user_typing'", "await sio.emit('message:typing'")
code = code.replace("@sio.event\nasync def stop_typing(sid, data):", "@sio.on('message:stop-typing')\nasync def stop_typing(sid, data):")
code = code.replace("await sio.emit('user_stopped_typing'", "await sio.emit('message:stop-typing'")

# Calling
# Currently there is @sio.on('call:initiate') -> handle_call_initiate.
# And @sio.event call_initiate
# And @sio.on("call_user") -> call_user
# And @sio.event answer_call
# And @sio.event reject_call
# And @sio.event end_call
# And @sio.event ice_candidate

calling_logic_new = """
@sio.on("call:initiate")
async def call_user(sid, data):
    print("CALL INITIATE RECEIVED", sid, data)
    user_id_from_conn = connected_users.get(sid, {}).get('user_id')
    if not user_id_from_conn: return {'error': 'Unauthorized'}
    
    receiver_id = data.get('targetUserId') or data.get('user_id') or data.get('receiver_id')
    call_type = data.get('call_type') or data.get('type', 'voice')
    if call_type == "audio": call_type = "voice"
    
    try:
        service = await get_calling_service_v2()
        call_session = await service.initiate_call(
            caller_id=user_id_from_conn, receiver_id=receiver_id, call_type=call_type
        )
        call_data = {
            "type": "call_incoming", "call_id": call_session.id,
            "caller_id": user_id_from_conn, "call_type": call_type,
            "caller_sid": sid, "from_sid": sid
        }
        await redis_pubsub.publish("user", receiver_id, "incoming_call", call_data)
        await sio.emit('call:incoming', call_data, room=f"user_{receiver_id}")
        return {'success': True, 'call_id': call_session.id}
    except Exception as e:
        logger.error(f"Call initiation failed: {e}")
        return {'error': str(e)}

@sio.on("call:accept")
async def answer_call(sid, data):
    user_id = connected_users.get(sid, {}).get('user_id')
    call_id = data.get('call_id')
    try:
        service = await get_calling_service_v2()
        call_session = await service.accept_call(call_id=call_id, receiver_id=user_id)
        ans_data = {"call_id": call_id, "receiver_id": user_id}
        await redis_pubsub.publish("user", call_session.caller_id, "call_answered", ans_data)
        await sio.emit('call:accept', ans_data, room=f"user_{call_session.caller_id}")
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
        rej_data = {"call_id": call_id, "reason": reason}
        await redis_pubsub.publish("user", call_session.caller_id, "call_rejected", rej_data)
        await sio.emit('call:reject', rej_data, room=f"user_{call_session.caller_id}")
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
        other_id = call_session.receiver_id if user_id == call_session.caller_id else call_session.caller_id
        end_data = {"call_id": call_id, "ended_by": user_id}
        await redis_pubsub.publish("user", other_id, "call_ended", end_data)
        await sio.emit('call:end', end_data, room=f"user_{other_id}")
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
            other_id = call_session.receiver_id if user_id == call_session.caller_id else call_session.caller_id
            offer_data = {"call_id": call_id, "offer": offer, "from_user_id": user_id}
            await sio.emit('webrtc:offer', offer_data, room=f"user_{other_id}")
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
            other_id = call_session.receiver_id if user_id == call_session.caller_id else call_session.caller_id
            ans_data = {"call_id": call_id, "answer": answer, "from_user_id": user_id}
            await sio.emit('webrtc:answer', ans_data, room=f"user_{other_id}")
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
            other_id = call_session.receiver_id if user_id == call_session.caller_id else call_session.caller_id
            ice_data = {"call_id": call_id, "candidate": candidate, "from_user_id": user_id}
            await redis_pubsub.publish("user", other_id, "ice_candidate", ice_data)
            await sio.emit('webrtc:ice-candidate', ice_data, room=f"user_{other_id}")
            return {'success': True}
    except Exception as e:
        return {'error': str(e)}
"""

import re
# Regex to remove old calling events
start_token = "# CALLING EVENTS (Aligned with socket.js)"
end_token = "# MATCH EVENTS"
before, rest = code.split(start_token, 1)
_, after = rest.split(end_token, 1)

code = before + start_token + "\n# ============================================\n" + calling_logic_new + "\n# ============================================\n" + end_token + after

code = code.replace("await sio.emit('message_received',", "await sio.emit('message:read',")

with open("backend/socket_server.py", "w") as f:
    f.write(code)

