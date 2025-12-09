from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from backend.database import init_db
from backend.services.presence import start_presence_monitor
from backend.routes import (
    auth,
    twofa,
    profiles,
    discovery,
    messaging,
    credits,
    payments,
    payouts,
    media,
    admin_security,
    admin_analytics,
    posts,
    feed,
    subscriptions,
    webhooks,
    compliance,
    calls,
    matchmaking
)
from backend.admin.routes import admin_payouts
from backend.routes import admin_security_enhanced, admin_analytics_enhanced, admin_users
from backend.routes import payments_enhanced
from backend.middleware.rate_limiter import RateLimiterMiddleware
from backend.middleware.content_moderation import ContentModerationMiddleware
from backend.middleware.request_logger import RequestLoggerMiddleware
from backend.middleware.security_headers import SecurityHeadersMiddleware
from backend.core.redis_client import redis_client
from backend.core.logging_config import LoggingConfig
from backend.core.security_validator import SecurityValidator
from backend.config import settings

# Initialize logging
logger = logging.getLogger('main')

app = FastAPI(title="Pairly Dating SaaS API", version="1.0.0")

# Get CORS origins
def get_cors_origins():
    cors_str = settings.CORS_ORIGINS
    if cors_str:
        return [origin.strip() for origin in cors_str.split(',')]
    
    # Default origins by environment
    env = settings.ENVIRONMENT
    if env == 'production':
        return [settings.FRONTEND_URL]
    else:
        return [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            settings.FRONTEND_URL
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggerMiddleware)

# Rate limiting
app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    ban_threshold_per_minute=settings.RATE_LIMIT_BAN_THRESHOLD,
    ban_seconds=settings.RATE_LIMIT_BAN_DURATION
)

# Content Moderation Middleware
app.add_middleware(ContentModerationMiddleware)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting Pairly API - Environment: {settings.ENVIRONMENT}")
    
    # Run security validation
    try:
        SecurityValidator.validate_all()
    except Exception as e:
        logger.error(f"Security validation failed: {str(e)}")
        if settings.ENVIRONMENT == 'production':
            raise
    
    # Initialize database
    logger.info("Initializing database connection")
    await init_db()
    
    # Connect to Redis
    logger.info("Connecting to Redis")
    await redis_client.connect()
    
    # Start presence monitor
    logger.info("Starting presence monitor")
    await start_presence_monitor()
    
    logger.info("Pairly API startup completed successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Pairly API")
    await redis_client.disconnect()
    logger.info("Shutdown complete")

app.include_router(auth.router)
app.include_router(twofa.router)
app.include_router(profiles.router)
app.include_router(discovery.router)
app.include_router(messaging.router)
app.include_router(credits.router)
app.include_router(payments.router)
app.include_router(payments_enhanced.router)  # Phase 8.1: Enhanced payments
app.include_router(payouts.router)
app.include_router(media.router)
app.include_router(posts.router)
app.include_router(feed.router)
app.include_router(subscriptions.router)
app.include_router(webhooks.router)
app.include_router(admin_payouts.router)
app.include_router(admin_security.router)
app.include_router(admin_analytics.router)
app.include_router(admin_security_enhanced.router)
app.include_router(admin_analytics_enhanced.router)
app.include_router(admin_users.router)
app.include_router(compliance.router)
app.include_router(calls.router)
app.include_router(matchmaking.router)

@app.get("/api")
async def root():
    return {"status": "ok", "message": "Pairly Dating SaaS API v1.0", "service": "pairly"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "pairly"}