import redis.asyncio as aioredis
from backend.config import settings
import time

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return redis_client


async def check_ws_rate(user_id: str, ip: str) -> tuple[bool, int]:
    redis = await get_redis()
    now = int(time.time())
    window = now // 5
    
    user_key = f"ws:user:{user_id}:{window}"
    ip_key = f"ws:ip:{ip}:{window}"
    
    user_count = await redis.incr(user_key)
    if user_count == 1:
        await redis.expire(user_key, 10)
    
    ip_count = await redis.incr(ip_key)
    if ip_count == 1:
        await redis.expire(ip_key, 10)
    
    if user_count > 30:
        ttl = await redis.ttl(user_key)
        return (False, max(ttl, 5))
    
    if ip_count > 60:
        ttl = await redis.ttl(ip_key)
        return (False, max(ttl, 5))
    
    return (True, 0)


async def mute_user(user_id: str, seconds: int):
    redis = await get_redis()
    mute_key = f"muted:user:{user_id}"
    await redis.setex(mute_key, seconds, "1")


async def is_muted(user_id: str) -> bool:
    redis = await get_redis()
    mute_key = f"muted:user:{user_id}"
    return await redis.exists(mute_key) > 0


async def unmute_user(user_id: str):
    redis = await get_redis()
    mute_key = f"muted:user:{user_id}"
    await redis.delete(mute_key)


async def list_muted():
    redis = await get_redis()
    cursor = 0
    muted_users = []
    
    while True:
        cursor, keys = await redis.scan(cursor, match="muted:user:*", count=100)
        for key in keys:
            user_id = key.replace("muted:user:", "")
            ttl = await redis.ttl(key)
            muted_users.append({"user_id": user_id, "ttl": ttl})
        if cursor == 0:
            break
    
    return muted_users