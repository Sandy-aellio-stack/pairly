import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis

async def set_user_refresh_jti(user_id: str, jti: str, ttl_days: int = 7):
    r = await get_redis()
    await r.setex(f"user_refresh:{user_id}", ttl_days * 86400, jti)

async def validate_user_refresh_jti(user_id: str, jti: str) -> bool:
    r = await get_redis()
    stored = await r.get(f"user_refresh:{user_id}")
    return stored == jti
