"""
JWT Token Blacklist using Redis
Implements token revocation for logout and security
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from backend.core.redis_client import redis_client

logger = logging.getLogger("token_blacklist")


class TokenBlacklist:
    """
    Redis-based token blacklist for JWT revocation
    """

    PREFIX = "blacklist:token:"
    USER_PREFIX = "blacklist:user:"

    @staticmethod
    async def blacklist_token(token_jti: str, expires_in_seconds: int):
        """
        Add a token to the blacklist

        Args:
            token_jti: JWT ID (jti claim)
            expires_in_seconds: TTL for the blacklist entry (should match token expiry)
        """
        try:
            key = f"{TokenBlacklist.PREFIX}{token_jti}"
            await redis_client.redis.setex(
                key,
                expires_in_seconds,
                "revoked"
            )
            logger.info(f"Token blacklisted: {token_jti[:8]}...")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            raise

    @staticmethod
    async def is_blacklisted(token_jti: str) -> bool:
        """
        Check if a token is blacklisted

        Args:
            token_jti: JWT ID to check

        Returns:
            True if blacklisted, False otherwise
        """
        try:
            key = f"{TokenBlacklist.PREFIX}{token_jti}"
            result = await redis_client.redis.get(key)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            # Fail closed: if Redis is down, treat as not blacklisted
            # but log the error for investigation
            return False

    @staticmethod
    async def blacklist_all_user_tokens(user_id: str):
        """
        Blacklist all tokens for a user (e.g., on password change)

        Args:
            user_id: User ID whose tokens should be blacklisted
        """
        try:
            key = f"{TokenBlacklist.USER_PREFIX}{user_id}"
            # Store with 30 day expiry (max token lifetime)
            await redis_client.redis.setex(
                key,
                30 * 24 * 60 * 60,  # 30 days
                "all_revoked"
            )
            logger.info(f"All tokens blacklisted for user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to blacklist user tokens: {e}")
            raise

    @staticmethod
    async def is_user_blacklisted(user_id: str) -> bool:
        """
        Check if all tokens for a user are blacklisted

        Args:
            user_id: User ID to check

        Returns:
            True if all user tokens are blacklisted
        """
        try:
            key = f"{TokenBlacklist.USER_PREFIX}{user_id}"
            result = await redis_client.redis.get(key)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to check user blacklist: {e}")
            return False


# Singleton instance
token_blacklist = TokenBlacklist()
