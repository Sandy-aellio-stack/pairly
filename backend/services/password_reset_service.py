"""
Password Reset Service - Production Ready
Handles forgot password and reset password functionality with proper security.

Security Features:
- Cryptographically secure tokens (32 bytes / 256 bits)
- Tokens are SHA-256 hashed before storage
- Token expiry: 15 minutes
- Single-use tokens (invalidated after use)
- Rate limiting on token generation
- No email enumeration (always return success)
"""
import secrets
import hashlib
import logging
import re
from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta

from backend.core.redis_client import redis_client
from backend.services.email_service import email_service
from backend.models.tb_user import TBUser
import bcrypt

logger = logging.getLogger("password_reset")


class PasswordResetService:
    """Service for handling password reset operations"""

    # Token configuration
    TOKEN_BYTES = 32  # 256 bits of entropy
    TOKEN_EXPIRY_MINUTES = 15
    
    # Redis key prefixes
    REDIS_TOKEN_PREFIX = "pwd_reset:token:"
    REDIS_RATE_LIMIT_PREFIX = "pwd_reset:rate:"
    
    # Rate limiting
    MAX_REQUESTS_PER_HOUR = 5  # Max reset requests per email per hour
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    )

    def __init__(self):
        self.token_expiry_seconds = self.TOKEN_EXPIRY_MINUTES * 60

    def _generate_token(self) -> str:
        """Generate a cryptographically secure reset token"""
        return secrets.token_urlsafe(self.TOKEN_BYTES)
    
    def _hash_token(self, token: str) -> str:
        """
        Hash token using SHA-256 for secure storage.
        We never store plaintext tokens.
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password meets minimum requirements.
        
        Requirements:
        - At least 8 characters
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one digit
        """
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, "Password meets requirements"

    async def _check_rate_limit(self, email: str) -> bool:
        """
        Check if email has exceeded rate limit for reset requests.
        Returns True if allowed, False if rate limited.
        """
        if not redis_client.is_connected():
            return True  # Allow if Redis not available
        
        rate_key = f"{self.REDIS_RATE_LIMIT_PREFIX}{email.lower()}"
        
        try:
            count = await redis_client.redis.get(rate_key)
            if count and int(count) >= self.MAX_REQUESTS_PER_HOUR:
                logger.warning(f"Rate limit exceeded for email: {email}")
                return False
            
            # Increment counter
            pipe = redis_client.redis.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, 3600)  # 1 hour
            await pipe.execute()
            
            return True
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error

    async def create_reset_token(
        self,
        email: str,
        frontend_url: str
    ) -> Tuple[bool, str]:
        """
        Create a password reset token and send reset email.
        
        Security measures:
        - Check rate limiting
        - Generate cryptographically secure token
        - Hash token before storage
        - Never reveal if email exists
        
        Args:
            email: User's email address
            frontend_url: Frontend URL for reset link
            
        Returns:
            (success: bool, message: str)
        """
        try:
            email_lower = email.lower().strip()
            
            # Check rate limit
            if not await self._check_rate_limit(email_lower):
                # Still return success to prevent enumeration
                return True, "If email exists, reset link has been sent"
            
            # Find user by email using Beanie - use dict query
            try:
                user = await TBUser.find_one({"email": email_lower})
            except Exception as db_error:
                # Database might not be initialized or available
                logger.warning(f"Database query failed: {db_error}")
                # Still return success to prevent information leakage
                return True, "If email exists, reset link has been sent"
            
            # For security, don't reveal if email exists
            if not user:
                logger.info(f"Password reset requested for non-existent email: {email_lower}")
                return True, "If email exists, reset link has been sent"
            
            # Check if Redis is available for token storage
            if not redis_client.is_connected():
                logger.error("Redis not available for token storage")
                # Still return success to prevent information leakage
                return True, "If email exists, reset link has been sent"
            
            # Invalidate any existing tokens for this user
            await self._invalidate_existing_tokens(str(user.id))
            
            # Generate secure token
            token = self._generate_token()
            token_hash = self._hash_token(token)
            
            # Store hashed token with user ID and expiry metadata
            await self._store_token(
                token_hash=token_hash,
                user_id=str(user.id),
                user_email=email_lower
            )
            
            # Generate reset link with unhashed token
            reset_link = f"{frontend_url}/reset-password?token={token}"
            
            # Send email
            email_sent = await email_service.send_password_reset_email(
                to=email_lower,
                reset_link=reset_link,
                user_name=user.name
            )
            
            if email_sent:
                logger.info(f"Password reset email sent to {email_lower}")
            else:
                logger.error(f"Failed to send reset email to {email_lower}")
            
            return True, "If email exists, reset link has been sent"
            
        except Exception as e:
            logger.error(f"Error creating reset token: {e}", exc_info=True)
            # Still return success to prevent information leakage
            return True, "If email exists, reset link has been sent"

    async def _store_token(
        self,
        token_hash: str,
        user_id: str,
        user_email: str
    ) -> None:
        """Store hashed token in Redis with expiry"""
        token_key = f"{self.REDIS_TOKEN_PREFIX}{token_hash}"
        
        # Store token data as JSON string
        import json
        token_data = json.dumps({
            "user_id": user_id,
            "email": user_email,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        if redis_client.is_connected():
            await redis_client.redis.setex(
                token_key,
                self.token_expiry_seconds,
                token_data
            )
            
            # Also store reverse lookup (user_id -> token_hash) for invalidation
            user_token_key = f"pwd_reset:user:{user_id}"
            await redis_client.redis.setex(
                user_token_key,
                self.token_expiry_seconds,
                token_hash
            )
            
            logger.debug(f"Stored reset token for user {user_id}, expires in {self.TOKEN_EXPIRY_MINUTES} minutes")
        else:
            logger.warning("Redis not available - password reset tokens cannot be stored")
            raise Exception("Token storage unavailable")

    async def _invalidate_existing_tokens(self, user_id: str) -> None:
        """Invalidate any existing reset tokens for a user"""
        if not redis_client.is_connected():
            return
        
        try:
            user_token_key = f"pwd_reset:user:{user_id}"
            existing_hash = await redis_client.redis.get(user_token_key)
            
            if existing_hash:
                # Delete the old token
                old_token_key = f"{self.REDIS_TOKEN_PREFIX}{existing_hash}"
                await redis_client.redis.delete(old_token_key)
                await redis_client.redis.delete(user_token_key)
                logger.debug(f"Invalidated existing token for user {user_id}")
        except Exception as e:
            logger.error(f"Error invalidating existing tokens: {e}")

    async def validate_reset_token(self, token: str) -> Optional[dict]:
        """
        Validate a reset token and return user info if valid.
        
        Args:
            token: The plaintext token from the reset link
            
        Returns:
            Dict with user_id and email if valid, None otherwise
        """
        if not token:
            return None
        
        try:
            token_hash = self._hash_token(token)
            token_key = f"{self.REDIS_TOKEN_PREFIX}{token_hash}"
            
            if not redis_client.is_connected():
                logger.error("Redis not available for token validation")
                return None
            
            token_data = await redis_client.redis.get(token_key)
            
            if not token_data:
                logger.info("Reset token not found or expired")
                return None
            
            import json
            data = json.loads(token_data)
            
            logger.debug(f"Token validated for user {data.get('user_id')}")
            return data
            
        except Exception as e:
            logger.error(f"Error validating reset token: {e}")
            return None

    async def reset_password(
        self,
        token: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        Reset user's password using the provided token.
        
        Security measures:
        - Validate token exists and not expired
        - Validate password strength
        - Hash new password with bcrypt
        - Immediately invalidate token after use
        - Send confirmation email
        
        Args:
            token: Reset token from email link
            new_password: User's new password
            
        Returns:
            (success: bool, message: str)
        """
        try:
            # Validate token first
            token_data = await self.validate_reset_token(token)
            
            if not token_data:
                return False, "Invalid or expired reset link. Please request a new one."
            
            user_id = token_data.get("user_id")
            user_email = token_data.get("email")
            
            # Validate password strength
            is_valid, message = self._validate_password_strength(new_password)
            if not is_valid:
                return False, message
            
            # Find user
            user = await TBUser.get(user_id)
            
            if not user:
                logger.error(f"User {user_id} not found during password reset")
                return False, "User not found"
            
            # Hash new password
            password_hash = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt(rounds=12)
            ).decode('utf-8')
            
            # Update user's password
            user.password_hash = password_hash
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
            
            # Immediately invalidate the token (single-use)
            await self._invalidate_token(token)
            
            # Send confirmation email
            await email_service.send_password_changed_notification(
                to=user_email,
                user_name=user.name
            )
            
            logger.info(f"Password reset successful for user {user_id}")
            return True, "Password reset successful. You can now login with your new password."
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}", exc_info=True)
            return False, "Failed to reset password. Please try again."

    async def _invalidate_token(self, token: str) -> None:
        """Invalidate a token after successful use"""
        if not redis_client.is_connected():
            return
        
        try:
            token_hash = self._hash_token(token)
            token_key = f"{self.REDIS_TOKEN_PREFIX}{token_hash}"
            
            # Get user_id before deleting
            token_data = await redis_client.redis.get(token_key)
            if token_data:
                import json
                data = json.loads(token_data)
                user_id = data.get("user_id")
                
                # Delete token and user lookup
                await redis_client.redis.delete(token_key)
                if user_id:
                    await redis_client.redis.delete(f"pwd_reset:user:{user_id}")
                
                logger.debug(f"Invalidated reset token after use")
        except Exception as e:
            logger.error(f"Error invalidating token: {e}")

    def get_token_info(self) -> dict:
        """Get token configuration info (for debugging/admin)"""
        return {
            "token_bytes": self.TOKEN_BYTES,
            "token_entropy_bits": self.TOKEN_BYTES * 8,
            "expiry_minutes": self.TOKEN_EXPIRY_MINUTES,
            "rate_limit_per_hour": self.MAX_REQUESTS_PER_HOUR,
            "password_min_length": self.MIN_PASSWORD_LENGTH,
            "storage": "redis",
            "hashing": "sha256"
        }


# Global singleton instance
password_reset_service = PasswordResetService()
