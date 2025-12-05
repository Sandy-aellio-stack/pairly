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
            print(f"⚠️  Redis unavailable for JWT revocation: {e}")
            _redis_available = False
            _redis = None
    return _redis

async def revoke_token(jti: str, ttl_seconds: int):
    try:
        r = await get_redis()
        if r:
            await r.setex(f"revoked_jwt:{jti}", ttl_seconds, "1")
    except Exception as e:
        print(f"⚠️  Failed to revoke token in Redis: {e}")

async def is_token_revoked(jti: str) -> bool:
    try:
        r = await get_redis()
        if r:
            return await r.exists(f"revoked_jwt:{jti}") == 1
        return False
    except Exception:
        return False

async def revoke_all_for_user(user_id: str):
    """Optional: pattern revoke - use carefully (may be expensive)."""
    try:
        r = await get_redis()
        if r:
            keys = await r.keys(f"user_tokens:{user_id}:*")
            if keys:
                await r.delete(*keys)
    except Exception as e:
        print(f"⚠️  Failed to revoke user tokens: {e}")
