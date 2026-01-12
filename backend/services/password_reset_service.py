"""
Password Reset Service
Handles forgot password and reset password functionality
"""
import secrets
import logging
from typing import Optional, Tuple
from datetime import datetime, timezone

from backend.core.redis_client import redis_client
from backend.services.email_service import email_service
from backend.models.tb_user import TBUser
import bcrypt

logger = logging.getLogger("password_reset")

class PasswordResetService:
    """Service for handling password reset operations"""

    def __init__(self):
        self.token_expiry = 600  # 10 minutes in seconds
        self.redis_prefix = "password_reset:"

    def generate_reset_token(self) -> str:
        """Generate a secure random token for password reset"""
        return secrets.token_urlsafe(32)

    async def create_reset_token(
        self,
        email: str,
        db,
        frontend_url: str
    ) -> Tuple[bool, str]:
        """
        Create a password reset token for the user.

        Args:
            email: User's email address
            db: MongoDB database connection
            frontend_url: Frontend URL for reset link

        Returns:
            (success: bool, message: str)
        """
        try:
            # Find user by email
            user = await db.users.find_one({"email": email.lower()})

            # For security, don't reveal if email exists
            if not user:
                logger.info(f"Password reset requested for non-existent email: {email}")
                return (True, "If email exists, reset link has been sent")

            # Generate secure token
            token = self.generate_reset_token()

            # Store token in Redis with user ID
            redis_key = f"{self.redis_prefix}{token}"

            if redis_client.is_connected():
                # Use Redis for token storage (production-safe)
                await redis_client.redis.setex(
                    redis_key,
                    self.token_expiry,
                    str(user["_id"])
                )
                logger.info(f"Password reset token stored in Redis for user {user['_id']}")
            else:
                # Fallback: Store in MongoDB (not ideal but functional)
                await db.password_reset_tokens.insert_one({
                    "token": token,
                    "user_id": user["_id"],
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": datetime.now(timezone.utc).timestamp() + self.token_expiry,
                    "used": False
                })
                logger.warning("Redis not available, storing token in MongoDB")

            # Generate reset link
            reset_link = f"{frontend_url}/reset-password?token={token}"

            # Send email
            email_sent = await email_service.send_password_reset_email(
                to=email,
                reset_link=reset_link,
                user_name=user.get("name")
            )

            if not email_sent:
                logger.error(f"Failed to send reset email to {email}")

            return (True, "If email exists, reset link has been sent")

        except Exception as e:
            logger.error(f"Error creating reset token: {e}", exc_info=True)
            return (False, "Failed to process password reset request")

    async def validate_reset_token(
        self,
        token: str,
        db
    ) -> Optional[str]:
        """
        Validate reset token and return user ID if valid.

        Args:
            token: Reset token
            db: MongoDB database connection

        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            redis_key = f"{self.redis_prefix}{token}"

            if redis_client.is_connected():
                # Check Redis
                user_id = await redis_client.redis.get(redis_key)
                if user_id:
                    return user_id
            else:
                # Fallback: Check MongoDB
                token_doc = await db.password_reset_tokens.find_one({
                    "token": token,
                    "used": False
                })

                if token_doc:
                    # Check expiration
                    if datetime.now(timezone.utc).timestamp() < token_doc["expires_at"]:
                        return str(token_doc["user_id"])
                    else:
                        logger.info("Token expired")

            return None

        except Exception as e:
            logger.error(f"Error validating reset token: {e}")
            return None

    async def reset_password(
        self,
        token: str,
        new_password: str,
        db
    ) -> Tuple[bool, str]:
        """
        Reset user's password using the provided token.

        Args:
            token: Reset token
            new_password: New password
            db: MongoDB database connection

        Returns:
            (success: bool, message: str)
        """
        try:
            # Validate token
            user_id = await self.validate_reset_token(token, db)

            if not user_id:
                return (False, "Invalid or expired token")

            # Validate password strength
            if len(new_password) < 8:
                return (False, "Password must be at least 8 characters long")

            # Hash new password
            hashed_password = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            # Update user's password
            from bson import ObjectId
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password": hashed_password,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count == 0:
                return (False, "Failed to update password")

            # Delete/invalidate token
            redis_key = f"{self.redis_prefix}{token}"

            if redis_client.is_connected():
                await redis_client.redis.delete(redis_key)
            else:
                await db.password_reset_tokens.update_one(
                    {"token": token},
                    {"$set": {"used": True}}
                )

            # Get user email for notification
            user = await db.users.find_one({"_id": ObjectId(user_id)})

            if user and user.get("email"):
                # Send confirmation email
                await email_service.send_password_changed_notification(
                    to=user["email"],
                    user_name=user.get("name")
                )

            logger.info(f"Password reset successful for user {user_id}")
            return (True, "Password reset successful")

        except Exception as e:
            logger.error(f"Error resetting password: {e}", exc_info=True)
            return (False, "Failed to reset password")

    async def cleanup_expired_tokens(self, db):
        """
        Cleanup expired tokens from MongoDB fallback storage.
        This is a maintenance task that should run periodically.
        """
        try:
            if not redis_client.is_connected():
                current_time = datetime.now(timezone.utc).timestamp()
                result = await db.password_reset_tokens.delete_many({
                    "expires_at": {"$lt": current_time}
                })
                if result.deleted_count > 0:
                    logger.info(f"Cleaned up {result.deleted_count} expired tokens")
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")


password_reset_service = PasswordResetService()
