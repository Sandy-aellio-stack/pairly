import redis.asyncio as aioredis
from typing import Optional
import os
from contextlib import asynccontextmanager

class RedisClient:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    async def connect(self):
        """Initialize Redis connection"""
        if not self.redis:
            try:
                self.redis = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self.redis.ping()
                print(f"✓ Redis connected: {self.redis_url}")
            except Exception as e:
                print(f"⚠ Redis connection failed: {e}")
                print("  Subscription features will work with degraded performance (no caching)")
                self.redis = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.redis = None

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

    @asynccontextmanager
    async def acquire_lock(self, key: str, ttl: int = 60):
        """Acquire a distributed lock for idempotency"""
        lock_key = f"lock:{key}"
        acquired = False
        try:
            if self.redis:
                acquired = await self.redis.set(lock_key, "1", ex=ttl, nx=True)
                if not acquired:
                    # Lock already held
                    yield False
                    return
            yield True
        finally:
            if acquired and self.redis:
                await self.redis.delete(lock_key)

    async def invalidate_subscription_cache(self, user_id: str):
        """Invalidate cached subscription status"""
        if not self.redis:
            return
        key = f"subscription:{user_id}"
        await self.redis.delete(key)

# Global instance
redis_client = RedisClient()
