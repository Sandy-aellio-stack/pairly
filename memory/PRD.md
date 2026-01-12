# TrueBond - Dating App PRD

## Product Overview
TrueBond is a credit-based dating application with real-time messaging, geolocation-based discovery, and video/audio calling features.

**Completion Status:** ~70-75% production-ready

## Tech Stack
- **Backend**: FastAPI (Python), Beanie ODM
- **Frontend**: React, Vite, Tailwind CSS, Zustand
- **Database**: MongoDB (Atlas M10+ recommended for production)
- **Real-time**: Socket.IO with Redis Pub/Sub
- **Authentication**: JWT (Access & Refresh tokens)
- **Payments**: Stripe + Razorpay
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **Media Storage**: AWS S3 (planned)

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

### Backend (REQUIRED)
```env
# Core
MONGO_URL=mongodb+srv://...
DB_NAME=truebond
JWT_SECRET=<64-char-secret>
REDIS_URL=redis://...
ENVIRONMENT=production
FRONTEND_URL=https://app.truebond.com
CORS_ALLOWED_ORIGINS=https://app.truebond.com

# Admin
ADMIN_EMAIL=admin@truebond.com
ADMIN_PASSWORD=<strong-password>

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...

# Push Notifications
FCM_SERVER_KEY=AAAA...

# SMS/OTP
FONOSTER_API_KEY=...
# OR Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...

# Email
EMAIL_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG....

# Media Storage
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=truebond-uploads
S3_REGION=us-east-1

# Monitoring (Optional)
SENTRY_DSN=...
```

### Frontend (REQUIRED)
```env
VITE_API_URL=https://api.truebond.com
VITE_FIREBASE_API_KEY=AIza...
VITE_FIREBASE_AUTH_DOMAIN=truebond.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=truebond
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc
VITE_FIREBASE_VAPID_KEY=BLc4...
```

## Test Credentials
- Admin: admin@truebond.com / TrueBond@Admin2026!

## Full Audit Report
See `/app/TRUEBOND_FULL_AUDIT_REPORT.md` for complete audit with API keys list and infrastructure requirements.
