import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis

async def revoke_token(jti: str, ttl_seconds: int):
    r = await get_redis()
    await r.setex(f"revoked_jwt:{jti}", ttl_seconds, "1")

async def is_token_revoked(jti: str) -> bool:
    r = await get_redis()
    return await r.exists(f"revoked_jwt:{jti}") == 1

async def revoke_all_for_user(user_id: str):
    """Optional: pattern revoke - use carefully (may be expensive)."""
    r = await get_redis()
    keys = await r.keys(f"user_tokens:{user_id}:*")
    if keys:
        await r.delete(*keys)
