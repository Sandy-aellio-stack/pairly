from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic import BaseModel, EmailStr

from backend.models.tb_user import TBUser, UserOwnProfile
from backend.services.tb_auth_service import (
    AuthService, SignupRequest, LoginRequest, TokenResponse
)
from backend.services.tb_otp_service import OTPService

router = APIRouter(prefix="/api/auth", tags=["TrueBond Auth"])
security = HTTPBearer()


# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TBUser:
    token = credentials.credentials
    return await AuthService.get_current_user(token)


class SendOTPRequest(BaseModel):
    mobile_number: str


class VerifyOTPRequest(BaseModel):
    mobile_number: str
    otp_code: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/signup", response_model=dict)
async def signup(data: SignupRequest):
    """Register a new user - requires age >= 18"""
    user, tokens = await AuthService.signup(data)
    return {
        "message": "Account created successfully",
        "user_id": str(user.id),
        "credits_balance": user.credits_balance,
        "tokens": tokens.model_dump()
    }


@router.post("/login", response_model=dict)
async def login(data: LoginRequest):
    """Login with email and password"""
    user, tokens = await AuthService.login(data)
    return {
        "message": "Login successful",
        "user_id": str(user.id),
        "tokens": tokens.model_dump()
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """Refresh access token"""
    return await AuthService.refresh_token(data.refresh_token)


@router.post("/logout")
async def logout(user: TBUser = Depends(get_current_user)):
    """Logout current user"""
    return await AuthService.logout(user)


@router.post("/otp/send")
async def send_otp(data: SendOTPRequest):
    """Send OTP to mobile number"""
    return await OTPService.send_otp(data.mobile_number)


@router.post("/otp/verify")
async def verify_otp(data: VerifyOTPRequest, user: TBUser = Depends(get_current_user)):
    """Verify OTP and mark user as verified"""
    if user.mobile_number != data.mobile_number:
        raise HTTPException(status_code=400, detail="Mobile number mismatch")
    
    await OTPService.verify_otp(data.mobile_number, data.otp_code)
    
    user.is_verified = True
    await user.save()
    
    return {"message": "Mobile number verified successfully"}


@router.get("/me", response_model=dict)
async def get_me(user: TBUser = Depends(get_current_user)):
    """Get current user's profile (excludes address)"""
    return {
        "id": str(user.id),
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "bio": user.bio,
        "profile_pictures": user.profile_pictures,
        "preferences": user.preferences.model_dump(),
        "intent": user.intent,
        "email": user.email,
        "mobile_number": user.mobile_number,
        "credits_balance": user.credits_balance,
        "is_verified": user.is_verified,
        "is_online": user.is_online,
        "created_at": user.created_at.isoformat()
    }
