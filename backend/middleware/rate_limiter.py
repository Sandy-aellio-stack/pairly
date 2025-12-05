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
        
        # Check rate limit (simple in-memory check)
        if len(self.request_counts[client]) > self.requests_per_minute:
            retry_after = max(ttl, 0)
            return JSONResponse({"detail": "rate_limited", "retry_after": retry_after}, status_code=429)
        
        auth_header = request.headers.get("authorization")
        
        # Check rate limit (simple in-memory check)
        if len(self.request_counts[client]) > self.requests_per_minute:
            return JSONResponse({"detail": "rate_limited", "retry_after": 60}, status_code=429)
        
        response = await call_next(request)
        return response


async def get_banned_ips():
    """Get list of banned IPs"""
    # In-memory stub - would need Redis for persistence
    return []


async def unban_ip(ip: str):
    """Unban an IP address"""
    # In-memory stub
    return True