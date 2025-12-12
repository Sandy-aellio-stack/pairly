# Pairly Backend - Deployment Guide

## Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose installed
- Copy `.env.example` to `.env` and configure

### Deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual Setup
```bash
# Start services
docker-compose up -d --build

# Initialize MongoDB replica set (first time only)
docker exec -it $(docker ps -qf "ancestor=mongo:6.0") mongosh --eval 'rs.initiate()'
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Pairly Backend                       │
├─────────────────────────────────────────────────────────┤
│  Services:                                              │
│  ├── web (FastAPI/Uvicorn) - Port 8001                 │
│  ├── mongo (MongoDB 6.0 with ReplicaSet)               │
│  ├── redis (Redis 7 Alpine)                            │
│  └── celery (Background tasks)                         │
└─────────────────────────────────────────────────────────┘
```

## API Endpoints Summary

### Core Features
| Phase | Feature | Prefix | Status |
|-------|---------|--------|--------|
| 1-8 | Auth, Profiles, Messaging, Payments | /api/* | ✅ |
| 9 | Realtime Messaging V2 | /api/messaging/v2 | ✅ |
| 10 | Realtime Calling V2 | /api/calling/v2 | ✅ |
| 11 | Presence Engine | /api/presence | ✅ |
| 12 | Analytics & Insights | /api/analytics | ✅ |
| 13 | Notification Engine | /api/notifications | ✅ |
| 14 | QA & Hardening | Middleware | ✅ |
| 15 | Deployment Prep | Docker/Docs | ✅ |

### Health Check
```bash
curl http://localhost:8001/api/health
# {"status":"healthy","service":"pairly"}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| MONGO_URI | MongoDB connection string | mongodb://mongo:27017/pairly |
| REDIS_URL | Redis connection string | redis://redis:6379/0 |
| JWT_SECRET | JWT signing secret | (required) |
| PAYMENTS_MOCK_MODE | Enable payment mocking | true |
| PRESENCE_TTL | Presence heartbeat TTL (seconds) | 120 |
| PRESENCE_AWAY | Away threshold (seconds) | 300 |

## Testing

```bash
# Run all tests
pytest backend/tests -q

# Run with coverage
pytest backend/tests --cov=backend --cov-report=html
```

## Mock Mode

All services work without external infrastructure using in-memory fallbacks:
- Redis → In-memory cache
- Celery → Manual task triggers
- Payments → Mock responses

**Production requires full infrastructure setup via docker-compose.**

## Security Checklist

- [ ] Replace `JWT_SECRET` with strong secret
- [ ] Update CORS origins for production
- [ ] Enable HTTPS/TLS
- [ ] Configure rate limiting thresholds
- [ ] Set up Sentry for error tracking
- [ ] Run `pip-audit` for dependency vulnerabilities
