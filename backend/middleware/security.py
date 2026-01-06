from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import os
import time
from typing import Callable

logger = logging.getLogger("security")

FRONTEND_URL = os.getenv("FRONTEND_URL", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing (production-safe)"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        if response.status_code >= 400:
            logger.warning("Request failed", extra=log_data)
        else:
            logger.debug("Request completed", extra=log_data)
        
        response.headers["X-Process-Time"] = str(process_time)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting for sensitive endpoints"""
    
    RATE_LIMITS = {
        "/api/auth/login": (5, 60),
        "/api/auth/signup": (3, 60),
        "/api/auth/otp/send": (3, 3600),
        "/api/auth/otp/verify": (5, 300),
        "/api/payments/order": (10, 60),
        "/api/messages/send": (30, 60),
    }
    
    async def dispatch(self, request: Request, call_next: Callable):
        from backend.core.redis_client import redis_client
        
        path = request.url.path
        
        for endpoint, (max_requests, window) in self.RATE_LIMITS.items():
            if path.startswith(endpoint):
                client_ip = request.client.host if request.client else "unknown"
                key = f"{endpoint}:{client_ip}"
                
                allowed, count, remaining = await redis_client.rate_limit_check(
                    key, max_requests, window
                )
                
                if not allowed:
                    logger.warning(f"Rate limit exceeded: {key}", extra={
                        "path": path,
                        "client_ip": client_ip,
                        "count": count
                    })
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Too many requests",
                            "retry_after": remaining
                        },
                        headers={"Retry-After": str(remaining)}
                    )
                break
        
        return await call_next(request)


async def production_error_handler(request: Request, exc: Exception):
    """Centralized error handler - no stack traces in production"""
    if ENVIRONMENT == "production":
        logger.error(f"Unhandled exception: {type(exc).__name__}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred"}
        )
    else:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
