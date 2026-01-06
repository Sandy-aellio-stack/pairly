# TrueBond - Dating App

## Overview
TrueBond is a full-stack dating application with a React frontend and Python FastAPI backend, featuring real-time chat and WebRTC-based audio/video calling.

## Project Structure
- **frontend/**: React + Vite application (port 5000)
- **backend/**: Python FastAPI backend with MongoDB and Socket.IO
- **docs/**: Project documentation
- **infra/**: Infrastructure configuration (Kubernetes, Prometheus)

## Development Setup

### Frontend
- Framework: React 19 with Vite
- Styling: TailwindCSS
- State: Zustand
- UI Components: Radix UI + custom components
- Real-time: socket.io-client
- Run: `cd frontend && yarn dev`

### Backend
- Framework: FastAPI with uvicorn
- Database: MongoDB (via motor/beanie)
- Real-time: python-socketio (integrated with FastAPI)
- Additional: Redis (caching/rate limiting), Celery (background tasks)
- Run: `PYTHONPATH=/home/runner/workspace uvicorn backend.main:socket_app --host localhost --port 8000`

## Key Features
- JWT-based authentication with secure token handling
- OTP verification for phone numbers
- Credit-based messaging system
- Real-time chat using Socket.IO
- Audio/video calling with WebRTC (signaling via Socket.IO)
- Real-time location/nearby users
- Admin panel with analytics
- Payment integration (Stripe only)

## Environment Variables Required
- `MONGO_URL`: MongoDB connection string (Atlas or local)
- `JWT_SECRET`: Secret for JWT tokens
- `STRIPE_SECRET_KEY`: Stripe secret key for payments
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook secret for credit fulfillment
- `REDIS_URL`: Redis connection string (for rate limiting, caching, sessions)

## API Endpoints
- `/api/auth/*`: Authentication (signup, login, OTP)
- `/api/users/*`: User profile management
- `/api/messages/*`: Messaging
- `/api/credits/*`: Credits balance and history
- `/api/location/*`: Location updates and nearby users
- `/api/admin/*`: Admin panel (auth, users, analytics, moderation, settings)
- `/api/health`: Health check

## Admin Panel
- Login: `/admin` (Demo credentials shown on login page)
- Dashboard with user stats and activity
- User management (view, suspend, reactivate)
- Analytics with charts (user growth, demographics, revenue)
- Moderation queue for reported content
- App settings (pricing, matching preferences, safety features)

## Socket.IO Events
### Client -> Server
- `join_chat`: Join a chat room with another user
- `send_message`: Send a message
- `typing/stop_typing`: Typing indicators
- `call_user`: Initiate WebRTC call
- `answer_call`: Answer incoming call
- `reject_call`: Reject incoming call
- `end_call`: End active call
- `ice_candidate`: Exchange ICE candidates

### Server -> Client
- `new_message`: New message received
- `user_typing/user_stopped_typing`: Typing indicators
- `incoming_call`: Incoming call notification
- `call_answered`: Call was answered
- `call_rejected`: Call was rejected
- `call_ended`: Call ended
- `ice_candidate`: ICE candidate from peer

## Recent Changes
- 2025-12-20: Initial Replit setup - configured frontend to run on port 5000
- 2025-12-20: Added Socket.IO server for real-time features
- 2025-12-20: Implemented WebRTC signaling for audio/video calls
- 2025-12-20: Added OTP verification page and flow
- 2025-12-20: Fixed MongoDB connection with TLS/certifi
- 2025-12-20: Fixed admin API URL to use same origin (was incorrectly pointing to localhost:8001)
- 2025-12-20: Fixed cursor visibility issue (removed custom cursor:none CSS)
- 2025-12-20: Fixed backend LSP errors in admin routes (TBCreditTransaction model, null checks)
- 2025-12-20: Connected all admin panel pages to real backend APIs
- 2025-12-20: Added user settings API (notifications, privacy, safety preferences)
- 2025-12-20: Updated Settings page with Privacy & Safety sections connected to backend
- 2025-12-20: Updated Credits page to match landing page design style
- 2025-12-20: Implemented heart-only cursor on desktop (hides system cursor)
- 2025-12-20: Fixed Privacy & Safety button in Profile page to navigate to Settings
- 2025-12-20: Fixed missing HeartCursor imports in static pages (Privacy, Terms, About, Contact, Blog, Careers, Help)
- 2025-12-20: All footer links now working (Privacy Policy, Terms, Contact, About, etc.)
- 2025-12-20: Synced backend payment packages to match landing page pricing (₹100/100, ₹450/500, ₹800/1000 coins)
- 2025-12-20: Enabled demo credit purchases (auto-verifies mock payments and adds credits)
- 2026-01-06: Production Hardening - Removed Razorpay, standardized on Stripe-only payments
- 2026-01-06: Added webhook-only credit system with idempotency (credits ONLY added via Stripe webhooks)
- 2026-01-06: Added Redis-based rate limiting middleware for sensitive endpoints
- 2026-01-06: Added security headers middleware (X-Content-Type-Options, X-Frame-Options, HSTS)
- 2026-01-06: Added centralized error handling - no stack traces in production
- 2026-01-06: Enhanced OTP system with rate limiting (3 sends/hour, 5 verify attempts)
- 2026-01-06: Added database indexes for payments collection
- 2026-01-06: Socket.IO already has JWT validation on connect
- 2026-01-06: Server-side call billing worker already in place with credit checks

## Production Security Features
- Stripe webhook signature verification (mandatory)
- Idempotency keys for payment processing (prevents duplicate credits)
- Rate limiting on login, signup, OTP, and payment endpoints
- Security headers (Content-Security-Policy, HSTS in production)
- JWT validation on all Socket.IO connections
- RBAC enforcement on admin routes
- Centralized error handling with production-safe responses
- Server-authoritative call billing with auto-end on insufficient credits
