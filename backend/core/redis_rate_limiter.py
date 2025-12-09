import time
import json
import logging
from typing import Tuple, Dict, Optional, List
from backend.core.redis_client import RedisClient

logger = logging.getLogger('core.rate_limiter')


class RedisRateLimiter:
    """Redis-backed distributed rate limiter using sliding window"""
    
    def __init__(self, redis_client: RedisClient, config: Dict):
        self.redis = redis_client
        self.requests_per_minute = config.get('requests_per_minute', 60)
        self.ban_threshold = config.get('ban_threshold', 150)
        self.ban_duration = config.get('ban_duration', 3600)
    
    async def check_rate_limit(self, ip: str) -> Tuple[bool, Dict]:
        """Check if IP is rate limited or banned"""
        # Check if banned first
        is_banned, retry_after = await self._check_ban(ip)
        if is_banned:
            logger.warning(
                "IP is banned",
                extra={"event": "ip_banned_check", "ip": ip, "retry_after": retry_after}
            )
            return False, {"reason": "ip_banned", "retry_after": retry_after}
        
        # Check sliding window rate limit
        request_count = await self._check_sliding_window(ip, 60, self.requests_per_minute)
        
        # Check if should ban
        if request_count > self.ban_threshold:
            await self.ban_ip(ip, self.ban_duration, "rate_limit_exceeded")
            logger.warning(
                "IP banned due to excessive requests",
                extra={
                    "event": "ip_banned",
                    "ip": ip,
                    "request_count": request_count,
                    "threshold": self.ban_threshold
                }
            )
            return False, {"reason": "rate_limit_exceeded", "retry_after": self.ban_duration}
        
        # Check if rate limited
        if request_count > self.requests_per_minute:
            logger.info(
                "IP rate limited",
                extra={
                    "event": "rate_limit_exceeded",
                    "ip": ip,
                    "request_count": request_count,
                    "limit": self.requests_per_minute
                }
            )
            return False, {"reason": "rate_limited", "retry_after": 60}
        
        return True, {}
    
    async def _check_ban(self, ip: str) -> Tuple[bool, int]:
        """Check if IP is banned"""
        if not self.redis.redis:
            return False, 0
        
        try:
            ban_key = f"ban:{ip}"
            ban_data = await self.redis.redis.get(ban_key)
            
            if ban_data:
                ban_info = json.loads(ban_data)
                ban_until = ban_info.get('ban_until', 0)
                retry_after = max(0, int(ban_until - time.time()))
                return True, retry_after
            
            return False, 0
        except Exception as e:
            logger.error(f"Error checking ban: {e}")
            return False, 0
    
    async def _check_sliding_window(self, ip: str, window_seconds: int, limit: int) -> int:
        """Check sliding window rate limit"""
        if not self.redis.redis:
            return 0
        
        try:
            key = f"rate_limit:{ip}"
            now = time.time()
            window_start = now - window_seconds
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis.redis.pipeline()
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in window
            pipe.zcard(key)
            
            # Set expiry
            pipe.expire(key, window_seconds)
            
            # Execute pipeline
            results = await pipe.execute()
            
            # Return count (third result)
            return results[2] if len(results) > 2 else 0
            
        except Exception as e:
            logger.error(f"Error in sliding window check: {e}")
            return 0
    
    async def ban_ip(self, ip: str, duration: int, reason: str):
        """Ban an IP address"""
        if not self.redis.redis:
            return
        
        try:
            ban_key = f"ban:{ip}"
            ban_data = {
                "banned_at": time.time(),
                "ban_until": time.time() + duration,
                "reason": reason
            }
            
            await self.redis.redis.setex(
                ban_key,
                duration,
                json.dumps(ban_data)
            )
            
            logger.warning(
                "IP banned",
                extra={
                    "event": "ip_banned",
                    "ip": ip,
                    "duration": duration,
                    "reason": reason
                }
            )
        except Exception as e:
            logger.error(f"Error banning IP: {e}")
    
    async def unban_ip(self, ip: str) -> bool:
        """Unban an IP address"""
        if not self.redis.redis:
            return False
        
        try:
            ban_key = f"ban:{ip}"
            result = await self.redis.redis.delete(ban_key)
            
            logger.info(
                "IP unbanned",
                extra={"event": "ip_unbanned", "ip": ip}
            )
            
            return result > 0
        except Exception as e:
            logger.error(f"Error unbanning IP: {e}")
            return False
    
    async def get_banned_ips(self) -> List[Dict]:
        """Get list of all banned IPs"""
        if not self.redis.redis:
            return []
        
        try:
            banned_ips = []
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.redis.scan(
                    cursor=cursor,
                    match="ban:*",
                    count=100
                )
                
                for key in keys:
                    ban_data = await self.redis.redis.get(key)
                    if ban_data:
                        ip = key.replace('ban:', '')
                        ban_info = json.loads(ban_data)
                        ban_info['ip'] = ip
                        banned_ips.append(ban_info)
                
                if cursor == 0:
                    break
            
            return banned_ips
        except Exception as e:
            logger.error(f"Error getting banned IPs: {e}")
            return []
    
    async def get_rate_limit_status(self, ip: str) -> Dict:
        """Get rate limit status for an IP"""
        is_banned, retry_after = await self._check_ban(ip)
        request_count = await self._check_sliding_window(ip, 60, self.requests_per_minute)
        
        return {
            "ip": ip,
            "is_banned": is_banned,
            "retry_after": retry_after if is_banned else 0,
            "request_count": request_count,
            "limit": self.requests_per_minute,
            "remaining": max(0, self.requests_per_minute - request_count)
        }
