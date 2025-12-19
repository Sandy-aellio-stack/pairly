from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import os

from backend.models.tb_user import TBUser
from backend.models.app_settings import AppSettings

router = APIRouter(prefix="/api/admin", tags=["TrueBond Admin Auth"])
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "truebond-admin-secret")
ADMIN_TOKEN_EXPIRY = 24  # hours

# Hardcoded demo admin credentials (in production, use database)
DEMO_ADMINS = {
    "admin@truebond.com": {
        "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        "name": "Super Admin",
        "role": "super_admin"
    },
    "moderator@truebond.com": {
        "password_hash": bcrypt.hashpw("mod123".encode(), bcrypt.gensalt()).decode(),
        "name": "Moderator",
        "role": "moderator"
    }
}


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    admin_name: str
    admin_role: str


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify admin JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "admin":
            raise HTTPException(status_code=401, detail="Invalid admin token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(data: AdminLoginRequest):
    """Admin login"""
    admin = DEMO_ADMINS.get(data.email)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(data.password.encode(), admin["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate admin token
    token_payload = {
        "email": data.email,
        "name": admin["name"],
        "role": admin["role"],
        "type": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=ADMIN_TOKEN_EXPIRY)
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
    
    return AdminTokenResponse(
        access_token=token,
        admin_name=admin["name"],
        admin_role=admin["role"]
    )


@router.get("/me")
async def get_admin_profile(admin: dict = Depends(get_current_admin)):
    """Get current admin info"""
    return {
        "email": admin["email"],
        "name": admin["name"],
        "role": admin["role"]
    }
