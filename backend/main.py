from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    admin_analytics
)
from backend.middleware.rate_limiter import RateLimiterMiddleware
import os

app = FastAPI(title="Pairly Dating SaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=60,
    ban_threshold_per_minute=150,
    ban_seconds=3600
)

@app.on_event("startup")
async def startup_event():
    await init_db()
    await start_presence_monitor()

app.include_router(auth.router)
app.include_router(twofa.router)
app.include_router(profiles.router)
app.include_router(discovery.router)
app.include_router(messaging.router)
app.include_router(credits.router)
app.include_router(payments.router)
app.include_router(payouts.router)
app.include_router(media.router)
app.include_router(admin_security.router)
app.include_router(admin_analytics.router)

@app.get("/api")
async def root():
    return {"status": "ok", "message": "Pairly Dating SaaS API v1.0", "service": "pairly"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "pairly"}