"""
Enhanced Redis client with health check and advanced operations
Compatible with existing redis_client.py
"""
import redis.asyncio as aioredis
from typing import Optional
import os
import logging

logger = logging.getLogger("redis")

class RedisClientEnhanced:
    """Enhanced Redis client with health check support"""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.is_ready = False

    async def connect(self):
        """Initialize Redis connection"""
        if not self.redis:
            try:
                self.redis = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                await self.redis.ping()
                self.is_ready = True
                logger.info(f"✅ Redis connected: {self._mask_url(self.redis_url)}")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}")
                logger.warning("⚠️ Continuing without Redis (fallback mode)")
                self.redis = None
                self.is_ready = False

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            self.is_ready = False
            logger.info("Redis disconnected")

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self.redis is not None and self.is_ready

    async def ping(self) -> bool:
        """Ping Redis to check connection"""
        if not self.redis:
            return False
        try:
            result = await self.redis.ping()
            return result
        except Exception as e:
            logger.error(f"Redis PING error: {e}")
            self.is_ready = False
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.redis:
            return None
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        """Set value in Redis with optional expiration"""
        if not self.redis:
            return False
        try:
            await self.redis.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str):
        """Delete key from Redis"""
        if not self.redis:
            return False
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def health_check(self) -> dict:
        """Comprehensive health check"""
        if not self.redis:
            return {
                "status": "disconnected",
                "connected": False,
                "error": "Redis client not initialized"
            }

        try:
            # Test ping
            ping_result = await self.ping()

            # Test write
            test_key = "health_check_test"
            await self.set(test_key, "ok", ex=10)

            # Test read
            test_value = await self.get(test_key)

            # Cleanup
            await self.delete(test_key)

            if ping_result and test_value == "ok":
                return {
                    "status": "healthy",
                    "connected": True,
                    "url": self._mask_url(self.redis_url),
                    "operations": ["ping", "set", "get", "delete"]
                }
            else:
                return {
                    "status": "degraded",
                    "connected": True,
                    "error": "Operations test failed"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }

    def _mask_url(self, url: str) -> str:
        """Mask password in Redis URL for logging"""
        if "@" in url:
            parts = url.split("@")
            if ":" in parts[0]:
                proto_user_pass = parts[0].split(":")
                if len(proto_user_pass) >= 3:
                    return f"{proto_user_pass[0]}://***:***@{parts[1]}"
        return url
