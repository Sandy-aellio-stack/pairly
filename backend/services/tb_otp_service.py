import random
import os
import logging
import bcrypt
from fastapi import HTTPException
from backend.models.tb_otp import TBOTP

logger = logging.getLogger("otp")


class OTPService:
    """OTP Service with database persistence and hashing.

    Email OTP delivery is handled server-side via SendGrid.
    """

    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))

    @staticmethod
    def hash_otp(otp_code: str) -> str:
        """Hash OTP code using bcrypt directly (avoids passlib/bcrypt 4.x incompatibility)"""
        otp_bytes = otp_code.encode("utf-8")
        return bcrypt.hashpw(otp_bytes, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_otp_hash(otp_code: str, hashed_otp: str) -> bool:
        """Verify OTP code against hash"""
        try:
            otp_bytes = otp_code.encode("utf-8")
            hashed_bytes = hashed_otp.encode("utf-8")
            return bcrypt.checkpw(otp_bytes, hashed_bytes)
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
            logger.error("[SendGrid] SENDGRID_API_KEY is not set — cannot send OTP email.")
            return False

        logger.info(f"[SendGrid] Sending OTP email to: {to_email} from: {from_email}")

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
            status = getattr(response, "status_code", None)
            body = getattr(response, "body", None)
            logger.info(f"[SendGrid] Response status={status} body={body}")

            if status and 200 <= status < 300:
                logger.info(f"[SendGrid] OTP email delivered to {to_email} (status={status})")
                return True
            else:
                logger.error(f"[SendGrid] Non-success status {status} for {to_email}. Body: {body}")
                return False

        except Exception as e:
            err_str = str(e)
            logger.error(f"[SendGrid] Exception sending to {to_email}: {err_str}")

            if "403" in err_str:
                logger.error(
                    "[SendGrid] *** 403 Forbidden — sender not verified. ***\n"
                    f"  EMAIL_FROM is set to: '{from_email}'\n"
                    "  Fix: Go to SendGrid → Settings → Sender Authentication and verify this address.\n"
                    "  Then set EMAIL_FROM in Replit Secrets to that verified address."
                )
            elif "401" in err_str:
                logger.error("[SendGrid] *** 401 Unauthorized — check that SENDGRID_API_KEY is correct and has 'Mail Send' permission. ***")

            return False

    @staticmethod
    async def send_email_otp(email: str, purpose: str = "email_verification") -> dict:
        """Generate, store, and deliver OTP to email via SendGrid."""
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

        logger.info(f"[OTP] Email OTP created for {email}, purpose={purpose}")

        sent = await OTPService._send_email_via_sendgrid(email, otp_code)

        if not sent:
            logger.error(f"[OTP] Email delivery failed for {email} — OTP was NOT sent.")
            raise HTTPException(
                status_code=503,
                detail="Failed to send OTP email. Please check server logs for SendGrid configuration issues."
            )

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
