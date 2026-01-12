# TrueBond - Dating App PRD

## Product Overview
TrueBond is a credit-based dating application with real-time messaging, geolocation-based discovery, and video/audio calling features.

## Tech Stack
- **Backend**: FastAPI (Python), Beanie ODM
- **Frontend**: React, Vite, Tailwind CSS, Zustand
- **Database**: MongoDB
- **Real-time**: Socket.IO with Redis Pub/Sub
- **Authentication**: JWT (Access & Refresh tokens)

## Core Features

### Implemented ✅
1. **User Authentication**
   - Signup/Login with email & password
   - JWT-based auth with refresh tokens
   - OTP verification flow
   - Password reset with secure tokens

2. **User Profiles**
   - Profile creation and editing
   - Photo uploads (base64, max 5 photos)
   - Preferences (age, gender, distance)
   - Privacy and safety settings

3. **Credit System**
   - 10 free credits on signup
   - Credit packages (Stripe/Razorpay)
   - Transaction history
   - Webhook handling for payments

4. **Real-time Messaging**
   - WebSocket with Redis Pub/Sub
   - REST API fallback
   - Typing indicators
   - Read receipts

5. **Geolocation & Discovery**
   - Live location updates
   - Nearby users with privacy controls
   - Distance bucketing for privacy

6. **Push Notifications (FCM)** - NEW
   - Device token registration (multi-device)
   - Event-driven notifications
   - Socket-aware (skip push if user online)
   - Notification settings per type

7. **Admin Dashboard**
   - User management
   - Analytics
   - Moderation tools
   - Settings management

### Partially Implemented 🔄
1. **Video/Audio Calling**
   - UI exists
   - Call initiation route exists
   - WebRTC signaling NOT complete
   - STUN/TURN NOT configured

2. **Matching System**
   - Models exist
   - Recommendation pipeline skeleton
   - Mutual like/match NOT implemented

### Not Implemented ❌
1. **Cloud Storage** - Photos stored as base64, not scalable
2. **2FA** - Models exist, integration incomplete
3. **Advanced Matchmaking** - Basic discovery only
4. **Push for Matches** - Ready in FCM service, needs match event trigger

## API Endpoints (Key)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/signup` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/auth/forgot-password` | POST | Initiate password reset |
| `/api/users/profile/{id}` | GET | View user profile |
| `/api/users/fcm-token` | POST/DELETE | FCM token management |
| `/api/messages/send` | POST | Send message |
| `/api/location/nearby` | GET | Get nearby users |
| `/api/v2/calls/initiate` | POST | Start a call |
| `/webhooks/stripe` | POST | Stripe webhook |
| `/webhooks/razorpay` | POST | Razorpay webhook |

## Data Models (Key)

### TBUser
```
{
  name, age, gender, bio,
  profile_pictures: [],
  email, mobile_number, password_hash,
  preferences: { interested_in, min_age, max_age, max_distance_km },
  settings: { notifications, privacy, safety },
  fcm_tokens: [],  // NEW
  credits_balance,
  location: GeoJSON,
  is_online, is_verified, is_active
}
```

## Session: January 12, 2026

### Completed Today
- ✅ Implemented FCM Push Notifications (backend + frontend)
  - Created `fcm_service.py` with non-blocking notification sending
  - Extended TBUser model with `fcm_tokens` field
  - Added `calls` to NotificationSettings
  - Added FCM token CRUD endpoints
  - Integrated notifications into message and call flows
  - Created frontend FCM service with Firebase SDK
  - Updated authStore for FCM init/cleanup

### Files Modified/Created
- `backend/services/fcm_service.py` (NEW)
- `backend/models/tb_user.py` (MODIFIED)
- `backend/routes/tb_users.py` (MODIFIED)
- `backend/services/tb_message_service.py` (MODIFIED)
- `backend/routes/calling_v2.py` (MODIFIED)
- `frontend/src/services/fcm.js` (NEW)
- `frontend/src/services/api.js` (MODIFIED)
- `frontend/src/store/authStore.js` (MODIFIED)
- `FCM_PUSH_NOTIFICATIONS.md` (NEW - Documentation)

## Backlog

### P0 (Blocking for Launch)
- None currently blocking

### P1 (High Priority)
- WebRTC Calling System (signaling + STUN/TURN)
- Cloud Storage for Photos (AWS S3)
- Complete Matching System with mutual likes

### P2 (Medium Priority)
- 2FA Integration
- Improve Test Coverage
- Rate limiting enhancements

### P3 (Low Priority/Future)
- Advanced Matchmaking Algorithm
- Analytics Dashboard Improvements
- Delete legacy route files

## Environment Variables

### Backend
```env
MONGO_URL=mongodb://...
JWT_SECRET=...
REDIS_URL=redis://...
FCM_SERVER_KEY=... (optional for test mode)
STRIPE_SECRET_KEY=...
RAZORPAY_KEY_ID=...
```

### Frontend
```env
VITE_API_URL=...
VITE_FIREBASE_API_KEY=... (optional for FCM)
VITE_FIREBASE_PROJECT_ID=...
```

## Test Credentials
- Admin: admin@truebond.com / TrueBond@Admin2026!
