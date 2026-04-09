from jose import jwt
from jose.exceptions import JWTError as JoseJWTError, ExpiredSignatureError as JoseExpiredSignatureError
import random
import string
import os
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from backend.models.tb_user import TBUser, Address, Preferences, Gender, Intent, GeoLocation
from backend.models.user import User as LegacyUser
from backend.models.tb_otp import TBOTP
from backend.models.tb_pending_session import PendingSession
from backend.models.tb_credit import TBCreditTransaction, TransactionReason
from backend.models.auth_models import FirebaseLoginRequest
from backend.services.tb_otp_service import OTPService
from backend.config import settings
import bcrypt as _bcrypt_lib
from bson.errors import InvalidId
from bson import ObjectId

logger = logging.getLogger(__name__)


def _bcrypt_truncate(password: str) -> bytes:
    """Return password encoded to UTF-8 and hard-capped at 72 bytes."""
    return password.encode("utf-8")[:72]

JWT_SECRET = settings.JWT_SECRET
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable not set")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = 168 # 7 days
REFRESH_TOKEN_EXPIRE_DAYS = 30


# Request schemas
class SignupRequest(BaseModel):
    # REQUIRED fields
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    mobile_number: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8)
    age: int = Field(ge=18, le=100)
    gender: Gender
    interested_in: Gender
    
    # OPTIONAL fields with defaults
    intent: Intent = Intent.DATING
    min_age: int = Field(ge=18, default=18)
    max_age: int = Field(le=100, default=50)
    max_distance_km: int = Field(ge=1, le=500, default=50)
    
    # Address fields - OPTIONAL with safe defaults
    address_line: str = Field(default="NA")
    city: str = Field(default="NA")
    state: str = Field(default="NA")
    country: str = Field(default="India")
    pincode: str = Field(default="000000")
    device_id: str = Field(..., min_length=1)
    referral_code: Optional[str] = Field(default=None, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_id: str = Field(..., min_length=1)


class LoginWithOTPRequest(BaseModel):
    """Request schema for login with OTP"""
    mobile_number: Optional[str] = Field(None, min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    otp_code: str = Field(..., min_length=6, max_length=6)
    device_id: str = Field(..., min_length=1)


class SignupWithOTPRequest(BaseModel):
    """Request schema for signup with OTP verification"""
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
    otp_code: str = Field(..., min_length=6, max_length=6)
    device_id: str = Field(..., min_length=1)
    referral_code: Optional[str] = Field(default=None, max_length=20)


class VerifyMobileRequest(BaseModel):
    """Request schema for verifying mobile number with OTP"""
    mobile_number: str = Field(..., min_length=10, max_length=15)
    otp_code: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str


class AuthService:
    @staticmethod
    def generate_referral_code(name: str) -> str:
        """Generate a unique short referral code based on name + random suffix."""
        prefix = ''.join(filter(str.isalpha, name.upper()))[:4].ljust(4, 'X')
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}{suffix}"

    @staticmethod
    def _truncate_password(password: str) -> bytes:
        """Return password encoded to UTF-8 hard-capped at 72 bytes (bcrypt limit)."""
        return password.encode("utf-8")[:72]

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt directly (passlib bypassed to avoid version bugs)."""
        hashed = _bcrypt_lib.hashpw(AuthService._truncate_password(password), _bcrypt_lib.gensalt())
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password using bcrypt directly. Handles $2a$/$2b$ prefix normalisation."""
        if not hashed:
            return False
        try:
            clean = hashed.strip()
            # Normalise $2a$ → $2b$ so bcrypt library accepts it
            if clean.startswith("$2a$"):
                clean = "$2b$" + clean[4:]
            return _bcrypt_lib.checkpw(AuthService._truncate_password(password), clean.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def create_access_token(user_id: str, role: str = "user") -> str:
        from uuid import uuid4
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "jti": str(uuid4()),
            "iss": "pairly",
            "aud": "pairly-api",
            "exp": now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
            "iat": now
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: str, role: str = "user") -> str:
        from uuid import uuid4
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "role": role,
            "type": "refresh",
            "jti": str(uuid4()),
            "iss": "pairly",
            "aud": "pairly-api",
            "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": now
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        import logging
        logger = logging.getLogger("auth")
        try:
            # Use same secret as other services to ensure consistency
            payload = jwt.decode(
                token, 
                JWT_SECRET, 
                algorithms=[JWT_ALGORITHM],
                audience="pairly-api",
                issuer="pairly"
            )
            logger.debug(f"Token decoded successfully for sub: {payload.get('sub')}")
            return payload
        except JoseExpiredSignatureError:
            logger.warning(f"Token expired for token starting with: {token[:10]}...")
            raise HTTPException(status_code=401, detail="Token expired")
        except JoseJWTError as e:
            logger.error(f"JWT decode error: {str(e)} for token starting with: {token[:10]}...")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error decoding token: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token: Unknown error")

    @staticmethod
    async def signup(data: SignupRequest) -> Tuple[TBUser, TokenResponse]:
        # Normalize email
        email_normalized = data.email.lower().strip()
        
        # Check age
        if data.age < 18:
            raise HTTPException(status_code=400, detail="Must be 18 or older to register")

        try:
            # Check existing email
            existing_email = await TBUser.find_one({"email": email_normalized})
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

        # Resolve referrer if referral_code provided
        referrer_id = None
        if data.referral_code:
            referrer = await TBUser.find_one({"referral_code": data.referral_code.upper()})
            if referrer:
                referrer_id = str(referrer.id)

        # Generate unique referral code for this new user
        new_referral_code = AuthService.generate_referral_code(data.name)

        # Create user
        user = TBUser(
            name=data.name,
            email=email_normalized,
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
            coins=10,  # Signup bonus
            is_verified=False,
            current_device_id=data.device_id,
            referral_code=new_referral_code,
            referred_by=referrer_id
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

        # Award referral bonus to referrer (50 coins)
        if referrer_id:
            try:
                from backend.services.tb_credit_service import CreditService
                await CreditService.add_credits(
                    user_id=referrer_id,
                    amount=50,
                    reason=TransactionReason.REFERRAL_REWARD,
                    reference_id=str(user.id),
                    description=f"Referral reward for inviting {user.name}"
                )
                await TBUser.find_one({"_id": ObjectId(referrer_id)}).update(
                    {"$inc": {"referral_rewards_count": 1}}
                )
                
                # Emit balance update to referrer if online
                from backend.socket_server import emit_notification_to_user
                referrer_new_balance = await CreditService.get_balance(referrer_id)
                await emit_notification_to_user(referrer_id, "balance_updated", {"coins": referrer_new_balance})

                logger.info(
                    "Referral reward granted", 
                    extra={
                        "referrer_id": referrer_id,
                        "new_user_id": str(user.id),
                        "coins_added": 50
                    }
                )
            except Exception as ref_err:
                logger.warning(f"Failed to process referral reward: {ref_err}")

        # Generate tokens
        tokens = TokenResponse(
            access_token=AuthService.create_access_token(str(user.id), user.role),
            refresh_token=AuthService.create_refresh_token(str(user.id), user.role),
            user_id=str(user.id)
        )

        return user, tokens

    @staticmethod
    async def login(data: LoginRequest) -> Tuple[TBUser, TokenResponse]:
        # Normalize email to lowercase for case-insensitive login
        email_normalized = data.email.lower().strip()
        
        try:
            # Case-insensitive search for email
            email_regex = re.compile(f"^{re.escape(email_normalized)}$", re.IGNORECASE)
            user = await TBUser.find_one({"email": email_regex})
        except Exception as e:
            raise HTTPException(status_code=503, detail="Database not available. Please try again later.")
        
        # If user not found in tb_users, check legacy users collection
        if not user:
            try:
                # Case-insensitive search for legacy email too
                email_regex = re.compile(f"^{re.escape(email_normalized)}$", re.IGNORECASE)
                legacy_user = await LegacyUser.find_one({"email": email_regex})
                if legacy_user:
                    # Legacy user found - verify password and migrate to new collection
                    if AuthService.verify_password(data.password, legacy_user.password_hash):
                        # Create new TBUser from legacy data
                        from backend.models.tb_user import Preferences, Gender, Intent
                        new_user = TBUser(
                            name=legacy_user.name,
                            email=legacy_user.email.lower(),
                            mobile_number="",
                            password_hash=AuthService.hash_password(data.password),  # Rehash with new method
                            age=25,
                            gender=Gender.OTHER,
                            intent=Intent.DATING,
                            preferences=Preferences(),
                            address=Address(),
                            coins=legacy_user.credits_balance or 10,
                            is_active=not legacy_user.is_suspended
                        )
                        import logging
                        logging.info(f"Migrating legacy user {legacy_user.email} to TBUser")
                        await new_user.insert()
                        user = new_user
            except Exception as e:
                import logging
                logging.error(f"Error during legacy user migration: {e}")
                pass  # Continue with original error
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not AuthService.verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        # Session tracking logic - DISABLED as per user request
        # if user.current_device_id and user.current_device_id != data.device_id:
        #     # Check if there's already a pending session for this user and new device
        #     pending = await PendingSession.find_one({
        #         "user_id": str(user.id),
        #         "new_device_id": data.device_id,
        #         "status": "pending"
        #     })
        #     if not pending:
        #         pending = PendingSession(
        #             user_id=str(user.id),
        #             new_device_id=data.device_id,
        #             old_device_id=user.current_device_id,
        #             status="pending"
        #         )
        #         await pending.insert()
        #     
        #     # Notify the old device via Socket.IO
        #     from backend.socket_server import emit_notification_to_user
        #     await emit_notification_to_user(
        #         str(user.id), 
        #         "login_approval_request", 
        #         {
        #             "pending_session_id": str(pending.id),
        #             "new_device_id": data.device_id,
        #             "message": "A new device is trying to log in to your account. Do you approve?"
        #         }
        #     )
        #     
        #     return {
        #         "status": "WAITING_FOR_APPROVAL",
        #         "pending_session_id": str(pending.id),
        #         "message": "Login pending approval from your other device."
        #     }

        # Update last login and session
        try:
            user.last_login_at = datetime.now(timezone.utc)
            user.last_seen = datetime.now(timezone.utc)
            user.is_online = True
            user.current_device_id = data.device_id
            await user.save()
        except Exception as e:
            logging.error(f"Error updating user status on login: {e}")
            # Continue anyway, don't block login for status update
            pass

        tokens = TokenResponse(
            access_token=AuthService.create_access_token(str(user.id), user.role),
            refresh_token=AuthService.create_refresh_token(str(user.id), user.role),
            user_id=str(user.id)
        )

        return user, tokens

    @staticmethod
    async def firebase_login(data: FirebaseLoginRequest):
        """
        Handle login/registration for users verified via Firebase Phone Auth.
        """
        phone = data.phone
        
        # 1. Check if user exists in MongoDB
        user = await TBUser.find_one({"mobile_number": phone})
        
        # 2. If not, create a new user
        if not user:
            from backend.models.tb_user import Preferences, Gender, Intent, Address
            user = TBUser(
                name=data.name or "User",
                email=data.email or f"user_{phone.replace('+', '')}@pairly.io",
                mobile_number=phone,
                password_hash="FIREBASE_AUTH",
                age=25,
                gender=Gender.OTHER,
                intent=Intent.DATING,
                preferences=Preferences(interested_in=Gender.OTHER),
                address=Address(address_line="NA", city="NA", state="NA", country="India", pincode="000000"),
                is_verified=True,
                coins=10,
                current_device_id=data.device_id
            )
            await user.insert()
            
            # Log signup bonus
            from backend.models.tb_credit import TBCreditTransaction, TransactionReason
            transaction = TBCreditTransaction(
                user_id=str(user.id),
                amount=10,
                reason=TransactionReason.SIGNUP_BONUS,
                balance_after=10,
                description="Welcome bonus via Phone Join"
            )
            await transaction.insert()

        # 3. Session tracking logic (One device at a time)
        if user.current_device_id and user.current_device_id != data.device_id:
            from backend.models.tb_pending_session import PendingSession
            pending = await PendingSession.find_one({
                "user_id": str(user.id),
                "new_device_id": data.device_id,
                "status": "pending"
            })
            if not pending:
                pending = PendingSession(
                    user_id=str(user.id),
                    new_device_id=data.device_id,
                    old_device_id=user.current_device_id,
                    status="pending"
                )
                await pending.insert()
            
            # Notify the old device
            from backend.socket_server import emit_notification_to_user
            await emit_notification_to_user(
                str(user.id), 
                "login_approval_request", 
                {
                    "pending_session_id": str(pending.id),
                    "new_device_id": data.device_id,
                    "message": "A new device is trying to log in to your account. Do you approve?"
                }
            )
            
            return {
                "status": "WAITING_FOR_APPROVAL",
                "pending_session_id": str(pending.id),
                "message": "Login pending approval from your other device."
            }

        # 4. Generate JWT tokens
        access_token = AuthService.create_access_token(str(user.id), user.role)
        refresh_token = AuthService.create_refresh_token(str(user.id), user.role)
        
        # 5. Update last login
        user.last_login_at = datetime.now(timezone.utc)
        if data.device_id:
            user.current_device_id = data.device_id
        await user.save()

        return {
            "success": True,
            "token": access_token,
            "access_token": access_token, # Keep for compat
            "refresh_token": refresh_token,
            "user_id": str(user.id),
            "user": {
                "id": str(user.id),
                "name": user.name,
                "phone": user.mobile_number
            }
        }

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
            access_token=AuthService.create_access_token(user_id, user.role),
            refresh_token=AuthService.create_refresh_token(user_id, user.role),
            user_id=user_id
        )

    @staticmethod
    async def get_current_user(token: str) -> TBUser:
        from backend.utils.token_blacklist import token_blacklist

        payload = AuthService.decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid access token")

        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti:
            is_blacklisted = await token_blacklist.is_blacklisted(jti)
            if is_blacklisted:
                raise HTTPException(status_code=401, detail="Token has been revoked")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")

        # Check if all user tokens are blacklisted
        is_user_blacklisted = await token_blacklist.is_user_blacklisted(user_id)
        if is_user_blacklisted:
            raise HTTPException(status_code=401, detail="Token has been revoked")

        from backend.utils.objectid_utils import validate_object_id
        user_oid = validate_object_id(user_id)
        user = await TBUser.get(user_oid)

        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        return user

    @staticmethod
    async def logout(user: TBUser, access_token: str = None):
        """
        Logout user and blacklist the current access token

        Args:
            user: Current user
            access_token: Optional access token to blacklist
        """
        from backend.utils.token_blacklist import token_blacklist
        import logging

        logger = logging.getLogger("auth_service")
        user.is_online = False
        user.last_seen = datetime.now(timezone.utc)
        await user.save()

        # Blacklist the access token if provided
        if access_token:
            try:
                payload = AuthService.decode_token(access_token)
                jti = payload.get("jti")
                if jti:
                    # Calculate remaining TTL
                    exp = payload.get("exp")
                    now = datetime.now(timezone.utc).timestamp()
                    ttl = int(exp - now)
                    if ttl > 0:
                        await token_blacklist.blacklist_token(jti, ttl)
            except Exception as e:
                # Log error but don't fail logout
                logger.error(f"Failed to blacklist token on logout: {e}")

        return {"message": "Logged out successfully"}

    # ==================== OTP-BASED AUTHENTICATION ====================

    @staticmethod
    async def signup_with_otp(data: SignupWithOTPRequest) -> Tuple[TBUser, TokenResponse]:
        """
        Signup with OTP verification.
        User provides mobile number and OTP code to verify ownership before account creation.
        """
        # Verify OTP first
        await OTPService.verify_otp(data.mobile_number, data.otp_code, purpose="signup")
        
        # Normalize email to lowercase
        email_normalized = data.email.lower().strip()
        
        # Check age
        if data.age < 18:
            raise HTTPException(status_code=400, detail="Must be 18 or older to register")

        try:
            # Check existing email (case-insensitive)
            email_regex = re.compile(f"^{re.escape(email_normalized)}$", re.IGNORECASE)
            existing_email = await TBUser.find_one({"email": email_regex})
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

        # Resolve referrer if referral_code provided
        referrer_id = None
        referrer = None
        if getattr(data, 'referral_code', None):
            referrer = await TBUser.find_one({"referral_code": data.referral_code.upper()})
            if referrer:
                referrer_id = str(referrer.id)

        # Create user
        user = TBUser(
            name=data.name,
            email=email_normalized,
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
                address_line="NA",
                city="NA",
                state="NA",
                country="India",
                pincode="000000"
            ),
            coins=10,  # Signup bonus
            is_verified=True,  # Verified via OTP
            current_device_id=data.device_id,
            referral_code=AuthService.generate_referral_code(data.name),
            referred_by=referrer_id
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

        # Award referral bonus to referrer (50 coins)
        if referrer_id:
            try:
                from backend.services.tb_credit_service import CreditService
                await CreditService.add_credits(
                    user_id=referrer_id,
                    amount=50,
                    reason=TransactionReason.REFERRAL_REWARD,
                    reference_id=str(user.id),
                    description=f"Referral reward for inviting {user.name}"
                )
                await TBUser.find_one({"_id": ObjectId(referrer_id)}).update(
                    {"$inc": {"referral_rewards_count": 1}}
                )

                # Emit balance update to referrer if online
                from backend.socket_server import emit_notification_to_user
                referrer_new_balance = await CreditService.get_balance(referrer_id)
                await emit_notification_to_user(referrer_id, "balance_updated", {"coins": referrer_new_balance})

                logger.info(
                    "Referral reward granted", 
                    extra={
                        "referrer_id": referrer_id,
                        "new_user_id": str(user.id),
                        "coins_added": 50
                    }
                )
            except Exception as ref_err:
                logger.warning(f"Failed to process referral reward (OTP signup): {ref_err}")

        # Generate tokens
        tokens = TokenResponse(
            access_token=AuthService.create_access_token(str(user.id), user.role),
            refresh_token=AuthService.create_refresh_token(str(user.id), user.role),
            user_id=str(user.id)
        )

        return user, tokens

    @staticmethod
    async def login_with_otp(data: LoginWithOTPRequest) -> Tuple[TBUser, TokenResponse]:
        """
        Login with OTP verification.
        User provides mobile number or email and OTP code to authenticate.
        """
        identifier = data.email.lower() if data.email else data.mobile_number
        if not identifier:
            raise HTTPException(status_code=400, detail="Missing identifier (email or mobile number)")

        # Verify OTP
        if data.email:
            await OTPService.verify_email_otp(data.email.lower(), data.otp_code, purpose="login")
        else:
            await OTPService.verify_otp(data.mobile_number, data.otp_code, purpose="login")
        
        # Find user
        try:
            if data.email:
                email_regex = re.compile(f"^{re.escape(data.email.lower())}$", re.IGNORECASE)
                user = await TBUser.find_one({"email": email_regex})
            else:
                user = await TBUser.find_one({"mobile_number": data.mobile_number})
        except Exception as e:
            raise HTTPException(status_code=503, detail="Database not available. Please try again later.")
        
        if not user:
            id_type = "email" if data.email else "mobile number"
            raise HTTPException(status_code=401, detail=f"User not found with this {id_type}")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        # Single-device enforcement: force-logout any previously logged-in device
        if user.current_device_id and user.current_device_id != data.device_id:
            try:
                from backend.socket_server import emit_notification_to_user
                await emit_notification_to_user(str(user.id), "force_logout", {
                    "reason": "Logged in from a new device",
                    "new_device_id": data.device_id
                })
                logging.info(f"force_logout (otp) emitted for user {user.id}")
            except Exception as force_logout_err:
                logging.warning(f"Could not send force_logout (otp): {force_logout_err}")

        # Update last login and session
        user.last_login_at = datetime.now(timezone.utc)
        user.is_online = True
        user.current_device_id = data.device_id
        await user.save()

        tokens = TokenResponse(
            access_token=AuthService.create_access_token(str(user.id), user.role),
            refresh_token=AuthService.create_refresh_token(str(user.id), user.role),
            user_id=str(user.id)
        )

        return user, tokens

    @staticmethod
    async def approve_login(pending_session_id: str, user_id: str):
        """Approve a pending login request from another device"""
        from bson import ObjectId
        pending = await PendingSession.get(ObjectId(pending_session_id))
        if not pending or pending.user_id != user_id or pending.status != "pending":
            raise HTTPException(status_code=404, detail="Pending session not found or already processed")
        
        pending.status = "approved"
        await pending.save()
        
        # Logout the old device (current session user)
        # Note: We'll update the user model when the new login is actually completed via polling
        return {"message": "Login approved"}

    @staticmethod
    async def deny_login(pending_session_id: str, user_id: str):
        """Deny a pending login request from another device"""
        from bson import ObjectId
        pending = await PendingSession.get(ObjectId(pending_session_id))
        if not pending or pending.user_id != user_id or pending.status != "pending":
            raise HTTPException(status_code=404, detail="Pending session not found or already processed")
        
        pending.status = "denied"
        await pending.save()
        return {"message": "Login denied"}

    @staticmethod
    async def check_login_status(pending_session_id: str):
        """Check status of pending login and return tokens if approved"""
        from bson import ObjectId
        pending = await PendingSession.get(ObjectId(pending_session_id))
        if not pending:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if pending.status == "approved":
            user = await TBUser.get(ObjectId(pending.user_id))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Force logout old device by updating user's current_device_id
            user.current_device_id = pending.new_device_id
            user.last_login_at = datetime.now(timezone.utc)
            await user.save()
            
            # Notify old device to logout
            from backend.socket_server import emit_notification_to_user
            await emit_notification_to_user(str(user.id), "force_logout", {"message": "Logged out because of login on another device"})

            tokens = TokenResponse(
                access_token=AuthService.create_access_token(str(user.id)),
                refresh_token=AuthService.create_refresh_token(str(user.id)),
                user_id=str(user.id)
            )
            return {"status": "approved", "tokens": tokens.model_dump(), "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "credits": user.credits_balance
            }}
        
        return {"status": pending.status}

    @staticmethod
    async def verify_mobile_number(mobile_number: str, otp_code: str) -> TBUser:
        """
        Verify mobile number for existing user.
        Marks user as verified after successful OTP verification.
        """
        # Verify OTP
        await OTPService.verify_otp(mobile_number, otp_code, purpose="verification")
        
        # Find and update user
        user = await TBUser.find_one({"mobile_number": mobile_number})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_verified = True
        await user.save()
        
        return user
