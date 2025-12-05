"""Redis client for caching and distributed operations.

Usage:
    from backend.core.redis_client import get_redis, cache_subscription
    
    redis = await get_redis()
    await redis.set('key', 'value')
"""
import aioredis
import os
from typing import Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    """Get or create Redis client."""
    global redis_client
    
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Continuing without Redis.")
            redis_client = None
    
    return redis_client


async def cache_subscription(user_id: str, tier_id: str, value: bool, ttl: int = 300):
    """Cache subscription check result."""
    try:
        redis = await get_redis()
        if redis:
            key = f"subscription:{user_id}:{tier_id}"
            await redis.setex(key, ttl, "1" if value else "0")
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")


async def get_cached_subscription(user_id: str, tier_id: str) -> Optional[bool]:
    """Get cached subscription check result."""
    try:
        redis = await get_redis()
        if not redis:
            return None
            
        key = f"subscription:{user_id}:{tier_id}"
        value = await redis.get(key)
        
        if value is None:
            return None
        
        return value == "1"
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")
        return None


async def invalidate_subscription_cache(user_id: str, tier_id: Optional[str] = None):
    """Invalidate subscription cache for a user."""
    try:
        redis = await get_redis()
        if not redis:
            return
        
        if tier_id:
            key = f"subscription:{user_id}:{tier_id}"
            await redis.delete(key)
        else:
            pattern = f"subscription:{user_id}:*"
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await redis.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis cache invalidation failed: {e}")


async def acquire_event_lock(event_id: str, ttl: int = 3600) -> bool:
    """Acquire lock for webhook event processing (idempotency)."""
    try:
        redis = await get_redis()
        if not redis:
            return True
        
        key = f"event_lock:{event_id}"
        result = await redis.set(key, "1", ex=ttl, nx=True)
        return result is not None
    except Exception as e:
        logger.warning(f"Redis lock acquisition failed: {e}")
        return True


async def release_event_lock(event_id: str):
    """Release webhook event lock."""
    try:
        redis = await get_redis()
        if redis:
            key = f"event_lock:{event_id}"
            await redis.delete(key)
    except Exception as e:
        logger.warning(f"Redis lock release failed: {e}")


async def cache_set(key: str, value: Any, ttl: Optional[int] = None):
    """Generic cache set."""
    try:
        redis = await get_redis()
        if not redis:
            return
        
        serialized = json.dumps(value)
        
        if ttl:
            await redis.setex(key, ttl, serialized)
        else:
            await redis.set(key, serialized)
    except Exception as e:
        logger.warning(f"Redis cache set failed: {e}")


async def cache_get(key: str) -> Optional[Any]:
    """Generic cache get."""
    try:
        redis = await get_redis()
        if not redis:
            return None
        
        value = await redis.get(key)
        
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    except Exception as e:
        logger.warning(f"Redis cache get failed: {e}")
        return None


async def cache_delete(key: str):
    """Delete cache key."""
    try:
        redis = await get_redis()
        if redis:
            await redis.delete(key)
    except Exception as e:
        logger.warning(f"Redis cache delete failed: {e}")
