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
                        "body": f"Your TrueBond verification code is: {otp_code}. Valid for 10 minutes."
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
