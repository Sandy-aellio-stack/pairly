import httpx
import random
import os
import json
import time
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from backend.models.tb_otp import TBOTP
# In-memory OTP storage for development
# Format: {phone: {"otp": code, "expires_at": timestamp}}
otp_store = {}

class OTPService:
    """OTP Service with in-memory storage for development"""

    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))

    @staticmethod
    async def check_rate_limit(identifier: str) -> bool:
        """Bypassed for development"""
        return True

    @staticmethod
    async def send_otp(mobile_number: str, purpose: str = "login") -> dict:
        """
        Generate and log OTP to terminal, bypassing Fonoster and Redis.
        """
        if not mobile_number:
            raise HTTPException(status_code=400, detail="Phone number missing")

        # Generate new OTP
        otp_code = OTPService.generate_otp()
        expires_at = time.time() + (5 * 60) # 5 minutes

        # Store in memory
        otp_store[mobile_number] = {
            "otp": otp_code,
            "expires_at": expires_at,
            "purpose": purpose
        }

        # Detailed terminal logging as requested
        print("\n================================")
        print("DEV OTP GENERATED")
        print(f"Phone: {mobile_number}")
        print(f"OTP: {otp_code}")
        print("================================\n")

        response = {
            "success": True,
            "message": "OTP generated",
            "expires_in_minutes": 5
        }

        # Return dev_otp in response when in development mode
        if os.getenv("ENVIRONMENT", "development") != "production":
            response["dev_otp"] = otp_code

        return response

    @staticmethod
    async def send_email_otp(email: str, purpose: str = "email_verification") -> dict:
        """
        Generate and send OTP via email, storing in memory for dev mock mode.
        """
        if not email:
            raise HTTPException(status_code=400, detail="Email address missing")

        # Generate new OTP
        otp_code = OTPService.generate_otp()
        expires_at = time.time() + (5 * 60) # 5 minutes

        # Store in memory for dev mock mode
        otp_store[email] = {
            "otp": otp_code,
            "expires_at": expires_at,
            "purpose": purpose
        }

        # Detailed terminal logging
        print("\n================================")
        print("DEV EMAIL OTP GENERATED")
        print(f"Email: {email}")
        print(f"OTP: {otp_code}")
        print("================================\n")

        # Try to send actual email if configured
        try:
            from backend.services.email_service import email_service
            await email_service.send_otp_email(to_email=email, otp_code=otp_code)
        except Exception as e:
            print(f"Email sending failed (but OTP logged to terminal): {e}")

        email_response = {
            "success": True,
            "message": "OTP sent to email",
            "email": email,
            "expires_in_minutes": 5
        }

        if os.getenv("ENVIRONMENT", "development") != "production":
            email_response["dev_otp"] = otp_code

        return email_response

    @staticmethod
    async def verify_otp(identifier: str, otp_code: str, purpose: str = "login") -> bool:
        """
        Verify OTP for the given identifier (phone or email) using in-memory store.
        Raises HTTPException(400) on failure.
        """
        entry = otp_store.get(identifier)
        if not entry:
            raise HTTPException(status_code=400, detail="OTP not found or expired. Please request a new OTP.")

        if time.time() > entry["expires_at"]:
            del otp_store[identifier]
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")

        if entry["otp"] != otp_code:
            raise HTTPException(status_code=400, detail="Invalid OTP. Please try again.")

        # Consume the OTP
        del otp_store[identifier]
        return True

    @staticmethod
    async def verify_email_otp(email: str, otp_code: str, purpose: str = "email_verification") -> bool:
        """
        Verify email OTP using in-memory store.
        """
        return await OTPService.verify_otp(email, otp_code, purpose)
