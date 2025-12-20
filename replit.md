# TrueBond - Dating App

## Overview
TrueBond is a full-stack dating application with a React frontend and Python FastAPI backend.

## Project Structure
- **frontend/**: React + Vite application (port 5000)
- **backend/**: Python FastAPI backend with MongoDB
- **docs/**: Project documentation
- **infra/**: Infrastructure configuration (Kubernetes, Prometheus)

## Development Setup

### Frontend
- Framework: React 19 with Vite
- Styling: TailwindCSS
- State: Zustand
- UI Components: Radix UI + custom components
- Run: `cd frontend && yarn dev`

### Backend
- Framework: FastAPI with uvicorn
- Database: MongoDB (via motor/beanie)
- Additional: Redis (caching/rate limiting), Celery (background tasks)
- Run: `cd backend && uvicorn main:app --host localhost --port 8000`

## Key Features
- User authentication with OTP
- Credit-based messaging system
- Real-time location/nearby users
- Video/audio calling
- Admin panel with analytics
- Payment integration (Stripe, Razorpay)

## Environment Variables Required
- `MONGODB_URL`: MongoDB connection string
- `JWT_SECRET`: Secret for JWT tokens
- `STRIPE_SECRET_KEY`: For payments
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`: For Indian payments
- `REDIS_URL`: Redis connection string

## Recent Changes
- 2025-12-20: Initial Replit setup - configured frontend to run on port 5000
