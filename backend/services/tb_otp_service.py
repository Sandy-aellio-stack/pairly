import httpx
import random
import os
import json
import time
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from backend.models.tb_otp import TBOTP
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class OTPService:
    """OTP Service with database persistence and hashing"""

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
        """
        Production rate limiting: 3 OTPs per 10 minutes per identifier.
        """
        from backend.services.rate_limiter_redis import rate_limiter
        
        # Initial check/init if needed (usually handled in app lifecycle)
        if not rate_limiter.redis:
            await rate_limiter.init()
            
        key = f"otp_limit:{identifier}"
        # Limit to 3 requests per 600 seconds (10 minutes)
        is_allowed = await rate_limiter.allow(key, limit=3, window=600)
        
        if not is_allowed:
            # Check if we should block the user or suggest waiting
            logger.warning(f"[OTP LIMIT] Rate limit exceeded for {identifier}")
            return False
        return True

    @staticmethod
    async def send_otp(mobile_number: str, purpose: str = "login") -> dict:
        """
        Generate and save OTP to database, and log to terminal.
        """
        if not mobile_number:
            raise HTTPException(status_code=400, detail="Phone number missing")

        # Check rate limit first
        if not await OTPService.check_rate_limit(mobile_number):
            raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait 10 minutes.")

        # Generate new OTP
        otp_code = OTPService.generate_otp()
        hashed_otp = OTPService.hash_otp(otp_code)
        
        # Save to database
        otp_record = TBOTP.create_otp(
            mobile_number=mobile_number,
            otp_code=hashed_otp,
            purpose=purpose,
            validity_minutes=5
        )
        await otp_record.insert()

        # Detailed terminal logging (Development only)
        import logging
        logger = logging.getLogger("otp")
        
        is_prod = os.getenv("ENVIRONMENT", "development") == "production"
        
        if not is_prod:
            print("\n================================")
            print(f"OTP GENERATED FOR {purpose.upper()}")
            print(f"Phone: {mobile_number}")
            print(f"OTP: {otp_code}")
            print("================================\n")
        
        logger.info(f"OTP generated for {mobile_number}, purpose={purpose}")

        response = {
            "success": True,
            "message": "OTP sent successfully",
            "expires_in_minutes": 5
        }

        return response

    @staticmethod
    async def send_email_otp(email: str, purpose: str = "email_verification") -> dict:
        """
        Generate and save OTP to database for email.
        """
        if not email:
            raise HTTPException(status_code=400, detail="Email address missing")

        # Check rate limit first
        if not await OTPService.check_rate_limit(email):
            raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait 10 minutes.")

        # Generate new OTP
        otp_code = OTPService.generate_otp()
        hashed_otp = OTPService.hash_otp(otp_code)
        
        # Save to database
        otp_record = TBOTP.create_otp(
            mobile_number="EMAIL",  # Placeholder for email-only OTPs
            email=email.lower(),
            otp_code=hashed_otp,
            purpose=purpose,
            validity_minutes=5
        )
        await otp_record.insert()

        # Detailed terminal logging (Development only)
        import logging
        logger = logging.getLogger("otp")
        
        is_prod = os.getenv("ENVIRONMENT", "development") == "production"
        
        if not is_prod:
            print("\n================================")
            print(f"EMAIL OTP GENERATED FOR {purpose.upper()}")
            print(f"Email: {email}")
            print(f"OTP: {otp_code}")
            print("================================\n")
        
        logger.info(f"Email OTP generated for {email}, purpose={purpose}")

        # Try to send actual email if configured
        try:
            from backend.services.email_service import email_service
            await email_service.send_otp_email(to_email=email, otp_code=otp_code)
        except Exception as e:
            if not is_prod:
                print(f"Email sending failed (but OTP logged to terminal): {e}")

        email_response = {
            "success": True,
            "message": "OTP sent to email",
            "email": email,
            "expires_in_minutes": 5
        }

        return email_response

    @staticmethod
    async def verify_otp(identifier: str, otp_code: str, purpose: str = "login") -> bool:
        """
        Verify OTP for the given identifier (phone or email) using database.
        Raises HTTPException(400) on failure.
        """
        is_email = "@" in identifier
        
        # Find latest valid OTP for this identifier and purpose
        query = {
            "purpose": purpose,
            "is_used": False
        }
        if is_email:
            query["email"] = identifier.lower()
        else:
            query["mobile_number"] = identifier

        otp_record = await TBOTP.find(query).sort(-TBOTP.created_at).first_or_none()
        
        if not otp_record:
            raise HTTPException(status_code=400, detail="OTP not found or already used. Please request a new OTP.")

        # Check expiration
        if otp_record.is_expired():
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")

        # Check brute force
        if otp_record.attempts >= otp_record.max_attempts:
            raise HTTPException(status_code=400, detail="Too many failed attempts. Please request a new OTP.")

        # Verify hash
        if not OTPService.verify_otp_hash(otp_code, otp_record.otp_code):
            otp_record.increment_attempts()
            await otp_record.save()
            
            remaining = otp_record.remaining_attempts()
            detail = f"Invalid OTP. {remaining} attempts remaining." if remaining > 0 else "Too many failed attempts. Please request a new OTP."
            raise HTTPException(status_code=400, detail=detail)

        # Mark as used
        otp_record.mark_used()
        await otp_record.save()
        
        import logging
        logger = logging.getLogger("otp")
        logger.info(f"OTP verified for {identifier}, purpose={purpose}")
        
        return True

    @staticmethod
    async def verify_email_otp(email: str, otp_code: str, purpose: str = "email_verification") -> bool:
        """
        Verify email OTP using database.
        """
        return await OTPService.verify_otp(email, otp_code, purpose)
