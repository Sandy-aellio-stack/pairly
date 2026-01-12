"""
Temporary mock authentication for testing without MongoDB
This allows testing the login UI while MongoDB is being set up
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timezone, timedelta
import bcrypt

router = APIRouter(prefix="/api/mock-auth", tags=["Mock Auth"])

# In-memory user storage (for testing only!)
MOCK_USERS = {}

JWT_SECRET = "test-secret-key"
JWT_ALGORITHM = "HS256"

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = "Test User"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/signup")
async def mock_signup(data: SignupRequest):
    if data.email in MOCK_USERS:
        raise HTTPException(status_code=400, detail="Email already registered")

    MOCK_USERS[data.email] = {
        "email": data.email,
        "password_hash": hash_password(data.password),
        "name": data.name,
        "credits_balance": 10
    }

    token = create_token(data.email)
    return {
        "message": "Account created successfully (MOCK MODE)",
        "user_id": data.email,
        "credits_balance": 10,
        "tokens": {
            "access_token": token,
            "refresh_token": token,
            "token_type": "bearer",
            "user_id": data.email
        }
    }

@router.post("/login")
async def mock_login(data: LoginRequest):
    user = MOCK_USERS.get(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(data.email)
    return {
        "message": "Login successful (MOCK MODE)",
        "user_id": data.email,
        "tokens": {
            "access_token": token,
            "refresh_token": token,
            "token_type": "bearer",
            "user_id": data.email
        }
    }

@router.get("/users")
async def list_mock_users():
    return {
        "users": [{"email": email, "name": user["name"]} for email, user in MOCK_USERS.items()],
        "note": "These are mock users for testing only"
    }
