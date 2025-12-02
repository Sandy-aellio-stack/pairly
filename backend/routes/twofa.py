from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.models.user import User, TwoFAMethod
from backend.routes.auth import get_current_user
from backend.services.twofa import (
    generate_totp_secret,
    generate_totp_qr,
    verify_totp,
    send_email_otp,
    verify_email_otp,
    check_otp_attempts,
    increment_otp_attempts,
    clear_otp_attempts
)
from backend.services.audit import log_event

router = APIRouter(prefix="/api/auth/2fa")


class SetupRequest(BaseModel):
    method: TwoFAMethod


class VerifyRequest(BaseModel):
    code: str


class DisableRequest(BaseModel):
    password: str


@router.post("/setup")
async def setup_2fa(req: SetupRequest, user: User = Depends(get_current_user)):
    if user.twofa_enabled:
        raise HTTPException(400, "2FA already enabled")
    
    if req.method == TwoFAMethod.TOTP:
        secret = generate_totp_secret()
        qr_code = generate_totp_qr(user.email, secret)
        
        user.twofa_secret = secret
        user.twofa_method = TwoFAMethod.TOTP
        await user.save()
        
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="2fa_setup_initiated",
            details={"method": "totp", "user_id": str(user.id)},
            severity="info"
        )
        
        return {
            "method": "totp",
            "secret": secret,
            "qr_code": qr_code,
            "message": "Scan QR code with Google Authenticator and verify with code"
        }
    
    elif req.method == TwoFAMethod.EMAIL:
        code = await send_email_otp(user.id, user.email)
        
        user.twofa_method = TwoFAMethod.EMAIL
        await user.save()
        
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="2fa_setup_initiated",
            details={"method": "email", "user_id": str(user.id)},
            severity="info"
        )
        
        return {
            "method": "email",
            "message": f"OTP sent to {user.email}. Verify to enable 2FA."
        }
    
    raise HTTPException(400, "Invalid method")


@router.post("/verify")
async def verify_2fa(req: VerifyRequest, user: User = Depends(get_current_user)):
    if user.twofa_enabled:
        raise HTTPException(400, "2FA already enabled and verified")
    
    if not user.twofa_method:
        raise HTTPException(400, "2FA not set up. Call /setup first")
    
    allowed, retry_after = await check_otp_attempts(str(user.id))
    if not allowed:
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="2fa_verify_locked",
            details={"user_id": str(user.id), "retry_after": retry_after},
            severity="warning"
        )
        raise HTTPException(429, f"Too many failed attempts. Retry after {retry_after} seconds")
    
    verified = False
    
    if user.twofa_method == TwoFAMethod.TOTP:
        if not user.twofa_secret:
            raise HTTPException(400, "TOTP secret not found")
        verified = verify_totp(user.twofa_secret, req.code)
    
    elif user.twofa_method == TwoFAMethod.EMAIL:
        verified = await verify_email_otp(user.id, req.code)
    
    if not verified:
        attempts = await increment_otp_attempts(str(user.id))
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="2fa_verify_failed",
            details={"user_id": str(user.id), "attempts": attempts, "method": user.twofa_method},
            severity="warning"
        )
        raise HTTPException(401, "Invalid verification code")
    
    user.twofa_enabled = True
    await user.save()
    
    await clear_otp_attempts(str(user.id))
    
    await log_event(
        actor_user_id=user.id,
        actor_ip=None,
        action="2fa_enabled",
        details={"user_id": str(user.id), "method": user.twofa_method},
        severity="info"
    )
    
    return {"status": "2fa_enabled", "method": user.twofa_method}


@router.post("/disable")
async def disable_2fa(req: DisableRequest, user: User = Depends(get_current_user)):
    if not user.twofa_enabled:
        raise HTTPException(400, "2FA not enabled")
    
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"])
    
    if not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(401, "Invalid password")
    
    user.twofa_enabled = False
    user.twofa_method = None
    user.twofa_secret = None
    await user.save()
    
    await log_event(
        actor_user_id=user.id,
        actor_ip=None,
        action="2fa_disabled",
        details={"user_id": str(user.id)},
        severity="info"
    )
    
    return {"status": "2fa_disabled"}


@router.get("/status")
async def get_2fa_status(user: User = Depends(get_current_user)):
    return {
        "enabled": user.twofa_enabled,
        "method": user.twofa_method if user.twofa_enabled else None
    }