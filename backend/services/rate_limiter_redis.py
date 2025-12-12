import time
import os

try:
    import aioredis
except:
    aioredis = None

class RateLimiter:
    def __init__(self, redis_url=None):
        self.redis = None
        self.url = redis_url

    async def init(self):
        if aioredis and self.url:
            self.redis = await aioredis.from_url(self.url)

    async def allow(self, key: str, limit: int, window: int):
        if not self.redis:
            # in-memory fallback naive
            return True
        now = int(time.time())
        pipe = self.redis.pipeline()
        await self.redis.zadd(key, {str(now): now})
        await self.redis.zremrangebyscore(key, 0, now - window)
        cnt = await self.redis.zcard(key)
        await self.redis.expire(key, window+2)
        return cnt <= limit

rate_limiter = RateLimiter(redis_url=os.getenv("REDIS_URL"))
