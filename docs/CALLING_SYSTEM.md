# WebRTC Calling System Documentation

## Overview

Pairly's WebRTC calling system enables real-time voice/video calls between users with per-minute credit billing, comprehensive signaling, and moderation hooks.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    WebRTC Call Flow                          │
└──────────────────────────────────────────────────────────────┘

Caller                  Signaling Server              Receiver
  │                            │                          │
  │──POST /api/call/start──────▶│                          │
  │   (offer SDP)               │                          │
  │                            │──WebSocket: call_incoming─▶│
  │                            │   (offer SDP)              │
  │                            │                          │
  │                            │◀──POST /api/call/accept───│
  │                            │   (answer SDP)             │
  │◀──WebSocket: call_accepted─│                          │
  │   (answer SDP)              │                          │
  │                            │                          │
  │◀────────ICE candidates─────┼─────────────────────────▶│
  │                            │                          │
  │──POST /api/call/connected──▶│                          │
  │                            │──Start Billing Ticker────▶│
  │                            │   (every 60 seconds)      │
  │                            │                          │
  │◀─────────Media (P2P)──────────────────────────────────▶│
  │                            │                          │
  │──POST /api/call/end────────▶│                          │
  │                            │──WebSocket: call_ended───▶│
  │                            │──Finalize Billing────────▶│
```

## Components

### 1. Call Session Model (`CallSession`)

Stores call state and metadata.

```python
class CallSession(Document):
    # Participants
    caller_id: PydanticObjectId
    receiver_id: PydanticObjectId
    
    # State
    status: CallStatus  # initiating, ringing, accepted, active, ended, etc.
    
    # Timestamps
    initiated_at: datetime
    accepted_at: Optional[datetime]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    
    # Billing
    duration_seconds: int
    billed_seconds: int
    cost_per_minute: int = 5
    total_cost: int
    
    # Signaling
    offer_sdp: Optional[str]
    answer_sdp: Optional[str]
    ice_candidates: list
    
    # Moderation
    flagged_for_moderation: bool
    moderation_notes: Optional[str]
```

**Call Status:**
- `INITIATING` - Call offer sent
- `RINGING` - Receiver notified
- `ACCEPTED` - Receiver accepted
- `ACTIVE` - Media flowing
- `ENDED` - Normal end
- `REJECTED` - Receiver rejected
- `CANCELLED` - Caller cancelled
- `FAILED` - Technical failure
- `INSUFFICIENT_CREDITS` - Auto-ended (no credits)

### 2. Call Signaling Service

Manages WebRTC signaling and state transitions.

**Key Methods:**
- `initiate_call()` - Start new call
- `accept_call()` - Accept incoming call
- `reject_call()` - Reject incoming call
- `start_call()` - Mark as active
- `end_call()` - End call
- `add_ice_candidate()` - Exchange ICE candidates
- `flag_for_moderation()` - Flag for review

**WebSocket Connection Management:**
```python
# Register user connection
active_connections[user_id] = websocket

# Send message to user
await send_to_user(user_id, {
    \"type\": \"call_incoming\",
    \"call_id\": \"...\",
    \"caller_id\": \"...\"
})
```

### 3. Call Billing Worker (Celery)

Background tasks for credit deduction.

**Tasks:**

#### `billing_tick_task(call_id)`
Runs every 60 seconds for active calls.

- Deducts `cost_per_minute` credits from caller
- Uses idempotency key: `call_{call_id}_minute_{n}`
- If insufficient credits → Auto-end call
- Schedules next tick

#### `finalize_call_task(call_id)`
Runs after call ends.

- Bills any remaining unbilled seconds
- Updates call statistics
- Sends post-call notifications

#### `fraud_check_task(call_id)` *(Stub)*
Detects suspicious patterns:
- Unusually long calls (> 2 hours)
- Rapid sequential calls
- High cost in short time

### 4. Call Routes API

**Base URL:** `/api/call`

#### Get ICE Configuration

```http
GET /api/call/ice

Response:
{
  \"iceServers\": [
    {
      \"urls\": [
        \"stun:stun.l.google.com:19302\",
        \"stun:stun1.l.google.com:19302\"
      ]
    }
  ],
  \"iceTransportPolicy\": \"all\",
  \"iceCandidatePoolSize\": 10
}
```

#### Start Call

```http
POST /api/call/start
Authorization: Bearer <token>
Content-Type: application/json

{
  \"receiver_id\": \"507f1f77bcf86cd799439011\",
  \"offer_sdp\": \"v=0\\r\\no=- ...\"
}

Response:
{
  \"call_id\": \"call_123\",
  \"status\": \"ringing\",
  \"receiver_id\": \"507f1f77bcf86cd799439011\",
  \"initiated_at\": \"2025-12-05T10:30:00Z\"
}
```

**Requirements:**
- Caller must have minimum 5 credits
- Receiver must be online (WebSocket connected)
- Neither user can be in another active call

#### Accept Call

```http
POST /api/call/accept
Authorization: Bearer <token>
Content-Type: application/json

{
  \"call_id\": \"call_123\",
  \"answer_sdp\": \"v=0\\r\\no=- ...\"
}

Response:
{
  \"call_id\": \"call_123\",
  \"status\": \"accepted\",
  \"accepted_at\": \"2025-12-05T10:30:15Z\"
}
```

#### Reject Call

```http
POST /api/call/reject
Authorization: Bearer <token>
Content-Type: application/json

{
  \"call_id\": \"call_123\",
  \"reason\": \"Not interested\"
}

Response:
{
  \"call_id\": \"call_123\",
  \"status\": \"rejected\",
  \"rejected_at\": \"2025-12-05T10:30:20Z\"
}
```

#### Mark Call as Connected

```http
POST /api/call/connected
Authorization: Bearer <token>
Content-Type: application/json

{
  \"call_id\": \"call_123\"
}

Response:
{
  \"call_id\": \"call_123\",
  \"status\": \"active\",
  \"started_at\": \"2025-12-05T10:30:25Z\"
}
```

**Effect:** Starts billing ticker (first tick in 60 seconds)

#### End Call

```http
POST /api/call/end
Authorization: Bearer <token>
Content-Type: application/json

{
  \"call_id\": \"call_123\",
  \"reason\": \"User ended call\"
}

Response:
{
  \"call_id\": \"call_123\",
  \"status\": \"ended\",
  \"duration_seconds\": 180,
  \"total_cost\": 15,
  \"ended_at\": \"2025-12-05T10:33:25Z\"
}
```

#### Get Call Logs

```http
GET /api/call/logs?limit=50&skip=0
Authorization: Bearer <token>

Response:
{
  \"calls\": [
    {
      \"call_id\": \"call_123\",
      \"caller_id\": \"...\",
      \"receiver_id\": \"...\",
      \"status\": \"ended\",
      \"duration_seconds\": 180,
      \"total_cost\": 15,
      \"initiated_at\": \"2025-12-05T10:30:00Z\",
      \"started_at\": \"2025-12-05T10:30:25Z\",
      \"ended_at\": \"2025-12-05T10:33:25Z\",
      \"end_reason\": \"User ended call\"
    }
  ],
  \"total\": 25,
  \"limit\": 50,
  \"skip\": 0
}
```

#### Flag Call (Admin)

```http
POST /api/call/admin/flag
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  \"call_id\": \"call_123\",
  \"reason\": \"Inappropriate content reported\"
}

Response:
{
  \"call_id\": \"call_123\",
  \"flagged\": true,
  \"reason\": \"Inappropriate content reported\"
}
```

### 5. WebSocket Signaling

**Endpoint:** `ws://localhost:8001/api/call/ws/{user_id}`

**Connection:**
```javascript
const ws = new WebSocket(`ws://localhost:8001/api/call/ws/${userId}`);

// Authenticate
ws.send(JSON.stringify({
  token: \"Bearer_token_here\"
}));

// Listen for events
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'connected':
      console.log('Connected to signaling server');
      break;
    
    case 'call_incoming':
      handleIncomingCall(message);
      break;
    
    case 'call_accepted':
      handleCallAccepted(message);
      break;
    
    case 'call_rejected':
      handleCallRejected(message);
      break;
    
    case 'call_ended':
      handleCallEnded(message);
      break;
    
    case 'ice_candidate':
      handleIceCandidate(message);
      break;
  }
};
```

**Events Received:**

#### `call_incoming`
```json
{
  \"type\": \"call_incoming\",
  \"call_id\": \"call_123\",
  \"caller_id\": \"507f1f77bcf86cd799439011\",
  \"offer_sdp\": \"v=0\\r\\n...\",
  \"timestamp\": \"2025-12-05T10:30:00Z\"
}
```

#### `call_accepted`
```json
{
  \"type\": \"call_accepted\",
  \"call_id\": \"call_123\",
  \"answer_sdp\": \"v=0\\r\\n...\",
  \"timestamp\": \"2025-12-05T10:30:15Z\"
}
```

#### `call_rejected`
```json
{
  \"type\": \"call_rejected\",
  \"call_id\": \"call_123\",
  \"reason\": \"Not interested\",
  \"timestamp\": \"2025-12-05T10:30:20Z\"
}
```

#### `call_ended`
```json
{
  \"type\": \"call_ended\",
  \"call_id\": \"call_123\",
  \"reason\": \"User ended call\",
  \"duration\": 180,
  \"timestamp\": \"2025-12-05T10:33:25Z\"
}
```

#### `ice_candidate`
```json
{
  \"type\": \"ice_candidate\",
  \"call_id\": \"call_123\",
  \"candidate\": {
    \"candidate\": \"candidate:...\",
    \"sdpMid\": \"0\",
    \"sdpMLineIndex\": 0
  },
  \"timestamp\": \"2025-12-05T10:30:05Z\"
}
```

**Sending ICE Candidates:**
```javascript
ws.send(JSON.stringify({
  type: \"ice_candidate\",
  call_id: \"call_123\",
  candidate: {
    candidate: \"candidate:...\",
    sdpMid: \"0\"
  }
}));
```

## Complete Call Flow

### Successful Call

```
1. Caller initiates call
   POST /api/call/start
   → Creates CallSession (status: RINGING)
   → WebSocket: call_incoming → Receiver

2. Receiver accepts
   POST /api/call/accept
   → Updates status: ACCEPTED
   → WebSocket: call_accepted → Caller

3. ICE candidates exchanged
   WebSocket: ice_candidate (both directions)

4. Media connected
   POST /api/call/connected
   → Updates status: ACTIVE
   → Starts billing ticker

5. Billing ticks every 60 seconds
   Celery: billing_tick_task
   → Deducts 5 credits from caller
   → Schedules next tick

6. Either user ends call
   POST /api/call/end
   → Updates status: ENDED
   → WebSocket: call_ended → Other user
   → Finalizes billing

7. Post-call finalization
   Celery: finalize_call_task
   → Bills remaining seconds
   → Updates statistics
```

### Rejected Call

```
1. Caller initiates
   POST /api/call/start
   → status: RINGING
   → WebSocket: call_incoming → Receiver

2. Receiver rejects
   POST /api/call/reject
   → Updates status: REJECTED
   → WebSocket: call_rejected → Caller
```

### Insufficient Credits

```
1-4. Normal call flow...

5. Billing tick fails (no credits)
   Celery: billing_tick_task
   → InsufficientCreditsError
   → Updates status: INSUFFICIENT_CREDITS
   → WebSocket: call_ended → Both users
```

## Billing Details

**Cost Structure:**
- **Base rate:** 5 credits per minute
- **Billing frequency:** Every 60 seconds
- **Partial minutes:** Billed on call end

**Example:**
- Call duration: 2 minutes 30 seconds
- Minute 1: 5 credits deducted (at 1:00)
- Minute 2: 5 credits deducted (at 2:00)
- Final 30 seconds: 2.5 credits deducted (on end)
- **Total:** 12.5 credits (rounded to 12 or 13)

**Idempotency:**
Each billing tick uses unique key:
```
call_{call_id}_minute_{minute_number}
```

Prevents duplicate charges on retry.

## Frontend Integration

### Complete Example

```javascript
// 1. Get ICE configuration
const iceConfig = await fetch('/api/call/ice').then(r => r.json());

// 2. Create RTCPeerConnection
const pc = new RTCPeerConnection(iceConfig);

// 3. Add local stream
const stream = await navigator.mediaDevices.getUserMedia({ 
  video: true, 
  audio: true 
});
stream.getTracks().forEach(track => pc.addTrack(track, stream));

// 4. Create offer
const offer = await pc.createOffer();
await pc.setLocalDescription(offer);

// 5. Start call
const response = await fetch('/api/call/start', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    receiver_id: receiverId,
    offer_sdp: offer.sdp
  })
});

const { call_id } = await response.json();

// 6. Send ICE candidates
pc.onicecandidate = (event) => {
  if (event.candidate) {
    ws.send(JSON.stringify({
      type: 'ice_candidate',
      call_id: call_id,
      candidate: event.candidate
    }));
  }
};

// 7. Handle answer
ws.onmessage = async (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'call_accepted') {
    await pc.setRemoteDescription(
      new RTCSessionDescription({
        type: 'answer',
        sdp: message.answer_sdp
      })
    );
  }
  
  if (message.type === 'ice_candidate') {
    await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
  }
};

// 8. Mark as connected when media flows
pc.oniceconnectionstatechange = async () => {
  if (pc.iceConnectionState === 'connected') {
    await fetch('/api/call/connected', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ call_id })
    });
  }
};

// 9. End call
async function endCall() {
  await fetch('/api/call/end', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      call_id,
      reason: 'User ended call'
    })
  });
  
  pc.close();
  stream.getTracks().forEach(track => track.stop());
}
```

## TURN Server Setup (Optional)

For production, configure a TURN server (Coturn):

### Install Coturn

```bash
sudo apt-get install coturn
```

### Configure `/etc/turnserver.conf`

```ini
listening-port=3478
external-ip=YOUR_SERVER_IP
realm=your-domain.com
fingerprint
lt-cred-mech
user=turn_user:turn_password
```

### Update ICE Config

```python
@router.get(\"/ice\")
async def get_ice_config():
    return {
        \"iceServers\": [
            {\"urls\": \"stun:stun.l.google.com:19302\"},
            {
                \"urls\": \"turn:your-turn-server.com:3478\",
                \"username\": \"turn_user\",
                \"credential\": \"turn_password\"
            }
        ]
    }
```

## Testing

Run comprehensive tests:

```bash
pytest backend/tests/test_calls.py -v
```

**Test Coverage:**
- ✅ Call initiation (success, offline, already in call)
- ✅ Call acceptance (success, wrong user, wrong status)
- ✅ Call rejection
- ✅ Call start
- ✅ Call end (success, not participant)
- ✅ Billing tick (success, insufficient credits)
- ✅ ICE candidate exchange
- ✅ Moderation flagging
- ✅ Call finalization with partial billing
- ✅ State machine full flow

## Monitoring

**Key Metrics:**
- Active calls count
- Average call duration
- Total minutes billed
- Insufficient credit rate
- Call completion rate
- Rejected call rate

**Alerts:**
- High failure rate
- Billing errors
- Unusually long calls
- WebSocket connection issues

## Security Considerations

1. **Authentication:** All endpoints require valid JWT token
2. **Authorization:** Users can only end their own calls
3. **Rate Limiting:** Prevent call spam
4. **Credit Checks:** Minimum balance before call start
5. **Idempotency:** Prevent duplicate billing
6. **Audit Logs:** All call events logged
7. **Moderation:** Flagging system for abuse

## Troubleshooting

### Call Not Connecting

1. Check ICE server configuration
2. Verify both users are online (WebSocket connected)
3. Check firewall rules
4. Test with TURN server

### Billing Not Working

1. Verify Celery worker is running
2. Check Redis connection
3. Verify user has credits
4. Check billing tick logs

### WebSocket Issues

1. Check WebSocket endpoint reachability
2. Verify authentication token
3. Check for connection drops
4. Monitor WebSocket logs

## Conclusion

Pairly's WebRTC calling system provides:
- ✅ Complete signaling infrastructure
- ✅ Per-minute credit billing
- ✅ Insufficient credit handling
- ✅ Moderation hooks
- ✅ Comprehensive testing
- ✅ Production-ready architecture

The system is scalable, well-tested, and ready for deployment.
