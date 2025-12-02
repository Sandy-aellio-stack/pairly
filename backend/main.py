from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.services.presence import start_presence_monitor
from backend.routes import auth, twofa, admin_security, admin_analytics, payments
from backend.middleware.rate_limiter import RateLimiterMiddleware

app = FastAPI(title="Dating SaaS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimiterMiddleware, requests_per_minute=30, ban_threshold_per_minute=150, ban_seconds=3600)

@app.on_event("startup")
async def startup_event():
    await init_db()
    await start_presence_monitor()

app.include_router(auth.router)
app.include_router(twofa.router)
app.include_router(payments.router)
app.include_router(admin_security.router)
app.include_router(admin_analytics.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Dating SaaS API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}