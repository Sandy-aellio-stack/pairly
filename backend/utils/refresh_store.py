import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_redis = None
_redis_available = True

async def get_redis():
    global _redis, _redis_available
    if not _redis_available:
        return None
    if _redis is None:
        try:
            _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
            await _redis.ping()
        except Exception as e:
            print(f"⚠️  Redis unavailable for refresh token store: {e}")
            _redis_available = False
            _redis = None
    return _redis

async def set_user_refresh_jti(user_id: str, jti: str, ttl_days: int = 7):
    try:
        r = await get_redis()
        if r:
            await r.setex(f"user_refresh:{user_id}", ttl_days * 86400, jti)
    except Exception as e:
        print(f"⚠️  Failed to store refresh JTI: {e}")

async def validate_user_refresh_jti(user_id: str, jti: str) -> bool:
    try:
        r = await get_redis()
        if r:
            stored = await r.get(f"user_refresh:{user_id}")
            return stored == jti
        # If Redis is not available, allow the refresh (degraded mode)
        return True
    except Exception:
        # On error, allow the refresh (degraded mode)
        return True
