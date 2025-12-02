from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from backend.models.user import User, Role
import jwt, os

router = APIRouter(prefix="/api/auth")
pwd = CryptContext(schemes=["bcrypt"])
security = HTTPBearer()

SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")
ALG = "HS256"

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    role: Role

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

def create_token(sub: str, role: Role, token_type: str, minutes: int):
    exp = datetime.utcnow() + timedelta(minutes=minutes)
    payload = {"sub": sub, "role": role, "token_type": token_type, "exp": exp}
    return jwt.encode(payload, SECRET, algorithm=ALG)

@router.post("/signup", response_model=AuthResponse)
async def signup(req: SignupRequest):
    if await User.find_one(User.email == req.email):
        raise HTTPException(400, "Email already exists")
    user = User(email=req.email, password_hash=pwd.hash(req.password), role=req.role)
    await user.insert()

    access = create_token(str(user.id), user.role, "access", 15)
    refresh = create_token(str(user.id), user.role, "refresh", 10080)

    return {"access_token": access, "refresh_token": refresh,
            "user": {"id": str(user.id), "email": user.email, "role": user.role}}

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    user = await User.find_one(User.email == req.email)
    if not user or not pwd.verify(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    access = create_token(str(user.id), user.role, "access", 15)
    refresh = create_token(str(user.id), user.role, "refresh", 10080)

    return {"access_token": access, "refresh_token": refresh,
            "user": {"id": str(user.id), "email": user.email,
                     "role": user.role, "credits_balance": user.credits_balance}}

@router.post("/refresh", response_model=AuthResponse)
async def refresh(req: RefreshRequest):
    try:
        payload = jwt.decode(req.refresh_token, SECRET, algorithms=[ALG])
        if payload.get("token_type") != "refresh":
            raise HTTPException(401, "Invalid token type")

        user = await User.get(payload["sub"])
        if not user:
            raise HTTPException(401, "User not found")

        access = create_token(str(user.id), user.role, "access", 15)
        refresh = create_token(str(user.id), user.role, "refresh", 10080)

        return {"access_token": access, "refresh_token": refresh,
                "user": {"id": str(user.id), "email": user.email, "role": user.role}}

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
