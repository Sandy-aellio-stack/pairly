from pydantic import BaseModel, EmailStr
from typing import Optional


class SendOTPRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class VerifyOTPRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    otp: str

class SendEmailOTPRequest(BaseModel):
    email: EmailStr

class VerifyEmailOTPRequest(BaseModel):
    email: str
    otp: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ApprovalRequest(BaseModel):
    pending_session_id: str

class FirebaseLoginRequest(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    device_id: Optional[str] = None
