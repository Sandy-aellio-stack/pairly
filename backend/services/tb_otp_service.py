import httpx
import random
import os
import json
import time
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from backend.models.tb_otp import TBOTP
from backend.core.redis_client_enhanced import RedisClientEnhanced

FONOSTER_API_KEY = os.getenv("FONOSTER_API_KEY", "APe3o0sdbt0emloi4fa1a4i0ko3affq8br")
FONOSTER_BASE_URL = "https://api.fonoster.io/v1beta2"

# Rate limiting configuration
OTP_SEND_RATE_LIMIT = 5  # Max OTP sends per hour
OTP_SEND_WINDOW = 3600  # 1 hour window

# Global Redis client for rate limiting
redis_client = RedisClientEnhanced()


class OTPService:
    """OTP Service with rate limiting and 5-minute expiry"""

    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))

    @staticmethod
    async def _check_rate_limit_redis(identifier: str) -> tuple:
        """
        Check rate limit using Redis.
        Returns (is_allowed, retry_after_seconds)
        """
        key = f"otp_rate:{identifier}"
        
        try:
            # Get current count
            current = await redis_client.get(key)
            if current is None:
                # First request - set with 1 hour expiry
                await redis_client.set(key, "1", ex=OTP_SEND_WINDOW)
                return True, 0
            
            count = int(current)
            if count >= OTP_SEND_RATE_LIMIT:
                # Get TTL to return retry_after
                ttl_key = f"otp_rate_ttl:{identifier}"
                ttl = await redis_client.get(ttl_key)
                retry_after = int(ttl) if ttl else OTP_SEND_WINDOW
                return False, retry_after
            
            # Increment count
            await redis_client.set(key, str(count + 1), ex=OTP_SEND_WINDOW)
            return True, 0
            
        except Exception as e:
            # If Redis fails, allow the request (fail open)
            print(f"Rate limit check failed: {e}")
            return True, 0

    @staticmethod
    async def check_rate_limit(identifier: str) -> bool:
        """
        Check if OTP can be sent (rate limiting)
        Returns True if allowed, raises HTTPException if rate limited
        """
        is_allowed, retry_after = await OTPService._check_rate_limit_redis(identifier)
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Too many OTP requests. Please try again in {retry_after} seconds."
            )
        return True

    @staticmethod
    async def send_otp(mobile_number: str, purpose: str = "login") -> dict:
        """
        Send OTP to mobile number with rate limiting and 5-minute expiry.
        
        Args:
            mobile_number: Target mobile number
            purpose: OTP purpose (login, verification, password_reset)
        
        Returns:
            dict with message and expiry info
        """
        # Check rate limit
        await OTPService.check_rate_limit(mobile_number)
        
        # Invalidate existing OTPs for this number and purpose
        await TBOTP.find({
            "mobile_number": mobile_number,
            "purpose": purpose,
            "is_used": False
        }).update_many({"$set": {"is_used": True}})

        # Generate new OTP
        otp_code = OTPService.generate_otp()
        
        # Create OTP record with 5-minute expiry
        otp_record = TBOTP.create_otp(
            mobile_number=mobile_number,
            otp_code=otp_code,
            purpose=purpose,
            validity_minutes=5,  # 5-minute expiry
            email=None
        )
        await otp_record.insert()

        # Send via Fonoster (or mock for development)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{FONOSTER_BASE_URL}/messages",
                    headers={
                        "Authorization": f"Bearer {FONOSTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "to": mobile_number,
                        "body": f"Your verification code is: {otp_code}. Valid for 5 minutes. Don't share this code."
                    },
                    timeout=30
                )
                
                if response.status_code not in [200, 201]:
                    print(f"Fonoster API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"Failed to send OTP via Fonoster: {e}")
            # Continue anyway for development

        return {
            "message": "OTP sent successfully",
            "mobile_number": mobile_number,
            "purpose": purpose,
            "expires_in_minutes": 5,
            "attempts_remaining": 3,
            # Include OTP in response for development/testing only
            "_dev_otp": otp_code if os.getenv("ENV", "development") == "development" else None
        }

    @staticmethod
    async def send_email_otp(email: str, purpose: str = "email_verification") -> dict:
        """
        Send OTP via email with rate limiting and 5-minute expiry.
        
        Args:
            email: Target email address
            purpose: OTP purpose (email_verification, login, password_reset)
        
        Returns:
            dict with message and expiry info
        """
        # Check rate limit
        is_allowed, retry_after = await OTPService._check_rate_limit_redis(f"email:{email}")
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Too many OTP requests. Please try again in {retry_after} seconds."
            )
        
        # Invalidate existing OTPs for this email and purpose
        try:
            await TBOTP.find({
                "email": email,
                "purpose": purpose,
                "is_used": False
            }).update_many({"$set": {"is_used": True}})
        except Exception:
            # If email field doesn't exist, try mobile_number field (backwards compat)
            await TBOTP.find({
                "mobile_number": email,
                "purpose": purpose,
                "is_used": False
            }).update_many({"$set": {"is_used": True}})

        # Generate new OTP
        otp_code = OTPService.generate_otp()
        
        # Create OTP record with 5-minute expiry
        otp_record = TBOTP(
            mobile_number=email,  # Using mobile_number field for email (backwards compat)
            email=email,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            is_used=False,
            attempts=0,
            max_attempts=3
        )
        await otp_record.insert()

        # Send via email
        try:
            from backend.services.email_service import email_service
            await email_service.send_otp_email(
                to_email=email,
                otp_code=otp_code
            )
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
            # Continue anyway - log OTP for development

        return {
            "message": "OTP sent to your email",
            "email": email,
            "purpose": purpose,
            "expires_in_minutes": 5,
            "attempts_remaining": 3,
            # Include OTP in response for development/testing only
            "_dev_otp": otp_code if os.getenv("ENV", "development") == "development" else None
        }

    @staticmethod
    async def verify_otp(mobile_number: str, otp_code: str, purpose: str = "login") -> bool:
        """
        Verify OTP for login/purpose.
        
        Args:
            mobile_number: User's mobile number
            otp_code: OTP code to verify
            purpose: OTP purpose (login, verification, password_reset)
        
        Returns:
            True if OTP is valid
        
        Raises:
            HTTPException if OTP is invalid/expired/max attempts reached
        """
        # Find valid OTP record
        otp_record = await TBOTP.find_one({
            "mobile_number": mobile_number,
            "purpose": purpose,
            "is_used": False
        })

        if not otp_record:
            raise HTTPException(status_code=400, detail="No valid OTP found. Please request a new OTP.")

        # Check if expired
        if otp_record.is_expired():
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")

        # Increment attempts
        otp_record.increment_attempts()
        await otp_record.save()

        # Check max attempts
        if otp_record.attempts >= otp_record.max_attempts:
            raise HTTPException(status_code=400, detail="Max attempts reached. Please request a new OTP.")

        # Verify OTP code
        if otp_record.otp_code != otp_code:
            remaining = otp_record.remaining_attempts()
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid OTP. {remaining} attempts remaining."
            )

        # Mark as used (one-time use only)
        otp_record.mark_used()
        await otp_record.save()

        return True

    @staticmethod
    async def verify_email_otp(email: str, otp_code: str, purpose: str = "email_verification") -> bool:
        """
        Verify email OTP.
        
        Args:
            email: User's email
            otp_code: OTP code to verify
            purpose: OTP purpose (email_verification, login, password_reset)
        
        Returns:
            True if OTP is valid
        
        Raises:
            HTTPException if OTP is invalid/expired/max attempts reached
        """
        # Try to find by email field first, then by mobile_number (backwards compat)
        otp_record = await TBOTP.find_one({
            "$or": [
                {"email": email, "purpose": purpose, "is_used": False},
                {"mobile_number": email, "purpose": purpose, "is_used": False}
            ]
        })

        if not otp_record:
            raise HTTPException(status_code=400, detail="No valid OTP found. Please request a new OTP.")

        # Check if expired
        if otp_record.is_expired():
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")

        # Increment attempts
        otp_record.increment_attempts()
        await otp_record.save()

        # Check max attempts
        if otp_record.attempts >= otp_record.max_attempts:
            raise HTTPException(status_code=400, detail="Max attempts reached. Please request a new OTP.")

        # Verify OTP code
        if otp_record.otp_code != otp_code:
            remaining = otp_record.remaining_attempts()
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid OTP. {remaining} attempts remaining."
            )

        # Mark as used (one-time use only)
        otp_record.mark_used()
        await otp_record.save()

        return True
