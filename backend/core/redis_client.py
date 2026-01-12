import redis.asyncio as aioredis
from typing import Optional, Tuple
import os
import time
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("redis")


class RedisClient:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._connected = False

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._connected and self.redis is not None

    async def connect(self):
        """Initialize Redis connection"""
        if not self.redis:
            try:
                self.redis = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis.ping()
                self._connected = True
                logger.info(f"Redis connected: {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis = None
                self._connected = False

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            self._connected = False

    @asynccontextmanager
    async def acquire_lock(self, key: str, ttl: int = 60):
        """Acquire a distributed lock for idempotency"""
        lock_key = f"lock:{key}"
        acquired = False
        try:
            if self.redis:
                acquired = await self.redis.set(lock_key, "1", ex=ttl, nx=True)
                if not acquired:
                    yield False
                    return
            yield True
        finally:
            if acquired and self.redis:
                await self.redis.delete(lock_key)

    async def rate_limit_check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using sliding window.
        Returns: (allowed, current_count, remaining_seconds)
        """
        if not self.redis:
            return (True, 0, 0)
        
        full_key = f"rate:{key}"
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(full_key, 0, window_start)
        pipe.zadd(full_key, {str(current_time): current_time})
        pipe.zcard(full_key)
        pipe.expire(full_key, window_seconds)
        
        results = await pipe.execute()
        current_count = results[2]
        
        if current_count > max_requests:
            ttl = await self.redis.ttl(full_key)
            return (False, current_count, ttl)
        
        return (True, current_count, 0)

    async def otp_rate_limit_check(
        self,
        identifier: str,
        action: str = "send"
    ) -> Tuple[bool, str]:
        """
        OTP-specific rate limiting.
        - send: max 3 per hour
        - verify: max 5 attempts per OTP
        Returns: (allowed, error_message)
        """
        if not self.redis:
            return (True, "")
        
        if action == "send":
            allowed, count, remaining = await self.rate_limit_check(
                f"otp_send:{identifier}",
                max_requests=3,
                window_seconds=3600
            )
            if not allowed:
                return (False, f"Too many OTP requests. Try again in {remaining} seconds.")
            return (True, "")
        
        elif action == "verify":
            key = f"otp_verify:{identifier}"
            attempts = await self.redis.incr(key)
            if attempts == 1:
                await self.redis.expire(key, 600)
            
            if attempts > 5:
                return (False, "Too many verification attempts. OTP locked.")
            return (True, "")
        
        return (True, "")

    async def clear_otp_verify_attempts(self, identifier: str):
        """Clear OTP verification attempts after success"""
        if self.redis:
            await self.redis.delete(f"otp_verify:{identifier}")

    async def login_rate_limit(self, identifier: str) -> Tuple[bool, int]:
        """
        Login rate limiting: max 5 attempts per 15 minutes.
        Returns: (allowed, remaining_seconds)
        """
        if not self.redis:
            return (True, 0)
        
        key = f"login:{identifier}"
        attempts = await self.redis.incr(key)
        
        if attempts == 1:
            await self.redis.expire(key, 900)
        
        if attempts > 5:
            ttl = await self.redis.ttl(key)
            return (False, ttl)
        
        return (True, 0)

    async def clear_login_attempts(self, identifier: str):
        """Clear login attempts after successful login"""
        if self.redis:
            await self.redis.delete(f"login:{identifier}")

    async def cache_subscription(self, user_id: str, is_subscribed: bool, ttl: int = 300):
        """Cache subscription status for a user"""
        if not self.redis:
            return
        key = f"subscription:{user_id}"
        await self.redis.setex(key, ttl, str(int(is_subscribed)))

    async def get_cached_subscription(self, user_id: str) -> Optional[bool]:
        """Get cached subscription status"""
        if not self.redis:
            return None
        key = f"subscription:{user_id}"
        value = await self.redis.get(key)
        if value is None:
            return None
        return bool(int(value))

    async def invalidate_subscription_cache(self, user_id: str):
        """Invalidate cached subscription status"""
        if not self.redis:
            return
        key = f"subscription:{user_id}"
        await self.redis.delete(key)

    async def store_session(self, user_id: str, session_id: str, device_info: str, ttl: int = 86400 * 7):
        """Store user session for multi-device tracking"""
        if not self.redis:
            return
        key = f"sessions:{user_id}"
        await self.redis.hset(key, session_id, device_info)
        await self.redis.expire(key, ttl)

    async def get_user_sessions(self, user_id: str) -> dict:
        """Get all active sessions for a user"""
        if not self.redis:
            return {}
        return await self.redis.hgetall(f"sessions:{user_id}") or {}

    async def revoke_session(self, user_id: str, session_id: str):
        """Revoke a specific session"""
        if self.redis:
            await self.redis.hdel(f"sessions:{user_id}", session_id)

    async def revoke_all_sessions(self, user_id: str):
        """Revoke all sessions for a user (logout everywhere)"""
        if self.redis:
            await self.redis.delete(f"sessions:{user_id}")

    async def health_check(self) -> dict:
        """Comprehensive health check for Redis"""
        if not self.redis:
            return {
                "status": "disconnected",
                "connected": False,
                "error": "Redis client not initialized"
            }

        try:
            # Test ping
            await self.redis.ping()

            # Test write
            test_key = "health_check_test"
            await self.redis.setex(test_key, 10, "ok")

            # Test read
            test_value = await self.redis.get(test_key)

            # Cleanup
            await self.redis.delete(test_key)

            if test_value == "ok":
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


redis_client = RedisClient()
