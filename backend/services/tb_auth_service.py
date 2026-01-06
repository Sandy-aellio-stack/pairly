import bcrypt
import jwt
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from backend.models.tb_user import TBUser, Address, Preferences, Gender, Intent, GeoLocation
from backend.models.tb_otp import TBOTP
from backend.models.tb_credit import TBCreditTransaction, TransactionReason
from backend.services.tb_otp_service import OTPService
import os

JWT_SECRET = os.getenv("JWT_SECRET", "truebond-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 30


# Request schemas
class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    mobile_number: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8)
    age: int = Field(ge=18, le=100)
    gender: Gender
    interested_in: Gender
    intent: Intent = Intent.DATING
    min_age: int = Field(ge=18, default=18)
    max_age: int = Field(le=100, default=50)
    max_distance_km: int = Field(ge=1, le=500, default=50)
    # Address (private)
    address_line: str
    city: str
    state: str
    country: str
    pincode: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

    @staticmethod
    def create_access_token(user_id: str) -> str:
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    async def signup(data: SignupRequest) -> Tuple[TBUser, TokenResponse]:
        # Check age
        if data.age < 18:
            raise HTTPException(status_code=400, detail="Must be 18 or older to register")

        try:
            # Check existing email
            existing_email = await TBUser.find_one({"email": data.email})
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already registered")

            # Check existing mobile
            existing_mobile = await TBUser.find_one({"mobile_number": data.mobile_number})
            if existing_mobile:
                raise HTTPException(status_code=400, detail="Mobile number already registered")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail="Database not available. Please try again later.")

        # Create user
        user = TBUser(
            name=data.name,
            email=data.email,
            mobile_number=data.mobile_number,
            password_hash=AuthService.hash_password(data.password),
            age=data.age,
            gender=data.gender,
            intent=data.intent,
            preferences=Preferences(
                interested_in=data.interested_in,
                min_age=data.min_age,
                max_age=data.max_age,
                max_distance_km=data.max_distance_km
            ),
            address=Address(
                address_line=data.address_line,
                city=data.city,
                state=data.state,
                country=data.country,
                pincode=data.pincode
            ),
            credits_balance=10,  # Signup bonus
            is_verified=False
        )
        await user.insert()

        # Log signup bonus credit
        transaction = TBCreditTransaction(
            user_id=str(user.id),
            amount=10,
            reason=TransactionReason.SIGNUP_BONUS,
            balance_after=10,
            description="Welcome bonus credits"
        )
        await transaction.insert()

        # Generate tokens
        tokens = TokenResponse(
            access_token=AuthService.create_access_token(str(user.id)),
            refresh_token=AuthService.create_refresh_token(str(user.id)),
            user_id=str(user.id)
        )

        return user, tokens

    @staticmethod
    async def login(data: LoginRequest) -> Tuple[TBUser, TokenResponse]:
        try:
            user = await TBUser.find_one({"email": data.email})
        except Exception as e:
            raise HTTPException(status_code=503, detail="Database not available. Please try again later.")
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not AuthService.verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        user.is_online = True
        await user.save()

        tokens = TokenResponse(
            access_token=AuthService.create_access_token(str(user.id)),
            refresh_token=AuthService.create_refresh_token(str(user.id)),
            user_id=str(user.id)
        )

        return user, tokens

    @staticmethod
    async def refresh_token(refresh_token: str) -> TokenResponse:
        payload = AuthService.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("sub")
        user = await TBUser.get(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        return TokenResponse(
            access_token=AuthService.create_access_token(user_id),
            refresh_token=AuthService.create_refresh_token(user_id),
            user_id=user_id
        )

    @staticmethod
    async def get_current_user(token: str) -> TBUser:
        payload = AuthService.decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid access token")

        user_id = payload.get("sub")
        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        return user

    @staticmethod
    async def logout(user: TBUser):
        user.is_online = False
        await user.save()
        return {"message": "Logged out successfully"}
