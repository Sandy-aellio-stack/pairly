# Luveloop - Production-Grade Real-Time Communication System

## 🚀 Overview

Luveloop is a comprehensive real-time communication system built for production environments. It supports instant messaging, audio/video calls, media sharing, and works seamlessly across web and mobile platforms.

## ✨ Key Features

### 📱 Real-Time Messaging
- **Instant message delivery** via Socket.IO
- **Typing indicators** for better UX
- **Read receipts** and delivery status
- **Message history** with MongoDB persistence
- **Offline notifications** via FCM

### 📞 Audio/Video Calling
- **WebRTC-based** peer-to-peer calls
- **STUN/TURN server** support for NAT traversal
- **Call signaling** via Socket.IO
- **Call quality tracking** and billing integration
- **Background call handling** on mobile

### 🖼️ Media Sharing
- **Image upload** to cloud storage
- **AWS S3, Cloudflare R2, Supabase** support
- **Unique filename generation**
- **Content validation** and security
- **CDN-ready URLs**

### 🌐 Platform Support
- **React** for web applications
- **React Native** for mobile apps
- **Progressive Web App** compatible
- **Responsive design** with Tailwind CSS

## 🏗️ Architecture

### Backend Stack
```
FastAPI (Python) + Socket.IO
├── MongoDB (Database)
├── Redis (Pub/Sub & Caching)
├── JWT Authentication
├── FCM Push Notifications
└── S3/Cloudflare R2 Storage
```

### Frontend Stack
```
React (Web) / React Native (Mobile)
├── Socket.IO Client
├── WebRTC for Calls
├── Tailwind CSS (Styling)
├── Firebase (Push Notifications)
└── Axios (HTTP Client)
```

## 📡 Socket Events

### Messaging Events
```javascript
// Send a message
socket.emit('message:send', {
  receiver_id: 'user123',
  content: 'Hello!',
  type: 'text'
})

// Receive new message
socket.on('message:new', (data) => {
  // data: { id, sender_id, content, type, created_at, status }
})

// Typing indicators
socket.emit('message:typing', { receiver_id: 'user123' })
socket.emit('message:stop-typing', { receiver_id: 'user123' })

// Read receipts
socket.emit('message:read', { sender_id: 'user123' })
```

### Calling Events
```javascript
// Initiate call
socket.emit('call:initiate', {
  targetUserId: 'user123',
  call_type: 'video',
  offer: webrtcOffer
})

// Incoming call
socket.on('call:incoming', (data) => {
  // data: { call_id, caller_id, call_type, offer }
})

// WebRTC signaling
socket.emit('webrtc:offer', { call_id, offer })
socket.emit('webrtc:answer', { call_id, answer })
socket.emit('webrtc:ice-candidate', { call_id, candidate })
```

### Presence Events
```javascript
// User online/offline
socket.on('user:online', (data) => {
  // data: { user_id }
})

socket.on('user:offline', (data) => {
  // data: { user_id, last_seen }
})
```

## 🗄️ Database Schema

### MongoDB Collections

#### Users Collection
```javascript
{
  _id: ObjectId,
  name: String,
  email: String,
  password_hash: String,
  profile_picture_url: String,
  is_online: Boolean,
  last_seen_at: Date,
  fcm_tokens: [String],
  settings: {
    privacy: {
      show_online: Boolean
    },
    notifications: {
      messages: Boolean,
      calls: Boolean
    }
  },
  created_at: Date,
  updated_at: Date
}
```

#### Messages Collection
```javascript
{
  _id: ObjectId,
  sender_id: ObjectId,
  receiver_id: ObjectId,
  content: String,
  media_url: String,
  message_type: String, // 'text' | 'image'
  status: String, // 'sent' | 'delivered' | 'read'
  is_read: Boolean,
  read_at: Date,
  created_at: Date
}
```

#### Conversations Collection
```javascript
{
  _id: ObjectId,
  participants: [ObjectId], // [user1_id, user2_id]
  last_message: String,
  last_message_at: Date,
  last_sender_id: ObjectId,
  unread_count: {
    user_id: Number
  },
  created_at: Date,
  updated_at: Date
}
```

#### Call Sessions Collection
```javascript
{
  _id: ObjectId,
  caller_id: String,
  receiver_id: String,
  status: String, // 'initiated' | 'ringing' | 'connected' | 'ended'
  call_type: String, // 'voice' | 'video'
  initiated_at: Date,
  connected_at: Date,
  ended_at: Date,
  duration_seconds: Number,
  credits_spent: Number,
  metadata: Object
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
MONGODB_URL=mongodb://localhost:27017/luveloop
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRE_MINUTES=30

# Storage (AWS S3 / Cloudflare R2 / Supabase)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_BUCKET_NAME=luveloop-media
AWS_REGION=us-east-1
AWS_ENDPOINT_URL=https://your-r2-account.r2.cloudflarestorage.com

# Push Notifications
FCM_SERVER_KEY=your-fcm-server-key

# TURN Server (for WebRTC)
TURN_SERVER_URL=turn:your-turn-server.com:3478
TURN_USERNAME=your-turn-username
TURN_PASSWORD=your-turn-password
```

## 🚀 Deployment

### Docker Setup
```bash
# Build and run with Docker Compose
docker-compose up -d

# Production deployment
docker-compose -f docker-compose.production.yml up -d
```

### Health Checks
- `/api/health` - Basic health check
- `/api/health/detailed` - Comprehensive service status
- `/api/health/redis` - Redis connection status

## 🔒 Security Features

- **JWT Authentication** for all socket connections
- **Token Blacklist** support for forced logout
- **Rate Limiting** on all endpoints
- **CORS Protection** with environment-based origins
- **Security Headers** (HSTS, CSP, etc.)
- **Input Validation** and sanitization
- **Content Moderation** for media uploads

## 📱 Mobile Integration

### React Native Setup
```bash
# Install required packages
npm install socket.io-client react-native-webrtc
npm install @react-native-async-storage/async-storage
npm install react-native-permissions
```

### Permissions (iOS/Android)
- Camera & Microphone access
- Background app refresh
- Push notifications
- Network access

## 🌍 Scaling

### Redis Pub/Sub
The system uses Redis pub/sub for horizontal scaling:
- **messages channel** - Real-time messaging
- **calls channel** - WebRTC signaling
- **presence channel** - User online/offline status

Multiple server instances can run simultaneously, with Redis handling cross-instance communication.

### Load Balancing
- Use sticky sessions for Socket.IO
- Configure health checks
- Enable auto-scaling based on CPU/memory

## 📊 Monitoring

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking and alerting
- Performance metrics

### Metrics
- Connection counts
- Message throughput
- Call success rates
- Storage usage

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest backend/tests/

# Test socket connections
python test_socket.py

# Test messaging
python backend_test_messaging_v2.py
```

### Frontend Tests
```bash
# Run React tests
npm test

# E2E testing with Cypress
npm run cypress:run
```

## 📚 Documentation

- [WebRTC Configuration Guide](./WEBRTC_CONFIGURATION.md)
- [API Documentation](./docs/api.md)
- [Deployment Guide](./docs/deployment.md)
- [Security Best Practices](./docs/security.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

---

**Built with ❤️ for real-time communication**
