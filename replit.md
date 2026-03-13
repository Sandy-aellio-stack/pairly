# Luveloop - Dating App

## Overview
Luveloop is a full-stack dating application with a React frontend and Python FastAPI backend, featuring real-time chat and WebRTC-based audio/video calling.

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
- Run: `cd frontend && node_modules/.bin/vite --host 0.0.0.0 --port 5000`

### Backend
- Framework: FastAPI with uvicorn
- Database: MongoDB (via motor/beanie)
- Real-time: python-socketio (integrated with FastAPI)
- Additional: Redis (caching/rate limiting, optional - graceful degradation if unavailable)
- Run: `PYTHONPATH=/home/runner/workspace uv run uvicorn backend.main:socket_app --host localhost --port 8000 --reload`

## Key Features
- JWT-based authentication with secure token handling
- OTP login (email/phone) with single-device enforcement (force-logout previous device)
- Credit-based messaging (1 coin/msg, 5 coins/min voice, 10 coins/min video)
- Real-time chat using Socket.IO (socket URL fixed to connect to backend port 8000)
- Audio/video calling with WebRTC (signaling via Socket.IO) with per-minute credit billing
- Periodic call billing worker (60s tick) that force-ends calls if credits run dry
- Real-time location/nearby users (`photo` field added to both nearby API endpoints)
- Admin panel with analytics
- Payment integration (Stripe, mock mode enabled)
- Unit test coverage: 34 tests across location service and OTP service

## Environment Variables
All configuration is stored in `backend/.env` and `frontend/.env`.

### Backend (`backend/.env`)
- `MONGO_URL`: MongoDB Atlas connection string
- `JWT_SECRET`: Secret for JWT tokens
- `REDIS_URL`: Redis connection string (optional, falls back gracefully)
- `FRONTEND_URL`: Frontend URL for CORS
- `CORS_ORIGINS`: Allowed origins for CORS
- `ADMIN_EMAIL` / `ADMIN_PASSWORD`: Admin panel credentials
- `PAYMENTS_ENABLED` / `PAYMENTS_MOCK_MODE`: Payment system config
- `EMAIL_ENABLED`: Email service toggle

### Frontend (`frontend/.env`)
- `VITE_API_URL`: Backend API URL (points to port 8000 of the Replit domain)
- `VITE_MAPBOX_PUBLIC_KEY`: Mapbox public key for maps

## API Endpoints
- `/api/auth/*`: Authentication (signup, login, OTP)
- `/api/users/*`: User profile management
- `/api/messages/*`: Messaging
- `/api/credits/*`: Credits balance and history
- `/api/location/*`: Location updates and nearby users
- `/api/admin/*`: Admin panel (auth, users, analytics, moderation, settings)
- `/api/notifications/*`: User notifications (get, mark read)
- `/api/health`: Health check

## Admin Panel
- Login: `/admin` (credentials in backend/.env: ADMIN_EMAIL / ADMIN_PASSWORD)
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
- 2026-03-13: Migrated to Replit environment
  - Installed frontend dependencies via npm --legacy-peer-deps
  - Updated Frontend workflow to use local vite binary
  - Created backend/.env and frontend/.env with all required config
  - Fixed dotenv to use override=True so .env file takes priority over env vars
  - Set CORS origins and FRONTEND_URL to Replit dev domain
  - Set ENVIRONMENT=development for compatibility
  - Redis runs via Upstash (graceful degradation if unavailable)
