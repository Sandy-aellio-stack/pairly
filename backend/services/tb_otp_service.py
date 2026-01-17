import httpx
import random
import os
from datetime import datetime, timezone
from fastapi import HTTPException
from backend.models.tb_otp import TBOTP

FONOSTER_API_KEY = os.getenv("FONOSTER_API_KEY", "APe3o0sdbt0emloi4fa1a4i0ko3affq8br")
FONOSTER_BASE_URL = "https://api.fonoster.io/v1beta2"


class OTPService:
    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))

    @staticmethod
    async def send_otp(mobile_number: str, purpose: str = "verification") -> dict:
        """Send OTP via Fonoster API"""
        # Invalidate existing OTPs for this number
        await TBOTP.find(TBOTP.mobile_number == mobile_number, TBOTP.is_used == False).update_many(
            {"$set": {"is_used": True}}
        )

        # Generate new OTP
        otp_code = OTPService.generate_otp()
        
        # Create OTP record
        otp_record = TBOTP.create_otp(
            mobile_number=mobile_number,
            otp_code=otp_code,
            purpose=purpose,
            validity_minutes=10
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
                        "body": f"Your Luveloop verification code is: {otp_code}. Valid for 10 minutes."
                    },
                    timeout=30
                )
                
                if response.status_code not in [200, 201]:
                    # Log error but don't fail - return OTP for testing
                    print(f"Fonoster API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"Failed to send OTP via Fonoster: {e}")
            # Continue anyway for development

        return {
            "message": "OTP sent successfully",
            "mobile_number": mobile_number,
            "expires_in_minutes": 10,
            # Include OTP in response for development/testing only
            "_dev_otp": otp_code if os.getenv("ENV", "development") == "development" else None
        }

    @staticmethod
    async def send_email_otp(email: str, purpose: str = "email_verification") -> dict:
        """Send OTP via email for verification"""
        from backend.services.email_service import email_service
        
        # Invalidate existing OTPs for this email
        try:
            await TBOTP.find({"email": email, "is_used": False}).update_many(
                {"$set": {"is_used": True}}
            )
        except:
            pass

        # Generate new OTP
        otp_code = OTPService.generate_otp()
        
        # Create OTP record with email field
        otp_record = TBOTP(
            mobile_number=email,  # Using mobile_number field for email (backwards compat)
            email=email,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc).replace(
                minute=datetime.now(timezone.utc).minute + 10
            ),
            is_used=False,
            attempts=0,
            max_attempts=3
        )
        await otp_record.insert()

        # Send via email
        try:
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
            "expires_in_minutes": 10,
            # Include OTP in response for development/testing only
            "_dev_otp": otp_code if os.getenv("ENV", "development") == "development" else None
        }

    @staticmethod
    async def verify_otp(mobile_number: str, otp_code: str, purpose: str = "verification") -> bool:
        """Verify OTP"""
        otp_record = await TBOTP.find_one(
            TBOTP.mobile_number == mobile_number,
            TBOTP.purpose == purpose,
            TBOTP.is_used == False
        )

        if not otp_record:
            raise HTTPException(status_code=400, detail="No valid OTP found. Please request a new one.")

        # Increment attempts
        otp_record.attempts += 1
        await otp_record.save()

        if not otp_record.is_valid():
            raise HTTPException(status_code=400, detail="OTP expired or max attempts reached")

        if otp_record.otp_code != otp_code:
            remaining = otp_record.max_attempts - otp_record.attempts
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid OTP. {remaining} attempts remaining."
            )

        # Mark as used
        otp_record.is_used = True
        await otp_record.save()

        return True

    @staticmethod
    async def verify_email_otp(email: str, otp_code: str, purpose: str = "email_verification") -> bool:
        """Verify email OTP"""
        # Try to find by email field first, then by mobile_number (backwards compat)
        otp_record = await TBOTP.find_one({
            "$or": [
                {"email": email, "is_used": False},
                {"mobile_number": email, "is_used": False}
            ]
        })

        if not otp_record:
            raise HTTPException(status_code=400, detail="No valid OTP found. Please request a new one.")

        # Increment attempts
        otp_record.attempts += 1
        await otp_record.save()

        # Check if expired
        if hasattr(otp_record, 'expires_at') and otp_record.expires_at:
            if datetime.now(timezone.utc) > otp_record.expires_at:
                raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

        # Check max attempts
        if otp_record.attempts > otp_record.max_attempts:
            raise HTTPException(status_code=400, detail="Max attempts reached. Please request a new OTP.")

        if otp_record.otp_code != otp_code:
            remaining = otp_record.max_attempts - otp_record.attempts
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid OTP. {remaining} attempts remaining."
            )

        # Mark as used
        otp_record.is_used = True
        await otp_record.save()

        return True
