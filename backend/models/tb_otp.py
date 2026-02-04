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
    def create_otp(cls, mobile_number: str, otp_code: str, purpose: str = "verification", validity_minutes: int = 5, email: str = None):
        """
        Create OTP record with configurable expiry (default 5 minutes for login/security)
        """
        return cls(
            mobile_number=mobile_number,
            email=email,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=validity_minutes)
        )

    def is_valid(self) -> bool:
        """
        Check if OTP is valid (not used, within attempts limit, not expired)
        """
        now = datetime.now(timezone.utc)
        return (
            not self.is_used and
            self.attempts < self.max_attempts and
            now < self.expires_at
        )

    def is_expired(self) -> bool:
        """Check if OTP has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def mark_used(self):
        """Mark OTP as used (one-time use only)"""
        self.is_used = True

    def increment_attempts(self):
        """Increment attempt count"""
        self.attempts += 1

    def remaining_attempts(self) -> int:
        """Get remaining attempts"""
        return max(0, self.max_attempts - self.attempts)

    class Settings:
        name = "tb_otps"
        indexes = [
            [("mobile_number", 1), ("purpose", 1), ("is_used", 1)],
            [("email", 1), ("purpose", 1), ("is_used", 1)],
            [("expires_at", 1)]
        ]
