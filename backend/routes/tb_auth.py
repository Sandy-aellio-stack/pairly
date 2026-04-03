from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

from backend.models.tb_user import TBUser, UserOwnProfile
from backend.models.auth_models import (
    SendOTPRequest, VerifyOTPRequest, SendEmailOTPRequest, 
    VerifyEmailOTPRequest, RefreshTokenRequest, ForgotPasswordRequest, 
    ResetPasswordRequest, ApprovalRequest, FirebaseLoginRequest
)
from backend.services.tb_auth_service import (
    AuthService, SignupRequest, LoginRequest, TokenResponse,
    SignupWithOTPRequest, LoginWithOTPRequest
)
from backend.socket_server import sio
from backend.services.tb_otp_service import OTPService
from backend.services.password_reset_service import password_reset_service

import logging

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TBUser:
    token = credentials.credentials
    import logging
    logger = logging.getLogger("auth")
    logger.debug(f"Attempting to authenticate with token starting with: {token[:10]}...")
    try:
        user = await AuthService.get_current_user(token)
        logger.debug(f"Authentication successful for user: {user.id}")
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise e

@router.post("/signup", response_model=dict)
async def signup(data: SignupRequest):
    """Register a new user - requires age >= 18"""
    try:
        user, tokens = await AuthService.signup(data)
        token_data = tokens.model_dump()
        
        # Developer account with unlimited coins
        DEV_USER_ID = "69a18167be16ddc2a28e19aa"
        DEV_EMAIL = "indiranigopi677@gmail.com"
        is_dev = str(user.id) == DEV_USER_ID or user.email.lower() == DEV_EMAIL.lower()
        coins_to_show = 999999 if is_dev else user.coins

        return {
            "message": "Account created successfully",
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_type": token_data["token_type"],
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "coins": coins_to_show
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=dict)
async def login(data: LoginRequest):
    """Login with email and password"""
    result = await AuthService.login(data)
    
    if isinstance(result, dict) and result.get("status") == "WAITING_FOR_APPROVAL":
        return result
        
    user, tokens = result
    token_data = tokens.model_dump()
    
    # Developer account with unlimited coins
    DEV_USER_ID = "69a18167be16ddc2a28e19aa"
    DEV_EMAIL = "indiranigopi677@gmail.com"
    is_dev = str(user.id) == DEV_USER_ID or user.email.lower() == DEV_EMAIL.lower()
    coins_to_show = 999999 if is_dev else user.coins

    return {
        "message": "Login successful",
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "token_type": token_data["token_type"],
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "coins": coins_to_show,
            "is_verified": user.is_verified
        }
    }
    # Notify admin panels about user login (non-blocking, do not fail login on emit errors)
    try:
        await sio.emit('admin_update', {
            'event': 'user_login',
            'user_id': str(user.id),
            'name': user.name,
            'email': user.email
        })
    except Exception:
        pass

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """Refresh access token"""
    return await AuthService.refresh_token(data.refresh_token)

@router.post("/logout")
async def logout(
    user: TBUser = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout current user and blacklist token"""
    token = credentials.credentials
    return await AuthService.logout(user, access_token=token)

@router.post("/send-otp")
async def send_otp_unified(data: SendOTPRequest):
    """Unified endpoint for sending OTP (phone or email)"""
    if data.email:
        return await OTPService.send_email_otp(data.email.lower(), purpose="login")
    if data.phone:
        return await OTPService.send_otp(data.phone, purpose="login")
    raise HTTPException(status_code=400, detail="Phone or email is required")

@router.post("/verify-otp")
async def verify_otp_unified(data: VerifyOTPRequest):
    """Unified endpoint for verifying OTP and logging in/signing up"""
    identifier = data.email.lower() if data.email else data.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Phone or email is required")
        
    # Verify OTP
    await OTPService.verify_otp(identifier, data.otp, purpose="login")
    
    # Find user
    query = {"email": identifier} if data.email else {"mobile_number": identifier}
    user = await TBUser.find_one(query)
    
    # If user doesn't exist, this is a signup flow (minimal for dev, usually redirected to signup)
    if not user:
        # In a real app, you might return a "proceed to signup" flag
        # For this task, we ensure the flow completes
        raise HTTPException(status_code=404, detail="User not found. Please sign up.")
    
    # Generate tokens
    tokens = TokenResponse(
        access_token=AuthService.create_access_token(str(user.id)),
        refresh_token=AuthService.create_refresh_token(str(user.id)),
        user_id=str(user.id)
    )
    
    return {
        "success": True,
        "message": "OTP verified and logged in",
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "user_id": str(user.id),
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "coins": user.coins,
            "is_verified": user.is_verified
        }
    }

@router.post("/otp/send")
async def send_otp(data: SendOTPRequest):
    """Send OTP to mobile number"""
    return await OTPService.send_otp(data.phone)

@router.post("/otp/verify")
async def verify_otp(data: VerifyOTPRequest):
    """Verify OTP and return JWT tokens for login"""
    # Verify OTP
    await OTPService.verify_otp(data.phone, data.otp)
    
    # Find user by phone number
    user = await TBUser.find_one({"mobile_number": data.phone})
    
    # If user doesn't exist, create a new one (minimal for development)
    if not user:
        user = TBUser(
            name="Dev User",
            email=f"dev_{data.phone}@example.com",
            mobile_number=data.phone,
            is_verified=True,
            coins=10
        )
        await user.insert()
    
    # Generate tokens
    tokens = TokenResponse(
        access_token=AuthService.create_access_token(str(user.id)),
        refresh_token=AuthService.create_refresh_token(str(user.id)),
        user_id=str(user.id)
    )
    
    # Developer account with unlimited coins
    DEV_USER_ID = "69a18167be16ddc2a28e19aa"
    DEV_EMAIL = "indiranigopi677@gmail.com"
    is_dev = str(user.id) == DEV_USER_ID or user.email.lower() == DEV_EMAIL.lower()
    coins_to_show = 999999 if is_dev else user.coins

    return {
        "success": True,
        "message": "OTP verified and logged in",
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "user_id": str(user.id),
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "coins": coins_to_show,
            "is_verified": user.is_verified
        }
    }

@router.post("/email/send-otp")
async def send_email_otp(data: SendEmailOTPRequest):
    """
    Generate and send a 6-digit OTP to the user's email.
    """
    return await OTPService.send_email_otp(data.email)


@router.post("/email/verify-otp")
async def verify_email_otp(data: VerifyEmailOTPRequest):
    """
    Verify the 6-digit OTP sent to email.
    """
    # Verify OTP against DB
    is_valid = await OTPService.verify_email_otp(data.email, data.otp, purpose="login")
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Find user and return JWT tokens (login-on-verify behaviour)
    user = await TBUser.find_one({"email": data.email.lower()})
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please sign up.")

    tokens = TokenResponse(
        access_token=AuthService.create_access_token(str(user.id)),
        refresh_token=AuthService.create_refresh_token(str(user.id)),
        user_id=str(user.id)
    )

    # Developer account special handling (coins)
    DEV_USER_ID = "69a18167be16ddc2a28e19aa"
    DEV_EMAIL = "indiranigopi677@gmail.com"
    is_dev = str(user.id) == DEV_USER_ID or user.email.lower() == DEV_EMAIL.lower()
    coins_to_show = 999999 if is_dev else user.coins

    return {
        "success": True,
        "message": "OTP verified and logged in",
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "user_id": str(user.id),
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "coins": coins_to_show,
            "is_verified": user.is_verified
        }
    }


@router.post("/otp/verify-email")
async def legacy_verify_email_otp(data: VerifyEmailOTPRequest):
    """Legacy endpoint for backward compatibility."""
    return await verify_email_otp(data)


@router.post("/firebase-login")
async def firebase_login(data: FirebaseLoginRequest):
    """
    Handle login/registration for users verified via Firebase Phone Auth.
    """
    return await AuthService.firebase_login(data)

# ==================== OTP-BASED LOGIN & SIGNUP ====================

@router.post("/signup-with-otp")
async def signup_with_otp(data: SignupWithOTPRequest):
    """Signup with OTP verification."""
    try:
        user, tokens = await AuthService.signup_with_otp(data)
        
        # Developer account with unlimited coins
        DEV_USER_ID = "69a18167be16ddc2a28e19aa"
        DEV_EMAIL = "indiranigopi677@gmail.com"
        is_dev = str(user.id) == DEV_USER_ID or user.email.lower() == DEV_EMAIL.lower()
        coins_to_show = 999999 if is_dev else user.coins

        return {
            "message": "Account created successfully",
            "user_id": str(user.id),
            "is_verified": user.is_verified,
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "tokens": tokens.model_dump(),
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "coins": coins_to_show,
                "is_verified": user.is_verified
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"OTP Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login-with-otp")
async def login_with_otp(data: LoginWithOTPRequest):
    """Login with OTP verification."""
    result = await AuthService.login_with_otp(data)
    
    if isinstance(result, dict) and result.get("status") == "WAITING_FOR_APPROVAL":
        return result

    user, tokens = result
    
    # Developer account with unlimited coins
    DEV_USER_ID = "69a18167be16ddc2a28e19aa"
    DEV_EMAIL = "indiranigopi677@gmail.com"
    is_dev = str(user.id) == DEV_USER_ID or user.email.lower() == DEV_EMAIL.lower()
    coins_to_show = 999999 if is_dev else user.coins

    return {
        "message": "Login successful",
        "user_id": str(user.id),
        "is_verified": user.is_verified,
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "tokens": tokens.model_dump(),
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "coins": coins_to_show,
            "is_verified": user.is_verified
        }
    }

# ==================== LOGIN APPROVAL ====================

@router.post("/login/approve")
async def approve_login(data: ApprovalRequest, user: TBUser = Depends(get_current_user)):
    """Approve a login request from a new device"""
    return await AuthService.approve_login(data.pending_session_id, str(user.id))

@router.post("/login/deny")
async def deny_login(data: ApprovalRequest, user: TBUser = Depends(get_current_user)):
    """Deny a login request from a new device"""
    return await AuthService.deny_login(data.pending_session_id, str(user.id))

@router.get("/login/status/{pending_session_id}")
async def check_login_status(pending_session_id: str):
    """Poll the status of a pending login"""
    return await AuthService.check_login_status(pending_session_id)

@router.post("/otp/send-for-signup")
async def send_otp_for_signup(data: SendOTPRequest):
    """Send OTP for signup verification."""
    return await OTPService.send_otp(data.phone, purpose="signup")

@router.post("/otp/send-for-login")
async def send_otp_for_login(data: SendOTPRequest):
    """Send OTP for login verification."""
    if data.email:
        user = await TBUser.find_one({"email": data.email.lower()})
        if not user:
            raise HTTPException(status_code=404, detail="User not found with this email")
        return await OTPService.send_email_otp(data.email.lower(), purpose="login")
    
    if not data.phone:
        raise HTTPException(status_code=400, detail="Mobile number or email is required")
        
    user = await TBUser.find_one({"mobile_number": data.phone})
    if not user:
        raise HTTPException(status_code=404, detail="User not found with this mobile number")
        
    return await OTPService.send_otp(data.phone, purpose="login")

@router.get("/me", response_model=dict)
async def get_me(user: TBUser = Depends(get_current_user)):
    """Get current user's profile"""
    # Developer account with unlimited coins
    DEV_USER_ID = "69a18167be16ddc2a28e19aa"
    DEV_EMAIL = "indiranigopi677@gmail.com"
    is_dev = str(user.id) == DEV_USER_ID or user.email.lower() == DEV_EMAIL.lower()
    coins_to_show = 999999 if is_dev else user.coins
    
    return {
        "id": str(user.id),
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "bio": user.bio,
        "profile_picture": user.profile_pictures[0] if user.profile_pictures else None,
        "profile_pictures": user.profile_pictures or [],
        "location": {
            "latitude": user.location.coordinates[1] if user.location else None,
            "longitude": user.location.coordinates[0] if user.location else None
        } if user.location else None,
        "is_online": user.is_online,
        "status": "suspended" if user.is_suspended else "active",
        "last_active": user.last_seen.isoformat(),
        "coins": coins_to_show,
        "role": user.role
    }

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset link."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    success, message = await password_reset_service.create_reset_token(
        email=request.email,
        frontend_url=frontend_url
    )
    return {
        "message": "If an account exists with this email, you will receive a password reset link shortly.",
        "success": True
    }

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using token from email."""
    success, message = await password_reset_service.reset_password(
        token=request.token,
        new_password=request.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {
        "message": message,
        "success": True
    }

@router.get("/validate-reset-token")
async def validate_reset_token(token: str):
    """Validate if a reset token is still valid."""
    token_data = await password_reset_service.validate_reset_token(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    return {
        "valid": True,
        "message": "Token is valid"
    }
