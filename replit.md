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
- Payment integration (Stripe, Razorpay)

## Environment Variables Required
- `MONGO_URL`: MongoDB connection string (Atlas or local)
- `JWT_SECRET`: Secret for JWT tokens
- `STRIPE_SECRET_KEY`: For payments (optional)
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`: For Indian payments (optional)
- `REDIS_URL`: Redis connection string (optional)

## API Endpoints
- `/api/auth/*`: Authentication (signup, login, OTP)
- `/api/users/*`: User profile management
- `/api/messages/*`: Messaging
- `/api/credits/*`: Credits balance and history
- `/api/location/*`: Location updates and nearby users
- `/api/health`: Health check

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
