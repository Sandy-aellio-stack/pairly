import pyotp
import qrcode
import io
import base64
import secrets
import redis.asyncio as aioredis
from backend.config import settings
from backend.models.otp import OTP
from backend.models.user import User
from beanie import PydanticObjectId
from datetime import datetime, timedelta
from typing import Optional

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return redis_client


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def generate_totp_qr(email: str, secret: str) -> str:
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=email, issuer_name="Dating SaaS")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


async def send_email_otp(user_id: PydanticObjectId, email: str) -> str:
    code = str(secrets.randbelow(900000) + 100000)
    
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp = OTP(
        user_id=user_id,
        code=code,
        method="email",
        expires_at=expires_at
    )
    await otp.insert()
    
    print(f"EMAIL OTP for {email}: {code}")
    
    return code


async def verify_email_otp(user_id: PydanticObjectId, code: str) -> bool:
    otp = await OTP.find_one(
        OTP.user_id == user_id,
        OTP.code == code,
        OTP.method == "email",
        OTP.verified == False
    )
    
    if not otp:
        return False
    
    if datetime.utcnow() > otp.expires_at:
        return False
    
    otp.verified = True
    await otp.save()
    
    return True


async def check_otp_attempts(user_id: str) -> tuple[bool, int]:
    redis = await get_redis()
    key = f"otp_attempts:{user_id}"
    
    attempts = await redis.get(key)
    if not attempts:
        return (True, 0)
    
    attempts_count = int(attempts)
    if attempts_count >= 5:
        ttl = await redis.ttl(key)
        return (False, ttl)
    
    return (True, attempts_count)


async def increment_otp_attempts(user_id: str):
    redis = await get_redis()
    key = f"otp_attempts:{user_id}"
    
    attempts = await redis.incr(key)
    if attempts == 1:
        await redis.expire(key, 3600)
    
    return attempts


async def clear_otp_attempts(user_id: str):
    redis = await get_redis()
    key = f"otp_attempts:{user_id}"
    await redis.delete(key)