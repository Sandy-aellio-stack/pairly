# Real-Time Messaging Implementation Guide

**Last Updated:** January 12, 2026
**TrueBond Backend Version:** 1.0.0

---

## Overview

TrueBond uses **Socket.IO** for real-time messaging features including:
- ✅ Instant message delivery
- ✅ Online/offline presence
- ✅ Typing indicators
- ✅ Read receipts
- ✅ Delivery confirmations

The system uses a **hybrid approach**: REST APIs for guaranteed delivery with credit deduction, and WebSockets for real-time notifications.

---

## Architecture

### Hybrid Messaging Flow

```
┌─────────────┐                    ┌──────────────┐                    ┌─────────────┐
│   Client A  │                    │   Backend    │                    │  Client B   │
│  (Sender)   │                    │              │                    │ (Receiver)  │
└─────────────┘                    └──────────────┘                    └─────────────┘
       │                                   │                                   │
       │  1. POST /api/messages/send      │                                   │
       │  (REST API with credit deduct)   │                                   │
       ├──────────────────────────────────>│                                   │
       │                                   │                                   │
       │  2. Message saved to DB           │                                   │
       │     Credits deducted              │                                   │
       │                                   │                                   │
       │  3. REST Response                 │                                   │
       │<──────────────────────────────────┤                                   │
       │                                   │                                   │
       │                                   │  4. WebSocket: new_message        │
       │                                   ├──────────────────────────────────>│
       │                                   │     (real-time delivery)          │
       │                                   │                                   │
       │                                   │  5. WebSocket: message_delivered  │
       │<──────────────────────────────────┤───────────────────────────────────┤
       │                                   │                                   │
```

**Key Points:**
- Messages are ALWAYS sent via REST API (guarantees persistence & credits)
- WebSocket delivers messages in real-time to connected users
- If receiver is offline, message waits in DB until they fetch via REST API

---

## Connection & Authentication

### 1. WebSocket Connection

**Client connects with JWT token:**

```javascript
import io from 'socket.io-client';

const socket = io('https://api.truebond.com', {
  auth: {
    token: accessToken  // JWT access token from login
  },
  transports: ['websocket'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});
```

### 2. Connection Events

**On successful connection:**
```javascript
socket.on('connect', () => {
  console.log('Connected to WebSocket');
  console.log('Socket ID:', socket.id);
});
```

**On connection error:**
```javascript
socket.on('connect_error', (error) => {
  console.error('Connection failed:', error.message);
  // Reasons: invalid token, expired token, blacklisted token
});
```

**On disconnection:**
```javascript
socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason);
  // Socket.IO will automatically attempt to reconnect
});
```

### 3. Authentication Security

**Backend validates:**
- ✅ Token is valid JWT
- ✅ Token is not expired
- ✅ Token is not blacklisted (after logout)
- ✅ User tokens are not globally blacklisted
- ✅ User account is active

**If auth fails:**
- Connection is rejected
- Client receives `connect_error` event
- Client should refresh token or redirect to login

---

## Sending Messages

### Recommended: REST API + WebSocket Delivery

**Always use REST API to send messages:**

```javascript
// 1. Send via REST API (guarantees credit deduction & persistence)
const response = await fetch('/api/messages/send', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    receiver_id: receiverUserId,
    content: 'Hello!'
  })
});

const result = await response.json();

if (response.ok) {
  console.log('Message sent:', result.message_id);
  // Message will be delivered in real-time via WebSocket
  // if receiver is connected
} else if (response.status === 402) {
  // Insufficient credits
  showBuyCreditsModal();
} else {
  console.error('Failed to send:', result.error);
}
```

**Backend automatically emits WebSocket event to receiver:**
```javascript
// Receiver gets this event in real-time
socket.on('new_message', (message) => {
  console.log('New message received:', message);
  // message = {
  //   id: 'message_id',
  //   sender_id: 'user_id',
  //   receiver_id: 'your_user_id',
  //   content: 'Hello!',
  //   is_read: false,
  //   created_at: '2026-01-12T10:30:00Z'
  // }

  addMessageToUI(message);
  playNotificationSound();
});
```

### Alternative: WebSocket-Only (Dev/Testing)

**For development or testing, you can send via WebSocket:**

```javascript
socket.emit('send_message_realtime', {
  receiver_id: receiverUserId,
  content: 'Hello!'
}, (response) => {
  if (response.success) {
    console.log('Message sent:', response.message_id);
  } else if (response.code === 402) {
    showBuyCreditsModal();
  } else {
    console.error('Error:', response.error);
  }
});
```

**⚠️ Production Recommendation:** Use REST API for sending, WebSocket for receiving.

---

## Real-Time Features

### 1. Presence (Online/Offline Status)

**Automatic presence updates:**
- User marked online on WebSocket connect
- User marked offline when all their connections disconnect
- `last_seen_at` timestamp updated on disconnect

**Listen for presence changes:**

```javascript
// User came online
socket.on('user_online', (data) => {
  console.log('User online:', data.user_id);
  updateUserStatus(data.user_id, 'online');
});

// User went offline
socket.on('user_offline', (data) => {
  console.log('User offline:', data.user_id);
  console.log('Last seen:', data.last_seen);
  updateUserStatus(data.user_id, 'offline', data.last_seen);
});
```

**Check user status via REST API:**
```javascript
const response = await fetch(`/api/users/profile/${userId}`, {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
const user = await response.json();

console.log('Is online:', user.is_online);
console.log('Last seen:', user.last_seen_at);
```

### 2. Typing Indicators

**Notify when user starts typing:**

```javascript
// User starts typing
function onUserStartTyping(receiverId) {
  socket.emit('typing', {
    receiver_id: receiverId
  });
}

// User stops typing (after 3 seconds of no input)
function onUserStopTyping(receiverId) {
  socket.emit('stop_typing', {
    receiver_id: receiverId
  });
}

// Listen for typing events
socket.on('user_typing', (data) => {
  console.log('User typing:', data.user_id);
  showTypingIndicator(data.user_id);
});

socket.on('user_stopped_typing', (data) => {
  console.log('User stopped typing:', data.user_id);
  hideTypingIndicator(data.user_id);
});
```

**Best Practices:**
- Debounce typing events (don't emit on every keystroke)
- Auto-stop typing after 3 seconds of inactivity
- Clear typing indicator on message send
- Clear typing indicator on conversation leave

**Example implementation:**

```javascript
let typingTimeout = null;
let isTyping = false;

function handleTyping(receiverId) {
  // Start typing if not already
  if (!isTyping) {
    socket.emit('typing', { receiver_id: receiverId });
    isTyping = true;
  }

  // Reset stop typing timer
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => {
    socket.emit('stop_typing', { receiver_id: receiverId });
    isTyping = false;
  }, 3000);
}

function handleSendMessage(receiverId, content) {
  // Stop typing when sending
  if (isTyping) {
    socket.emit('stop_typing', { receiver_id: receiverId });
    isTyping = false;
  }

  // Send message via REST API
  sendMessage(receiverId, content);
}
```

### 3. Read Receipts

**Mark messages as read:**

```javascript
// Option 1: REST API (recommended for multiple messages)
await fetch(`/api/messages/read/${otherUserId}`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// Option 2: WebSocket (real-time)
socket.emit('mark_read_realtime', {
  other_user_id: otherUserId
}, (response) => {
  console.log('Marked as read:', response.marked_read);
});
```

**Listen for read receipts:**

```javascript
socket.on('messages_read', (data) => {
  console.log('Messages read by:', data.reader_id);
  console.log('Count:', data.count);
  console.log('Read at:', data.read_at);

  // Update UI: show double check marks
  updateMessagesReadStatus(data.reader_id);
});
```

### 4. Delivery Confirmations

**Mark message as delivered:**

```javascript
socket.on('new_message', (message) => {
  // Display message
  addMessageToUI(message);

  // Notify sender that message was delivered
  socket.emit('mark_delivered', {
    message_id: message.id
  });
});
```

**Listen for delivery confirmations:**

```javascript
socket.on('message_delivered', (data) => {
  console.log('Message delivered:', data.message_id);
  console.log('Delivered at:', data.delivered_at);

  // Update UI: show single check mark
  updateMessageDeliveryStatus(data.message_id);
});
```

---

## Conversation Management

### 1. Join Conversation

**Join conversation room to receive messages:**

```javascript
socket.emit('join_conversation', {
  other_user_id: otherUserId
}, (response) => {
  if (response.success) {
    console.log('Joined room:', response.room_id);
  } else {
    console.error('Failed to join:', response.error);
    // Reasons: Access denied, invalid user ID, user deactivated
  }
});
```

**When to join:**
- User opens a conversation
- User navigates to chat page
- User clicks on a message notification

### 2. Leave Conversation

**Leave conversation room:**

```javascript
socket.emit('leave_conversation', {
  room_id: roomId
}, (response) => {
  console.log('Left conversation');
});
```

**When to leave:**
- User closes conversation
- User navigates away from chat
- User switches to different conversation

### 3. Authorization

**Backend automatically verifies:**
- ✅ Both users exist
- ✅ Both users are active (not deactivated)
- ✅ Users are not the same person
- ✅ Conversation access is authorized

**Access denied reasons:**
- User trying to message themselves
- User account deactivated
- Other user account deactivated
- Invalid user ID

---

## Message Notifications

### In-App Notifications

**Listen for notification events:**

```javascript
socket.on('new_message_notification', (data) => {
  console.log('New message from:', data.sender_id);
  console.log('Sender name:', data.sender_name);
  console.log('Preview:', data.content_preview);

  // Show notification if user is on different page
  if (currentPage !== '/chat/' + data.sender_id) {
    showNotification({
      title: `New message from ${data.sender_name}`,
      body: data.content_preview,
      onClick: () => navigateTo('/chat/' + data.sender_id)
    });
  }
});
```

### Push Notifications (Future)

For offline users, implement push notifications:
- Firebase Cloud Messaging (FCM)
- Apple Push Notification Service (APNS)
- Web Push API

---

## Error Handling

### Connection Errors

```javascript
socket.on('connect_error', (error) => {
  console.error('Connection error:', error.message);

  // Try to refresh token
  const newToken = await refreshAccessToken();

  if (newToken) {
    // Reconnect with new token
    socket.auth.token = newToken;
    socket.connect();
  } else {
    // Redirect to login
    window.location.href = '/login?session_expired=true';
  }
});
```

### Message Send Errors

```javascript
socket.emit('send_message_realtime', data, (response) => {
  if (response.error) {
    if (response.code === 402) {
      // Insufficient credits
      showError('You need more credits to send messages');
      showBuyCreditsButton();
    } else if (response.error === 'Access denied') {
      // User blocked or deactivated
      showError('Cannot send message to this user');
    } else {
      // Generic error
      showError('Failed to send message. Please try again.');
    }
  }
});
```

### Reconnection Handling

```javascript
socket.on('reconnect', (attemptNumber) => {
  console.log('Reconnected after', attemptNumber, 'attempts');

  // Rejoin any active conversations
  if (currentConversation) {
    socket.emit('join_conversation', {
      other_user_id: currentConversation.userId
    });
  }
});

socket.on('reconnect_failed', () => {
  console.error('Failed to reconnect');
  showError('Connection lost. Please refresh the page.');
});
```

---

## Best Practices

### 1. Always Use REST API for Sending

✅ **DO:**
```javascript
// Send via REST API
const response = await fetch('/api/messages/send', {
  method: 'POST',
  body: JSON.stringify({ receiver_id, content })
});

// Listen for real-time delivery
socket.on('new_message', handleNewMessage);
```

❌ **DON'T:**
```javascript
// Don't rely solely on WebSocket for sending
socket.emit('send_message_realtime', { receiver_id, content });
// What if connection drops? Message may be lost!
```

**Why:**
- REST API guarantees database persistence
- REST API guarantees credit deduction
- WebSocket is for real-time delivery, not persistence

### 2. Handle Connection States

```javascript
let isConnected = false;
let messageQueue = [];

socket.on('connect', () => {
  isConnected = true;
  // Send any queued messages
  messageQueue.forEach(msg => sendMessage(msg));
  messageQueue = [];
});

socket.on('disconnect', () => {
  isConnected = false;
});

function sendMessage(data) {
  if (isConnected) {
    // Send immediately via WebSocket
    socket.emit('send_message_realtime', data);
  } else {
    // Queue for later or use REST API
    messageQueue.push(data);
    // Or: send via REST API immediately (recommended)
    sendViaRestAPI(data);
  }
}
```

### 3. Debounce Typing Events

```javascript
import { debounce } from 'lodash';

const emitTyping = debounce((receiverId) => {
  socket.emit('typing', { receiver_id: receiverId });
}, 300);

function handleInputChange(receiverId, value) {
  if (value.length > 0) {
    emitTyping(receiverId);
  }
}
```

### 4. Clean Up on Unmount

```javascript
useEffect(() => {
  // Setup listeners
  socket.on('new_message', handleNewMessage);
  socket.on('user_typing', handleTyping);

  // Cleanup
  return () => {
    socket.off('new_message', handleNewMessage);
    socket.off('user_typing', handleTyping);

    // Leave conversation room
    if (roomId) {
      socket.emit('leave_conversation', { room_id: roomId });
    }
  };
}, []);
```

### 5. Sync State on Reconnect

```javascript
socket.on('reconnect', async () => {
  // Fetch any missed messages
  const since = lastMessageTimestamp;
  const missedMessages = await fetchMessagesSince(since);

  // Update UI
  missedMessages.forEach(addMessageToUI);

  // Rejoin conversations
  if (currentConversation) {
    socket.emit('join_conversation', {
      other_user_id: currentConversation.userId
    });
  }
});
```

---

## Testing Real-Time Messaging

### Unit Tests

**Test WebSocket events:**

```javascript
import { io } from 'socket.io-client';

describe('WebSocket Messaging', () => {
  let socket;
  const testToken = 'valid_jwt_token';

  beforeAll((done) => {
    socket = io('http://localhost:8001', {
      auth: { token: testToken }
    });
    socket.on('connect', done);
  });

  afterAll(() => {
    socket.disconnect();
  });

  test('should connect with valid token', () => {
    expect(socket.connected).toBe(true);
  });

  test('should send message', (done) => {
    socket.emit('send_message_realtime', {
      receiver_id: 'test_user_id',
      content: 'Test message'
    }, (response) => {
      expect(response.success).toBe(true);
      expect(response.message_id).toBeDefined();
      done();
    });
  });

  test('should receive typing event', (done) => {
    socket.on('user_typing', (data) => {
      expect(data.user_id).toBe('test_user_id');
      done();
    });

    // Trigger typing from another connection
    anotherSocket.emit('typing', { receiver_id: myUserId });
  });
});
```

### Manual Testing

**Test checklist:**
- [ ] Connect with valid token
- [ ] Connection rejected with invalid token
- [ ] Connection rejected with expired token
- [ ] Send message via REST API, receive via WebSocket
- [ ] Send message via WebSocket (optional)
- [ ] Typing indicators appear and disappear
- [ ] Online/offline status updates
- [ ] Read receipts work
- [ ] Delivery confirmations work
- [ ] Reconnection works after disconnect
- [ ] Multiple browser tabs/devices sync
- [ ] Messages delivered to offline users when they reconnect
- [ ] Access denied for blocked/deactivated users

---

## WebSocket Events Reference

### Client → Server

| Event | Data | Response | Description |
|-------|------|----------|-------------|
| `connect` | `{auth: {token}}` | Boolean | Authenticate and connect |
| `join_conversation` | `{other_user_id}` | `{success, room_id}` | Join conversation room |
| `leave_conversation` | `{room_id}` | `{success}` | Leave conversation room |
| `send_message_realtime` | `{receiver_id, content}` | `{success, message_id}` | Send message (optional) |
| `typing` | `{receiver_id}` | - | Notify typing started |
| `stop_typing` | `{receiver_id}` | - | Notify typing stopped |
| `mark_read_realtime` | `{other_user_id}` | `{success, marked_read}` | Mark messages as read |
| `mark_delivered` | `{message_id}` | `{success}` | Mark message delivered |

### Server → Client

| Event | Data | Description |
|-------|------|-------------|
| `connect` | - | Connection successful |
| `connect_error` | `{message}` | Connection failed |
| `disconnect` | `{reason}` | Connection closed |
| `reconnect` | `{attemptNumber}` | Reconnected after disconnect |
| `new_message` | `{id, sender_id, receiver_id, content, is_read, created_at}` | New message received |
| `new_message_notification` | `{message_id, sender_id, sender_name, content_preview, created_at}` | New message notification |
| `user_typing` | `{user_id, timestamp}` | User started typing |
| `user_stopped_typing` | `{user_id, timestamp}` | User stopped typing |
| `user_online` | `{user_id}` | User came online |
| `user_offline` | `{user_id, last_seen}` | User went offline |
| `messages_read` | `{reader_id, count, read_at}` | Messages marked as read |
| `message_delivered` | `{message_id, delivered_at}` | Message delivered to recipient |

---

## Performance Optimization

### 1. Connection Pooling

Use singleton socket instance:

```javascript
// socket.js
let socketInstance = null;

export function getSocket(token) {
  if (!socketInstance) {
    socketInstance = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket']
    });
  }
  return socketInstance;
}

export function disconnectSocket() {
  if (socketInstance) {
    socketInstance.disconnect();
    socketInstance = null;
  }
}
```

### 2. Message Batching

Batch multiple operations:

```javascript
// Instead of marking each message individually
messages.forEach(msg => markAsRead(msg.id));

// Batch mark all messages from user
markAllAsRead(otherUserId);
```

### 3. Lazy Loading

Load conversations on demand:

```javascript
// Don't load all messages on page load
// Load initial messages
fetchRecentMessages(otherUserId, limit=50);

// Load more on scroll
onScrollTop(() => {
  fetchOlderMessages(otherUserId, before=oldestMessageId);
});
```

---

## Security Considerations

### 1. Token Validation

- ✅ JWT validated on every connection
- ✅ Token blacklist checked (after logout)
- ✅ Expired tokens rejected
- ✅ User account status verified

### 2. Authorization

- ✅ Users can only access their own conversations
- ✅ Conversation access verified on every action
- ✅ Cannot send to deactivated users
- ✅ Cannot send to self

### 3. Rate Limiting

WebSocket rate limiting (future enhancement):
- Limit messages per minute
- Limit typing events per minute
- Temporary ban on abuse

### 4. Input Validation

- ✅ Message content length (1-2000 chars)
- ✅ User ID format validation
- ✅ XSS protection (sanitize HTML)
- ✅ No script injection

---

## Troubleshooting

### Connection Issues

**Problem:** Can't connect to WebSocket

**Solutions:**
1. Check token is valid: `jwt.decode(token)`
2. Check token not expired: `exp > Date.now()`
3. Check token not blacklisted (after logout)
4. Check firewall/proxy allows WebSocket
5. Try REST API to verify credentials

### Messages Not Delivering

**Problem:** Messages not appearing in real-time

**Solutions:**
1. Check WebSocket connection: `socket.connected`
2. Check joined conversation room
3. Check receiver is online: `user.is_online`
4. Fallback: Fetch via REST API
5. Check browser console for errors

### Typing Indicators Not Working

**Problem:** Typing indicators not showing

**Solutions:**
1. Check conversation access authorized
2. Check debounce delay not too long
3. Check auto-stop timeout not too short
4. Verify event listeners registered
5. Check receiver is connected

### Presence Not Updating

**Problem:** Online/offline status not updating

**Solutions:**
1. Check WebSocket connection
2. Check database `is_online` field
3. Check presence update function
4. Verify multiple connections handled
5. Check last_seen_at timestamp

---

## Migration from Polling to WebSocket

If currently using polling:

```javascript
// Before: Polling every 5 seconds
setInterval(() => {
  fetchNewMessages();
}, 5000);

// After: WebSocket
socket.on('new_message', (message) => {
  addMessageToUI(message);
});

// Benefits:
// - Instant delivery (no 5s delay)
// - Reduced server load (no constant polling)
// - Lower bandwidth (no repeated requests)
// - Better user experience
```

---

## Summary

**Real-Time Messaging Architecture:**
- ✅ WebSocket for real-time delivery
- ✅ REST API for guaranteed persistence
- ✅ JWT authentication with blacklist checking
- ✅ Automatic presence tracking
- ✅ Typing indicators
- ✅ Read receipts and delivery confirmations
- ✅ Conversation authorization
- ✅ Reconnection handling

**Production Ready:**
- ✅ Secure authentication
- ✅ Authorization checks
- ✅ Error handling
- ✅ Reconnection logic
- ✅ Multiple device support
- ✅ Offline message queuing (via REST API)

**Next Steps:**
- Implement frontend Socket.IO client
- Add message persistence layer
- Setup push notifications for offline users
- Add message encryption (E2E)
- Implement message reactions
- Add file/image sharing

---

*For backend implementation details, see `/backend/socket_server.py`*
*For REST API reference, see `/docs/BACKEND_ARCHITECTURE.md`*
