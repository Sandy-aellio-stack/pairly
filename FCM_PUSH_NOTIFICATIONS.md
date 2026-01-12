# TrueBond Push Notifications (FCM) Implementation

## Overview

Firebase Cloud Messaging (FCM) push notifications have been implemented for the TrueBond application. The implementation is:
- **Backend-first**: All notification logic runs on the server
- **Non-blocking**: Notifications are fire-and-forget, never blocking user flows
- **Socket-aware**: Skips push if user is active on WebSocket
- **Idempotent**: Each event generates at most one notification

## Notification Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `new_message` | When a message is sent via REST API | `{ event_type, reference_id (message_id), sender_id, sender_name, click_action: "OPEN_CHAT" }` |
| `new_match` | When two users mutually match | `{ event_type, reference_id (match_id), matched_user_id, matched_user_name, click_action: "OPEN_MATCH" }` |
| `incoming_call` | When a call is initiated | `{ event_type, reference_id (call_id), caller_id, caller_name, call_type, click_action: "ANSWER_CALL" }` |

## FCM Token Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     FCM TOKEN LIFECYCLE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User Login/Signup                                           │
│     └─► App requests notification permission                    │
│         └─► Firebase SDK generates FCM token                    │
│             └─► App sends token to backend                      │
│                 POST /api/users/fcm-token { token }             │
│                                                                 │
│  2. Token Refresh (automatic by Firebase)                       │
│     └─► Firebase SDK generates new token                        │
│         └─► App sends new token to backend                      │
│             POST /api/users/fcm-token { token }                 │
│                                                                 │
│  3. User Logout                                                 │
│     └─► App calls DELETE /api/users/fcm-token { token }         │
│         └─► Backend removes token from user's list              │
│                                                                 │
│  4. Delivery Failure                                            │
│     └─► Backend auto-removes invalid tokens                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Socket vs Push Decision Logic

```
┌─────────────────┬───────────────────┬──────────────┐
│ Event Type      │ User on Socket?   │ Send Push?   │
├─────────────────┼───────────────────┼──────────────┤
│ new_message     │ Yes               │ No           │
│ new_message     │ No                │ Yes          │
│ new_match       │ Yes               │ No           │
│ new_match       │ No                │ Yes          │
│ incoming_call   │ Yes               │ Yes (always) │
│ incoming_call   │ No                │ Yes          │
└─────────────────┴───────────────────┴──────────────┘
```

**Rationale:**
- **Messages**: If user is connected via WebSocket, they receive real-time updates, so push is redundant
- **Matches**: Same as messages - real-time updates via socket
- **Calls**: Always send push because user might have app open but not looking at screen, and calls are time-sensitive

## API Endpoints

### Register FCM Token
```http
POST /api/users/fcm-token
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "token": "fcm_device_token_string"
}

Response (200):
{
  "message": "FCM token registered",
  "registered": true,
  "device_count": 1
}
```

### Unregister FCM Token
```http
DELETE /api/users/fcm-token
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "token": "fcm_device_token_string"
}

Response (200):
{
  "message": "FCM token removed",
  "removed": true,
  "device_count": 0
}
```

### Unregister All Tokens
```http
DELETE /api/users/fcm-tokens/all
Authorization: Bearer <jwt_token>

Response (200):
{
  "message": "All FCM tokens removed",
  "removed": 3
}
```

## User Notification Settings

Users can control which notifications they receive via the settings API:

```http
PUT /api/users/settings
{
  "notifications": {
    "messages": true,    // Push for new messages
    "matches": true,     // Push for new matches
    "calls": true,       // Push for incoming calls (recommended: always on)
    "nearby": false,     // Push for nearby users
    "marketing": false   // Marketing/promotional push
  }
}
```

## Backend Files

| File | Purpose |
|------|---------|
| `backend/services/fcm_service.py` | Core FCM service with send logic |
| `backend/models/tb_user.py` | Extended with `fcm_tokens` field |
| `backend/routes/tb_users.py` | FCM token CRUD endpoints |
| `backend/services/tb_message_service.py` | Triggers message notifications |
| `backend/routes/calling_v2.py` | Triggers call notifications |

## Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/services/fcm.js` | FCM initialization & token management |
| `frontend/src/services/api.js` | API methods for FCM endpoints |
| `frontend/src/store/authStore.js` | FCM init on login, cleanup on logout |

## Configuration

### Backend (.env)
```env
# Optional: FCM Server Key for production
# Leave empty for test mode (logs notifications instead of sending)
FCM_SERVER_KEY=your_fcm_server_key
```

### Frontend (.env)
```env
# Optional: Firebase configuration
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_FIREBASE_VAPID_KEY=your_vapid_key
```

## Test Mode

When `FCM_SERVER_KEY` is not set:
- Backend logs notifications instead of sending to FCM
- Format: `[FCM-TEST] Would send to token xxx...: Title - Body`
- Useful for development and testing

## Integration Points

1. **Message Sending** (`tb_message_service.py`):
   - After message is persisted and credits deducted
   - Calls `fcm_service.notify_new_message()` via `asyncio.create_task()` (non-blocking)

2. **Call Initiation** (`calling_v2.py`):
   - After call session is created
   - Calls `fcm_service.notify_incoming_call()` via `asyncio.create_task()` (non-blocking)

3. **Match Creation** (to be implemented):
   - When matching system creates a mutual match
   - Should call `fcm_service.notify_new_match()` for both users

## Security Considerations

- FCM tokens are stored per-user (max 5 tokens for multiple devices)
- Tokens are automatically invalidated on failed delivery
- User notification preferences are always respected
- No sensitive data included in push payloads (only IDs and names)
