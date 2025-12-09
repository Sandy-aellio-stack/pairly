import logging
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from collections import OrderedDict

logger = logging.getLogger('payment.idempotency')


class IdempotencyService:
    """
    Idempotency service with Redis fallback to in-memory storage.
    
    Purpose: Prevent duplicate payment processing when requests are retried.
    Key Format: idempotency:{key_hash}
    TTL: 24 hours (configurable)
    """
    
    def __init__(self, redis_client=None, ttl_seconds: int = 86400):
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds
        
        # Fallback in-memory store (dict with expiry)
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._using_fallback = redis_client is None
        
        if self._using_fallback:
            logger.warning(
                "IdempotencyService: Redis not available, using in-memory fallback. "
                "This is NOT production-safe for distributed systems."
            )
    
    def generate_key(self, user_id: str, operation: str, params: dict) -> str:
        """
        Generate deterministic idempotency key from request parameters.
        
        Args:
            user_id: User performing the operation
            operation: Operation type (e.g., 'create_payment_intent')
            params: Request parameters (sorted for consistency)
        
        Returns:
            Hashed idempotency key
        """
        # Sort params to ensure consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        
        # Create key components
        key_components = f"{user_id}:{operation}:{sorted_params}"
        
        # Hash for fixed-length key
        key_hash = hashlib.sha256(key_components.encode()).hexdigest()[:32]
        
        return f"idempotency:{key_hash}"
    
    async def check_and_store(
        self,
        idempotency_key: str,
        result: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Check if operation was already processed.
        
        Args:
            idempotency_key: Unique key for this operation
            result: Result to store (if operation is being processed now)
        
        Returns:
            - None if operation is new (proceed with operation)
            - Stored result if operation was already processed (return cached result)
        """
        if self._using_fallback:
            return await self._check_and_store_memory(idempotency_key, result)
        else:
            return await self._check_and_store_redis(idempotency_key, result)
    
    async def _check_and_store_memory(self, key: str, result: Optional[Any]) -> Optional[Any]:
        """In-memory implementation (fallback)"""
        # Clean expired entries
        self._cleanup_expired()
        
        # Check if key exists
        if key in self._memory_store:
            stored_data = self._memory_store[key]
            
            # Check if expired
            if datetime.now(timezone.utc) < stored_data['expires_at']:
                logger.info(f"Idempotency hit (memory): {key}")
                return stored_data['result']
            else:
                # Expired, remove
                del self._memory_store[key]
        
        # Store new result if provided
        if result is not None:
            self._memory_store[key] = {
                'result': result,
                'expires_at': datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds),
                'created_at': datetime.now(timezone.utc)
            }
            logger.info(f"Idempotency stored (memory): {key}")
        
        return None
    
    async def _check_and_store_redis(self, key: str, result: Optional[Any]) -> Optional[Any]:
        """Redis implementation (production)"""
        try:
            # Check if key exists
            existing = await self.redis_client.get(key)
            
            if existing:
                logger.info(f"Idempotency hit (Redis): {key}")
                return json.loads(existing)
            
            # Store new result if provided
            if result is not None:
                await self.redis_client.setex(
                    key,
                    self.ttl_seconds,
                    json.dumps(result)
                )
                logger.info(f"Idempotency stored (Redis): {key}, TTL={self.ttl_seconds}s")
            
            return None
        
        except Exception as e:
            logger.error(f"Redis error in idempotency check: {e}. Falling back to allow operation.")
            # On Redis error, allow operation (fail open for availability)
            return None
    
    def _cleanup_expired(self):
        """Clean up expired entries in memory store"""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, data in self._memory_store.items()
            if now >= data['expires_at']
        ]
        
        for key in expired_keys:
            del self._memory_store[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired idempotency keys")
    
    async def invalidate(self, idempotency_key: str):
        """Manually invalidate an idempotency key (for testing/admin purposes)"""
        if self._using_fallback:
            if idempotency_key in self._memory_store:
                del self._memory_store[idempotency_key]
                logger.info(f"Invalidated idempotency key (memory): {idempotency_key}")
        else:
            try:
                await self.redis_client.delete(idempotency_key)
                logger.info(f"Invalidated idempotency key (Redis): {idempotency_key}")
            except Exception as e:
                logger.error(f"Error invalidating idempotency key: {e}")
    
    def get_stats(self) -> dict:
        """Get idempotency service statistics"""
        if self._using_fallback:
            self._cleanup_expired()
            return {
                "backend": "memory",
                "active_keys": len(self._memory_store),
                "ttl_seconds": self.ttl_seconds,
                "warning": "Using in-memory fallback - not production-safe"
            }
        else:
            return {
                "backend": "redis",
                "ttl_seconds": self.ttl_seconds,
                "production_safe": True
            }


# Global instance (initialized in main.py)
idempotency_service: Optional[IdempotencyService] = None


def get_idempotency_service() -> IdempotencyService:
    """Get global idempotency service instance"""
    global idempotency_service
    if idempotency_service is None:
        # Initialize with fallback mode
        idempotency_service = IdempotencyService(redis_client=None)
    return idempotency_service
