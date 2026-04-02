from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional


class SendOTPRequest(BaseModel):
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None

    @model_validator(mode='after')
    def normalize_phone(self):
        if not self.phone and self.mobile_number:
            self.phone = self.mobile_number
        return self


class VerifyOTPRequest(BaseModel):
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None
    otp: Optional[str] = None
    otp_code: Optional[str] = None

    @model_validator(mode='after')
    def normalize_fields(self):
        if not self.phone and self.mobile_number:
            self.phone = self.mobile_number
        if not self.otp and self.otp_code:
            self.otp = self.otp_code
        return self

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
