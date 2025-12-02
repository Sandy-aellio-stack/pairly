import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis.asyncio as aioredis
from backend.config import settings
from backend.services.audit import log_event

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return redis_client


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 30, ban_threshold_per_minute: int = 150, ban_seconds: int = 3600):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.ban_threshold = ban_threshold_per_minute
        self.ban_seconds = ban_seconds

    async def dispatch(self, request: Request, call_next):
        redis = await get_redis()
        client = request.client.host if request.client else "unknown"
        
        now = int(time.time())
        window_start = now - 60
        
        ban_key = f"banned:ip:{client}"
        is_banned = await redis.get(ban_key)
        if is_banned:
            ttl = await redis.ttl(ban_key)
            retry_after = max(ttl, 0)
            return JSONResponse({"detail": "ip_banned", "retry_after": retry_after}, status_code=429)
        
        ip_key = f"rl:ip:{client}"
        ip_count = await redis.incr(ip_key)
        if ip_count == 1:
            await redis.expire(ip_key, 60)
        
        if ip_count > self.ban_threshold:
            await redis.setex(ban_key, self.ban_seconds, "1")
            await log_event(
                actor_user_id=None,
                actor_ip=client,
                action="ip_banned",
                details={"ip": client, "count": ip_count},
                severity="warning"
            )
            return JSONResponse({"detail": "ip_banned", "retry_after": self.ban_seconds}, status_code=429)
        
        if ip_count > self.requests_per_minute:
            ttl = await redis.ttl(ip_key)
            retry_after = max(ttl, 0)
            return JSONResponse({"detail": "rate_limited", "retry_after": retry_after}, status_code=429)
        
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            user_key = f"rl:token:{token[:20]}"
            user_count = await redis.incr(user_key)
            if user_count == 1:
                await redis.expire(user_key, 60)
            
            if user_count > self.requests_per_minute:
                ttl = await redis.ttl(user_key)
                retry_after = max(ttl, 0)
                return JSONResponse({"detail": "rate_limited", "retry_after": retry_after}, status_code=429)
        
        response = await call_next(request)
        return response


async def get_banned_ips():
    redis = await get_redis()
    cursor = 0
    banned_ips = []
    
    while True:
        cursor, keys = await redis.scan(cursor, match="banned:ip:*", count=100)
        for key in keys:
            ip = key.replace("banned:ip:", "")
            ttl = await redis.ttl(key)
            banned_ips.append({"ip": ip, "ttl": ttl})
        if cursor == 0:
            break
    
    return banned_ips


async def unban_ip(ip: str):
    redis = await get_redis()
    ban_key = f"banned:ip:{ip}"
    await redis.delete(ban_key)
    return True