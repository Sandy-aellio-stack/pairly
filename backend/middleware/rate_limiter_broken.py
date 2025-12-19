import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from collections import defaultdict
from backend.core.redis_rate_limiter import RedisRateLimiter
from backend.core.redis_client import redis_client

logger = logging.getLogger('middleware.rate_limiter')

# In-memory fallback rate limiter
class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int, ban_threshold: int, ban_seconds: int):
        self.requests_per_minute = requests_per_minute
        self.ban_threshold = ban_threshold
        self.ban_seconds = ban_seconds
        self.request_counts = defaultdict(list)
        self.banned_ips = {}

    async def check_rate_limit(self, ip: str):
        now = time.time()
        
        # Check if banned
        if ip in self.banned_ips:
            ban_time, ban_until = self.banned_ips[ip]
            if now < ban_until:
                retry_after = int(ban_until - now)
                return False, {"reason": "ip_banned", "retry_after": retry_after}
            else:
                del self.banned_ips[ip]
        
        # Clean old requests
        self.request_counts[ip] = [t for t in self.request_counts[ip] if now - t < 60]
        
        # Add current request
        self.request_counts[ip].append(now)
        
        # Check if should ban
        if len(self.request_counts[ip]) > self.ban_threshold:
            self.banned_ips[ip] = (now, now + self.ban_seconds)
            return False, {"reason": "rate_limit_exceeded", "retry_after": self.ban_seconds}
        
        # Check rate limit
        if len(self.request_counts[ip]) > self.requests_per_minute:
            return False, {"reason": "rate_limited", "retry_after": 60}
        
        return True, {}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60, ban_threshold_per_minute: int = 150, ban_seconds: int = 3600):
        super().__init__(app)
        self.config = {
            'requests_per_minute': requests_per_minute,
            'ban_threshold': ban_threshold_per_minute,
            'ban_duration': ban_seconds
        }
        
        # Try to use Redis, fallback to in-memory
        self.redis_limiter = None
        self.memory_limiter = InMemoryRateLimiter(requests_per_minute, ban_threshold_per_minute, ban_seconds)
        self.using_redis = False

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "unknown"
        
        # Initialize Redis limiter on first request if available
        if self.redis_limiter is None and redis_client.redis:
            self.redis_limiter = RedisRateLimiter(redis_client, self.config)
            self.using_redis = True
            logger.info("Rate limiter using Redis backend")
        
        # Use Redis limiter if available, otherwise fallback to memory
        if self.using_redis and self.redis_limiter:
            allowed, info = await self.redis_limiter.check_rate_limit(client)
        else:
            allowed, info = await self.memory_limiter.check_rate_limit(client)
        
        if not allowed:
            return JSONResponse(
                {"detail": info.get("reason", "rate_limited"), "retry_after": info.get("retry_after", 60)},
                status_code=429
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers['X-RateLimit-Limit'] = str(self.config['requests_per_minute'])
        
        return response


# Global rate limiter instance for admin access
_global_limiter = None

def get_global_limiter():
    global _global_limiter
    if _global_limiter is None and redis_client.redis:
        _global_limiter = RedisRateLimiter(redis_client, {
            'requests_per_minute': 60,
            'ban_threshold': 150,
            'ban_duration': 3600
        })
    return _global_limiter


async def get_banned_ips():
    """Get list of banned IPs"""
    limiter = get_global_limiter()
    if limiter:
        return await limiter.get_banned_ips()
    return []


async def unban_ip(ip: str):
    """Unban an IP address"""
    limiter = get_global_limiter()
    if limiter:
        return await limiter.unban_ip(ip)
    return False