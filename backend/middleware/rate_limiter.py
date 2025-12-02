import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from collections import defaultdict

# In-memory rate limiting (for development without Redis)
class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60, ban_threshold_per_minute: int = 150, ban_seconds: int = 3600):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.ban_threshold = ban_threshold_per_minute
        self.ban_seconds = ban_seconds
        self.request_counts = defaultdict(list)
        self.banned_ips = {}

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Check if banned
        if client in self.banned_ips:
            ban_time, ban_until = self.banned_ips[client]
            if now < ban_until:
                retry_after = int(ban_until - now)
                return JSONResponse({"detail": "ip_banned", "retry_after": retry_after}, status_code=429)
            else:
                del self.banned_ips[client]
        
        # Clean old requests (older than 60 seconds)
        self.request_counts[client] = [t for t in self.request_counts[client] if now - t < 60]
        
        # Add current request
        self.request_counts[client].append(now)
        
        # Check if should ban
        if len(self.request_counts[client]) > self.ban_threshold:
            self.banned_ips[client] = (now, now + self.ban_seconds)
            return JSONResponse({"detail": "rate_limit_exceeded", "retry_after": self.ban_seconds}, status_code=429)
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