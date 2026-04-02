"""
Luveloop - Dating App Backend
Production-ready FastAPI backend with MongoDB
"""
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory (override=True ensures .env values take priority)
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging

from backend.tb_database import init_db, close_db
from backend.socket_server import sio
from backend.core.redis_client import redis_client
from backend.core.redis_pubsub import redis_pubsub
from backend.core.security_config import security_config, validate_security_config
from backend.middleware.security import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware
)

from backend.routes.tb_auth import router as auth_router
from backend.routes.health import router as health_router
# Removed legacy_auth_router
from backend.routes.tb_users import router as users_router
from backend.routes.tb_location import router as location_router
from backend.routes.tb_messages import router as messages_router
from backend.routes.tb_credits import router as credits_router
from backend.routes.tb_payments import router as payments_router

from backend.routes.tb_notifications import router as notifications_router
from backend.routes.tb_search import router as search_router
from backend.routes.calling_v2 import router as calling_v2_router
from backend.routes.user_settings import router as settings_router

from backend.routes.tb_admin_auth import router as admin_auth_router
from backend.routes.tb_admin_users import router as admin_users_router
from backend.routes.tb_admin_analytics import router as admin_analytics_router
from backend.routes.tb_admin_settings import router as admin_settings_router
from backend.routes.tb_admin_moderation import router as admin_moderation_router

from backend.routes.webhooks import router as webhooks_router
from backend.mock_auth import router as mock_auth_router
from backend.core.env_validator import validate_or_exit
from backend.middleware.exception_handlers import setup_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("luveloop")

# Validate environment variables at startup
validate_or_exit()

# Validate security configuration
security_valid, security_errors = validate_security_config()
if not security_valid:
    logger.critical("Security configuration validation failed:")
    for error in security_errors:
        logger.critical(f"  ❌ {error}")
    if security_config.is_production:
        import sys
        sys.exit(1)
else:
    logger.info("Security configuration validated successfully")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

mongo_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global mongo_client
    mongo_client = await init_db()
    await redis_client.connect()
    try:
        logger.info(f"Redis client ready: {redis_client.is_connected()}")
    except Exception as e:
        logger.warning(f"Redis client check failed: {e}")
    
    # Initialize WebSocket Redis Pub/Sub for real-time messaging
    from backend.socket_server import init_websocket_pubsub
    try:
        await init_websocket_pubsub()
    except Exception as e:
        logger.warning(f"Redis PubSub initialization failed: {e}")
    try:
        logger.info(f"Redis PubSub ready: {redis_pubsub.is_connected()}")
    except Exception as e:
        logger.warning(f"Redis PubSub check failed: {e}")

    # Start periodic call billing worker
    import asyncio
    from backend.workers.call_billing_worker import call_billing_worker
    billing_task = asyncio.create_task(call_billing_worker())

    logger.info("Application startup complete")
    yield

    billing_task.cancel()
    try:
        await billing_task
    except asyncio.CancelledError:
        pass
    await close_db(mongo_client)
    
    # Disconnect Redis Pub/Sub
    from backend.core.redis_pubsub import redis_pubsub
    await redis_pubsub.disconnect()
    
    await redis_client.disconnect()


fastapi_app = FastAPI(
    title="Luveloop API",
    description="Dating App Backend - Credit-based messaging with live location",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None
)

# CORS Configuration - Environment-based
# Uses security_config which automatically configures based on ENVIRONMENT
logger.info(f"CORS configuration: origins={security_config.cors_origins}, env={ENVIRONMENT}")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.cors_origins,
    allow_credentials=security_config.cors_allow_credentials,
    allow_methods=security_config.cors_allow_methods,
    allow_headers=security_config.cors_allow_headers,
    max_age=security_config.cors_max_age,
)

fastapi_app.add_middleware(SecurityHeadersMiddleware)
fastapi_app.add_middleware(RequestLoggingMiddleware)
fastapi_app.add_middleware(RateLimitMiddleware)

# Setup comprehensive exception handlers
setup_exception_handlers(fastapi_app)


fastapi_app.include_router(health_router)
fastapi_app.include_router(auth_router)
fastapi_app.include_router(users_router)
fastapi_app.include_router(location_router)
fastapi_app.include_router(messages_router)
fastapi_app.include_router(credits_router)
fastapi_app.include_router(payments_router)
fastapi_app.include_router(notifications_router)
fastapi_app.include_router(settings_router)
fastapi_app.include_router(search_router)
fastapi_app.include_router(calling_v2_router)
fastapi_app.include_router(webhooks_router)

# Standardize Admin Routers
fastapi_app.include_router(admin_auth_router)
fastapi_app.include_router(admin_users_router)
fastapi_app.include_router(admin_analytics_router)
fastapi_app.include_router(admin_settings_router)
fastapi_app.include_router(admin_moderation_router)

# Mock auth for development/testing only
if ENVIRONMENT == "development":
    fastapi_app.include_router(mock_auth_router)
    logger.info("Mock auth enabled (development mode)")




@fastapi_app.get("/api/health/redis")
async def health_check_redis():
    """Check Redis connection and operations"""
    health = await redis_client.health_check()

    status_code = 200
    if health["status"] == "unhealthy" or health["status"] == "disconnected":
        status_code = 503
    elif health["status"] == "degraded":
        status_code = 200

    return JSONResponse(
        status_code=status_code,
        content=health
    )


@fastapi_app.get("/api/health/detailed")
async def health_check_detailed():
    """Detailed health check for all services"""
    redis_health = await redis_client.health_check()

    # Check MongoDB
    mongo_status = "unknown"
    try:
        if mongo_client:
            await mongo_client.admin.command('ping')
            mongo_status = "connected"
        else:
            mongo_status = "disconnected"
    except Exception as e:
        mongo_status = f"error: {str(e)}"

    overall_status = "healthy"
    if redis_health["status"] in ["unhealthy", "disconnected"] or mongo_status != "connected":
        overall_status = "degraded"

    return {
        "status": overall_status,
        "service": "luveloop",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "services": {
            "redis": redis_health,
            "mongodb": {
                "status": mongo_status,
                "connected": mongo_status == "connected"
            },
            "api": {
                "status": "healthy",
                "connected": True
            }
        }
    }


@fastapi_app.get("/")
async def root():
    return {
        "app": "Luveloop",
        "version": "1.0.0",
        "docs": "/docs" if ENVIRONMENT != "production" else None,
        "health": "/api/health"
    }

# ============================================
# SOCKET.IO INTEGRATION
# ============================================
import socketio
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
socket_app = app  # Alias expected by the workflow runner
