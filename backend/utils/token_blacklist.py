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
        Check if a token is blacklisted.
        Robust check to avoid NoneType errors.
        """
        if not token_jti:
            return False
            
        try:
            # Add defensive check for redis_client.redis
            if redis_client is None:
                logger.warning("Redis client is None")
                return False
            
            redis_conn = getattr(redis_client, 'redis', None)
            if redis_conn is None:
                logger.warning("Redis connection is None")
                return False
                
            key = f"{TokenBlacklist.PREFIX}{token_jti}"
            result = await redis_conn.get(key)
            
            # Properly check for None - never call .get() on result
            if result is None:
                return False
            return True
        except AttributeError as e:
            logger.error(f"Failed to check blacklist (AttributeError): {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
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
        Check if all tokens for a user are blacklisted.
        Robust check to avoid NoneType errors.
        """
        if not user_id:
            return False
            
        try:
            # Add defensive check for redis_client.redis
            if redis_client is None:
                logger.warning("Redis client is None")
                return False
            
            redis_conn = getattr(redis_client, 'redis', None)
            if redis_conn is None:
                logger.warning("Redis connection is None")
                return False
                
            key = f"{TokenBlacklist.USER_PREFIX}{user_id}"
            result = await redis_conn.get(key)
            
            # Properly check for None - never call .get() on result
            if result is None:
                return False
            return True
        except AttributeError as e:
            logger.error(f"Failed to check user blacklist (AttributeError): {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to check user blacklist: {e}")
            return False


# Singleton instance
token_blacklist = TokenBlacklist()
