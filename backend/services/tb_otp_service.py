import random
import os
import logging
from fastapi import HTTPException
from backend.models.tb_otp import TBOTP
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger("otp")


class OTPService:
    """OTP Service with database persistence and hashing.

    Phone OTP delivery is handled client-side via Firebase Auth.
    Email OTP delivery is handled server-side via SendGrid (or SMTP fallback).
    """

    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))

    @staticmethod
    def hash_otp(otp_code: str) -> str:
        """Hash OTP code using bcrypt"""
        return pwd_context.hash(otp_code)

    @staticmethod
    def verify_otp_hash(otp_code: str, hashed_otp: str) -> bool:
        """Verify OTP code against hash"""
        try:
            return pwd_context.verify(otp_code, hashed_otp)
        except Exception:
            return False

    @staticmethod
    async def check_rate_limit(identifier: str) -> bool:
        """Production rate limiting: 3 OTPs per 10 minutes per identifier."""
        from backend.services.rate_limiter_redis import rate_limiter
        if not rate_limiter.redis:
            await rate_limiter.init()
        key = f"otp_limit:{identifier}"
        is_allowed = await rate_limiter.allow(key, limit=3, window=600)
        if not is_allowed:
            logger.warning(f"[OTP LIMIT] Rate limit exceeded for {identifier}")
            return False
        return True

    @staticmethod
    async def send_otp(mobile_number: str, purpose: str = "login") -> dict:
        """Store OTP record in DB for phone-number flows.

        NOTE: Actual SMS delivery is handled client-side via Firebase Auth.
        This function exists for any legacy backend-only OTP routes.
        """
        if not mobile_number:
            raise HTTPException(status_code=400, detail="Phone number missing")

        if not await OTPService.check_rate_limit(mobile_number):
            raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait 10 minutes.")

        otp_code = OTPService.generate_otp()
        hashed_otp = OTPService.hash_otp(otp_code)

        otp_record = TBOTP.create_otp(
            mobile_number=mobile_number,
            otp_code=hashed_otp,
            purpose=purpose,
            validity_minutes=5
        )
        await otp_record.insert()

        logger.info(f"OTP record created for {mobile_number}, purpose={purpose}")

        return {
            "success": True,
            "message": "OTP sent successfully",
            "expires_in_minutes": 5
        }

    @staticmethod
    async def _send_email_via_sendgrid(to_email: str, otp_code: str) -> bool:
        """Send OTP email using SendGrid. Returns True on success."""
        api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("EMAIL_FROM", "noreply@luveloop.app")
        if not api_key:
            return False
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            sg = SendGridAPIClient(api_key)
            html_body = f"""
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;background:#fff;border-radius:16px;box-shadow:0 2px 12px rgba(0,0,0,.08)">
              <h2 style="color:#0f172a;margin-bottom:8px">Your Luveloop Login Code</h2>
              <p style="color:#64748b;margin-bottom:24px">Use the code below to sign in. It expires in 5 minutes.</p>
              <div style="background:#f8fafc;border-radius:12px;padding:24px;text-align:center;letter-spacing:8px;font-size:36px;font-weight:700;color:#0f172a;margin-bottom:24px">{otp_code}</div>
              <p style="color:#94a3b8;font-size:13px">If you didn't request this, you can safely ignore this email.</p>
            </div>
            """
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject="Your Luveloop OTP Code",
                html_content=html_body
            )
            response = sg.send(message)
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"OTP email sent via SendGrid to {to_email} (status={response.status_code})")
                return True
            else:
                logger.error(f"SendGrid returned non-success status for {to_email}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"SendGrid email failed to {to_email}: {e}")
            return False

    @staticmethod
    async def send_email_otp(email: str, purpose: str = "email_verification") -> dict:
        """Generate, store, and deliver OTP to email via SendGrid (SMTP fallback)."""
        if not email:
            raise HTTPException(status_code=400, detail="Email address missing")

        if not await OTPService.check_rate_limit(email):
            raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait 10 minutes.")

        otp_code = OTPService.generate_otp()
        hashed_otp = OTPService.hash_otp(otp_code)

        otp_record = TBOTP.create_otp(
            mobile_number="EMAIL",
            email=email.lower(),
            otp_code=hashed_otp,
            purpose=purpose,
            validity_minutes=5
        )
        await otp_record.insert()

        logger.info(f"Email OTP created for {email}, purpose={purpose}")

        # Try SendGrid first, then fall back to SMTP email_service
        sent = await OTPService._send_email_via_sendgrid(email, otp_code)
        if not sent:
            try:
                from backend.services.email_service import email_service
                await email_service.send_otp_email(to_email=email, otp_code=otp_code)
                logger.info(f"OTP email sent via SMTP fallback to {email}")
            except Exception as e:
                logger.error(f"Email OTP delivery failed for {email}: {e}")

        return {
            "success": True,
            "message": "OTP sent to email",
            "email": email,
            "expires_in_minutes": 5
        }

    @staticmethod
    async def verify_otp(identifier: str, otp_code: str, purpose: str = "login") -> bool:
        """Verify OTP for the given identifier (phone or email).
        Raises HTTPException(400) on failure.
        """
        is_email = "@" in identifier

        query = {"purpose": purpose, "is_used": False}
        if is_email:
            query["email"] = identifier.lower()
        else:
            query["mobile_number"] = identifier

        otp_record = await TBOTP.find(query).sort(-TBOTP.created_at).first_or_none()

        if not otp_record:
            raise HTTPException(status_code=400, detail="OTP not found or already used. Please request a new OTP.")

        if otp_record.is_expired():
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")

        if otp_record.attempts >= otp_record.max_attempts:
            raise HTTPException(status_code=400, detail="Too many failed attempts. Please request a new OTP.")

        if not OTPService.verify_otp_hash(otp_code, otp_record.otp_code):
            otp_record.increment_attempts()
            await otp_record.save()
            remaining = otp_record.remaining_attempts()
            detail = f"Invalid OTP. {remaining} attempts remaining." if remaining > 0 else "Too many failed attempts. Please request a new OTP."
            raise HTTPException(status_code=400, detail=detail)

        otp_record.mark_used()
        await otp_record.save()

        logger.info(f"OTP verified for {identifier}, purpose={purpose}")
        return True

    @staticmethod
    async def verify_email_otp(email: str, otp_code: str, purpose: str = "email_verification") -> bool:
        """Verify email OTP using database."""
        return await OTPService.verify_otp(email, otp_code, purpose)
