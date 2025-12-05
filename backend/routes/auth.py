from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime
from backend.models.user import User, Role, TwoFAMethod
from backend.models.session import Session
from backend.services.token_utils import create_access_token, create_refresh_token, verify_token
from backend.services.audit import log_event
from backend.services.fingerprint import register_fingerprint
from backend.services.twofa import (
    verify_totp,
    send_email_otp,
    verify_email_otp,
    check_otp_attempts,
    increment_otp_attempts,
    clear_otp_attempts
)
from backend.middleware.failed_login import check_login_lock, register_failed_attempt, clear_failed_attempts
from backend.utils.jwt_revocation import is_token_revoked, revoke_token
from backend.utils.refresh_store import set_user_refresh_jti, validate_user_refresh_jti
import uuid

router = APIRouter(prefix="/api/auth")
pwd_context = CryptContext(schemes=["bcrypt"])
security = HTTPBearer()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_info: str = ""


class Login2FARequest(BaseModel):
    email: EmailStr
    temp_token: str
    code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    session_id: str = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    session_id: str
    token_type: str = "bearer"
    user: dict


class TwoFARequired(BaseModel):
    requires_2fa: bool = True
    method: str
    temp_token: str
    message: str


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(creds.credentials, "access")
    
    # Check if token is revoked
    jti = payload.get("jti")
    if jti and await is_token_revoked(jti):
        raise HTTPException(401, "Token revoked")
    
    user = await User.get(payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    return user


@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest, request: Request):
    existing = await User.find_one(User.email == req.email)
    if existing:
        raise HTTPException(400, "Email already exists")

    user = User(
        email=req.email,
        password_hash=pwd_context.hash(req.password),
        name=req.name,
        role=req.role,
        credits_balance=0
    )
    await user.insert()

    client_ip = request.client.host if request.client else "unknown"
    rtid = str(uuid.uuid4())
    
    session = Session(
        session_id=str(uuid.uuid4()),
        user_id=user.id,
        device_info="signup_device",
        ip=client_ip,
        refresh_token_id=rtid,
        created_at=datetime.utcnow(),
        last_active_at=datetime.utcnow()
    )
    await session.insert()

    try:
        fingerprint = await register_fingerprint(
            request=request,
            user_id=user.id,
            session_id=session.session_id,
            ip=client_ip
        )
        session.fingerprint_hash = fingerprint.fingerprint_hash
        await session.save()
    except Exception as e:
        print(f"Fingerprint capture error: {e}")

    await log_event(
        actor_user_id=user.id,
        actor_ip=client_ip,
        action="signup",
        details={"session_id": session.session_id, "rtid": rtid, "device_info": "signup_device"},
        severity="info"
    )

    access_token = create_access_token(str(user.id), user.role, rtid, 30)
    refresh_token = create_refresh_token(str(user.id), user.role, rtid, 7)
    
    # Store refresh token JTI for validation
    refresh_payload = verify_token(refresh_token, "refresh")
    await set_user_refresh_jti(str(user.id), refresh_payload["jti"], ttl_days=7)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        session_id=session.session_id,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "credits_balance": user.credits_balance
        }
    )


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    
    await check_login_lock(client_ip, req.email)
    
    user = await User.find_one(User.email == req.email)
    
    if not user or not pwd_context.verify(req.password, user.password_hash):
        await register_failed_attempt(client_ip, user.id if user else None)
        await log_event(
            actor_user_id=user.id if user else None,
            actor_ip=client_ip,
            action="login_failed",
            details={"email": req.email},
            severity="warning"
        )
        raise HTTPException(401, "Invalid credentials")

    if user.is_suspended:
        raise HTTPException(403, "Account suspended")

    await clear_failed_attempts(user.id)

    if user.twofa_enabled and user.twofa_method:
        temp_token = create_access_token(str(user.id), user.role, "temp", 10)
        
        if user.twofa_method == TwoFAMethod.EMAIL:
            await send_email_otp(user.id, user.email)
            message = f"OTP sent to {user.email}"
        else:
            message = "Enter code from your authenticator app"
        
        await log_event(
            actor_user_id=user.id,
            actor_ip=client_ip,
            action="login_2fa_required",
            details={"user_id": str(user.id), "method": user.twofa_method},
            severity="info"
        )
        
        return TwoFARequired(
            requires_2fa=True,
            method=user.twofa_method,
            temp_token=temp_token,
            message=message
        )

    rtid = str(uuid.uuid4())
    
    session = Session(
        session_id=str(uuid.uuid4()),
        user_id=user.id,
        device_info=req.device_info or "unknown",
        ip=client_ip,
        refresh_token_id=rtid,
        created_at=datetime.utcnow(),
        last_active_at=datetime.utcnow()
    )
    await session.insert()

    try:
        fingerprint = await register_fingerprint(
            request=request,
            user_id=user.id,
            session_id=session.session_id,
            ip=client_ip
        )
        session.fingerprint_hash = fingerprint.fingerprint_hash
        await session.save()
    except Exception as e:
        print(f"Fingerprint capture error: {e}")

    await log_event(
        actor_user_id=user.id,
        actor_ip=client_ip,
        action="login_success",
        details={"session_id": session.session_id, "rtid": rtid, "device_info": req.device_info},
        severity="info"
    )

    access_token = create_access_token(str(user.id), user.role, rtid, 30)
    refresh_token = create_refresh_token(str(user.id), user.role, rtid, 7)
    
    # Store refresh token JTI for validation
    refresh_payload = verify_token(refresh_token, "refresh")
    await set_user_refresh_jti(str(user.id), refresh_payload["jti"], ttl_days=7)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        session_id=session.session_id,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "credits_balance": user.credits_balance
        }
    )


@router.post("/login/2fa", response_model=TokenResponse)
async def login_2fa_verify(req: Login2FARequest, request: Request):
    try:
        payload = verify_token(req.temp_token, "access")
        if payload.get("rtid") != "temp":
            raise HTTPException(401, "Invalid temp token")
    except:
        raise HTTPException(401, "Invalid or expired temp token")
    
    user = await User.get(payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    
    if user.email != req.email:
        raise HTTPException(401, "Email mismatch")
    
    allowed, retry_after = await check_otp_attempts(str(user.id))
    if not allowed:
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="2fa_login_locked",
            details={"user_id": str(user.id), "retry_after": retry_after},
            severity="error"
        )
        raise HTTPException(429, f"Too many failed attempts. Retry after {retry_after} seconds")
    
    verified = False
    
    if user.twofa_method == TwoFAMethod.TOTP:
        if not user.twofa_secret:
            raise HTTPException(400, "TOTP not configured")
        verified = verify_totp(user.twofa_secret, req.code)
    
    elif user.twofa_method == TwoFAMethod.EMAIL:
        verified = await verify_email_otp(user.id, req.code)
    
    if not verified:
        attempts = await increment_otp_attempts(str(user.id))
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="2fa_login_failed",
            details={"user_id": str(user.id), "attempts": attempts},
            severity="warning"
        )
        raise HTTPException(401, "Invalid 2FA code")
    
    await clear_otp_attempts(str(user.id))
    
    client_ip = request.client.host if request.client else "unknown"
    rtid = str(uuid.uuid4())
    
    session = Session(
        session_id=str(uuid.uuid4()),
        user_id=user.id,
        device_info="unknown",
        ip=client_ip,
        refresh_token_id=rtid,
        created_at=datetime.utcnow(),
        last_active_at=datetime.utcnow()
    )
    await session.insert()

    try:
        fingerprint = await register_fingerprint(
            request=request,
            user_id=user.id,
            session_id=session.session_id,
            ip=client_ip
        )
        session.fingerprint_hash = fingerprint.fingerprint_hash
        await session.save()
    except Exception as e:
        print(f"Fingerprint capture error: {e}")

    await log_event(
        actor_user_id=user.id,
        actor_ip=client_ip,
        action="login_success_2fa",
        details={"session_id": session.session_id, "rtid": rtid},
        severity="info"
    )

    access_token = create_access_token(str(user.id), user.role, rtid, 30)
    refresh_token = create_refresh_token(str(user.id), user.role, rtid, 7)
    
    # Store refresh token JTI for validation
    refresh_payload = verify_token(refresh_token, "refresh")
    await set_user_refresh_jti(str(user.id), refresh_payload["jti"], ttl_days=7)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        session_id=session.session_id,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "credits_balance": user.credits_balance
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    payload = verify_token(req.refresh_token, "refresh")
    
    rtid = payload.get("rtid")
    if not rtid:
        raise HTTPException(401, "Invalid token format")
    
    session = await Session.find_one(Session.refresh_token_id == rtid)
    if not session:
        await log_event(
            actor_user_id=None,
            actor_ip=None,
            action="refresh_failed",
            details={"rtid": rtid, "reason": "session_not_found"},
            severity="warning"
        )
        raise HTTPException(401, "Session not found")
    
    if session.revoked:
        await log_event(
            actor_user_id=session.user_id,
            actor_ip=None,
            action="refresh_failed",
            details={"rtid": rtid, "reason": "session_revoked", "session_id": session.session_id},
            severity="error"
        )
        raise HTTPException(401, "Session revoked")
    
    user = await User.get(payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    
    old_rtid = rtid
    new_rtid = str(uuid.uuid4())
    session.refresh_token_id = new_rtid
    session.last_active_at = datetime.utcnow()
    await session.save()

    await log_event(
        actor_user_id=user.id,
        actor_ip=None,
        action="refresh_rotated",
        details={"old_rtid": old_rtid, "new_rtid": new_rtid, "session_id": session.session_id},
        severity="info"
    )

    access_token = create_access_token(str(user.id), user.role, new_rtid, 30)
    refresh_token = create_refresh_token(str(user.id), user.role, new_rtid, 7)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        session_id=session.session_id,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "credits_balance": user.credits_balance
        }
    )


@router.post("/logout")
async def logout(req: LogoutRequest, user: User = Depends(get_current_user)):
    if req.session_id:
        session = await Session.find_one(Session.session_id == req.session_id, Session.user_id == user.id)
    else:
        session = await Session.find_one(Session.user_id == user.id, Session.revoked == False)
    
    if session:
        session.revoked = True
        await session.save()
        
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="session_revoked",
            details={"session_id": session.session_id},
            severity="info"
        )
    
    return {"status": "logged_out"}


@router.get("/sessions")
async def get_sessions(user: User = Depends(get_current_user)):
    sessions = await Session.find(
        Session.user_id == user.id,
        Session.revoked == False
    ).sort("-last_active_at").to_list()
    
    return [
        {
            "session_id": s.session_id,
            "device_info": s.device_info,
            "ip": s.ip,
            "created_at": s.created_at.isoformat(),
            "last_active_at": s.last_active_at.isoformat()
        }
        for s in sessions
    ]


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "credits_balance": user.credits_balance,
        "is_suspended": user.is_suspended,
        "twofa_enabled": user.twofa_enabled,
        "twofa_method": user.twofa_method
    }