"""
TrueBond - Dating App Backend
Production-ready FastAPI backend with MongoDB
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from backend.tb_database import init_db, close_db

# Import TrueBond routes
from backend.routes.tb_auth import router as auth_router
from backend.routes.tb_users import router as users_router
from backend.routes.tb_location import router as location_router
from backend.routes.tb_messages import router as messages_router
from backend.routes.tb_credits import router as credits_router
from backend.routes.tb_payments import router as payments_router

# MongoDB client reference
mongo_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global mongo_client
    # Startup
    mongo_client = await init_db()
    print("🚀 TrueBond Backend Started")
    yield
    # Shutdown
    await close_db(mongo_client)


app = FastAPI(
    title="TrueBond API",
    description="Dating App Backend - Credit-based messaging with live location",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("ENV") == "development" else "Something went wrong"
        }
    )


# Register TrueBond routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(location_router)
app.include_router(messages_router)
app.include_router(credits_router)
app.include_router(payments_router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "truebond",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    return {
        "app": "TrueBond",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }
