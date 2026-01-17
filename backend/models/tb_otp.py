from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone, timedelta


class TBOTP(Document):
    """OTP verification record"""
    mobile_number: Indexed(str)
    email: Optional[str] = None  # For email-based OTP
    otp_code: str
    purpose: str = "verification"  # verification, login, password_reset, email_verification
    is_used: bool = False
    attempts: int = 0
    max_attempts: int = 3
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create_otp(cls, mobile_number: str, otp_code: str, purpose: str = "verification", validity_minutes: int = 10, email: str = None):
        return cls(
            mobile_number=mobile_number,
            email=email,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=validity_minutes)
        )

    def is_valid(self) -> bool:
        return (
            not self.is_used and
            self.attempts < self.max_attempts and
            datetime.now(timezone.utc) < self.expires_at
        )

    class Settings:
        name = "tb_otps"
