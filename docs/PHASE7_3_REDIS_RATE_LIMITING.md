# 🔴 Phase 7.3: Redis Rate Limiting Upgrade

## 📋 Overview
Replace the existing in-memory rate limiter with a Redis-backed distributed rate limiting system using atomic counters and TTL. This upgrade enables true distributed rate limiting across multiple backend instances, persistent ban lists, and improved performance.

---

## ⚠️ **CRITICAL BLOCKER**

### Redis Service Unavailable

**Current Status**: Redis client is implemented (`/app/backend/core/redis_client.py`) but the Redis service is not available in the environment. The application gracefully degrades, but Task 3 cannot be completed without a functional Redis instance.

**Evidence**:
- From `/app/test_result.md`:
  ```
  - task: "Phase 2 - Redis Client for Caching & Locking"
    implemented: true
    working: false
    file: "/app/backend/core/redis_client.py"
    status: "Redis service is not available in current environment"
  ```

**Resolution Required BEFORE Implementation**:

1. **Install Redis** in the environment:
   ```bash
   # Option 1: Via apt (if available)
   sudo apt-get update && sudo apt-get install redis-server
   
   # Option 2: Via docker (if docker available)
   docker run -d -p 6379:6379 redis:7-alpine
   ```

2. **Verify Redis is running**:
   ```bash
   redis-cli ping
   # Expected output: PONG
   ```

3. **Update .env file** with correct REDIS_URL:
   ```
   REDIS_URL=redis://localhost:6379
   ```

4. **Test connection** using existing client:
   ```bash
   python3 -c "import asyncio; from backend.core.redis_client import redis_client; asyncio.run(redis_client.connect())"
   # Should print: ✓ Redis connected: redis://localhost:6379
   ```

**Once Redis is operational, proceed with implementation below.**

---

## 🎯 Objectives

1. **Replace In-Memory Rate Limiter**: Migrate from in-memory to Redis-backed distributed rate limiter
2. **Atomic Operations**: Use Redis atomic counters for accurate rate limiting
3. **TTL-Based Expiration**: Automatically expire rate limit counters using Redis TTL
4. **Persistent Ban List**: Store IP bans in Redis for persistence across restarts
5. **Distributed Support**: Enable rate limiting across multiple backend instances
6. **Sliding Window**: Implement sliding window algorithm for accurate rate limiting
7. **Configurable Limits**: Support per-route rate limits with different thresholds
8. **Performance**: Minimize latency overhead (target: <5ms per request)

---

## 🏗️ Architecture Design

### **Current Implementation Analysis**

**Location**: `/app/backend/middleware/rate_limiter.py`

**Current Approach**:
```python
class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60, ban_threshold_per_minute: int = 150, ban_seconds: int = 3600):
        self.request_counts = defaultdict(list)  # ❌ In-memory only
        self.banned_ips = {}                     # ❌ Lost on restart
```

**Problems**:
1. **Not Distributed**: Each backend instance has its own counters
2. **Memory Leak Risk**: `defaultdict(list)` grows indefinitely
3. **Lost on Restart**: Ban list is not persisted
4. **Race Conditions**: Possible with multiple requests from same IP
5. **Inefficient**: Must iterate through timestamps to count requests

---

### **New Redis-Based Design**

#### **1. Rate Limiting Strategy**

**Algorithm**: Sliding Window Counter

**Why Sliding Window?**
- More accurate than fixed window
- Prevents burst at window boundaries
- Fair resource distribution
- Efficient with Redis

**How It Works**:
```
For each request from IP address:
1. Current timestamp (in seconds): ts = time.time()
2. Redis key: "rate_limit:{ip_address}"
3. Add current timestamp to sorted set: ZADD key ts ts
4. Remove old entries: ZREMRANGEBYSCORE key 0 (ts - 60)
5. Count entries in window: ZCARD key
6. If count > limit: Reject request
7. Set key TTL to 60 seconds (auto-cleanup)
```

**Redis Data Structure**:
```
Key: "rate_limit:{ip_address}"
Type: Sorted Set (ZSET)
Members: Request timestamps
Score: Same timestamp (for range operations)
TTL: 60 seconds
```

**Example**:
```
rate_limit:192.168.1.100 = {
    1705320600.123: 1705320600.123,
    1705320601.456: 1705320601.456,
    1705320602.789: 1705320602.789,
    ...
}
```

---

#### **2. Ban List Management**

**Strategy**: Redis Strings with TTL

**Data Structure**:
```
Key: "ban:{ip_address}"
Value: JSON object with ban details
TTL: Ban duration (e.g., 3600 seconds)

Example:
ban:192.168.1.100 = {
    "banned_at": 1705320600,
    "reason": "rate_limit_exceeded",
    "ban_until": 1705324200,
    "request_count": 150
}
TTL: 3600 seconds
```

**Benefits**:
- Automatic expiration via Redis TTL
- Persistent across restarts
- Fast lookup (O(1))
- Distributed across all backend instances

---

#### **3. New Rate Limiter Implementation**

**Location**: `/app/backend/core/redis_rate_limiter.py` (new file)

**Class Design**:

```
RedisRateLimiter class:
  
  __init__(redis_client, config):
    - Store Redis client reference
    - Load configuration (requests_per_minute, ban_threshold, ban_duration)
  
  async check_rate_limit(ip: str) -> tuple[bool, dict]:
    - Check if IP is banned (check ban:{ip})
    - If banned, return (False, {"reason": "banned", "retry_after": N})
    - Check rate limit using sliding window
    - If exceeded ban threshold, ban the IP
    - If exceeded rate limit, return (False, {"reason": "rate_limited", "retry_after": 60})
    - Return (True, {})
  
  async _check_ban(ip: str) -> tuple[bool, int]:
    - Redis GET ban:{ip}
    - If exists, parse JSON and return (True, retry_after)
    - Return (False, 0)
  
  async _check_sliding_window(ip: str, window_seconds: int, limit: int) -> int:
    - Redis key: rate_limit:{ip}
    - Current timestamp: now = time.time()
    - Redis pipeline:
        ZADD rate_limit:{ip} now now
        ZREMRANGEBYSCORE rate_limit:{ip} 0 (now - window_seconds)
        ZCARD rate_limit:{ip}
        EXPIRE rate_limit:{ip} window_seconds
    - Execute pipeline atomically
    - Return count from ZCARD
  
  async ban_ip(ip: str, duration: int, reason: str):
    - Create ban record JSON
    - Redis SET ban:{ip} json EX duration
    - Log ban event
  
  async unban_ip(ip: str) -> bool:
    - Redis DEL ban:{ip}
    - Log unban event
    - Return True if key existed
  
  async get_banned_ips() -> list[dict]:
    - Redis SCAN for ban:* keys
    - For each key, GET and parse JSON
    - Return list of ban records
  
  async get_rate_limit_status(ip: str) -> dict:
    - Check ban status
    - Check current request count in window
    - Return status dict with all info
```

---

#### **4. Configuration System**

**Location**: `/app/backend/config.py` (add settings)

**New Configuration Options**:
```
Environment Variables:
  RATE_LIMIT_ENABLED: bool (default: true)
  RATE_LIMIT_REQUESTS_PER_MINUTE: int (default: 60)
  RATE_LIMIT_BAN_THRESHOLD: int (default: 150)
  RATE_LIMIT_BAN_DURATION: int (default: 3600)
  RATE_LIMIT_USE_REDIS: bool (default: true if Redis available)
  RATE_LIMIT_FALLBACK_TO_MEMORY: bool (default: true)
```

**Per-Route Configuration** (optional future enhancement):
```python
# Example: Different limits for different endpoints
RATE_LIMITS = {
    "/api/auth/login": 5,  # 5 requests per minute
    "/api/payments/checkout": 10,
    "/api/messages/*": 100,  # Higher limit for real-time features
    "default": 60
}
```

---

#### **5. Updated Middleware**

**Location**: `/app/backend/middleware/rate_limiter.py` (major refactor)

**Changes**:
```
RateLimiterMiddleware class:
  
  __init__(app, redis_client, config):
    - Create RedisRateLimiter instance if Redis available
    - Fallback to in-memory limiter if Redis unavailable
    - Log which limiter is being used
  
  async dispatch(request, call_next):
    - Extract client IP
    - Call rate limiter (Redis or fallback)
    - If rate limited, return 429 response
    - If banned, return 429 with ban details
    - Otherwise, call next middleware
    - Add rate limit headers to response
  
  async _get_client_ip(request) -> str:
    - Check X-Forwarded-For header (if behind proxy)
    - Fallback to request.client.host
    - Handle missing client info
```

**Rate Limit Response Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705320660
Retry-After: 60  (if rate limited)
```

---

#### **6. Admin API for Ban Management**

**Location**: `/app/backend/routes/admin_security.py` (enhance existing)

**New Admin Endpoints**:

```
GET /api/admin/security/rate-limits
  - Get rate limit statistics
  - Show top offenders
  - Current ban list
  - Rate limit configuration

GET /api/admin/security/rate-limits/{ip}
  - Get rate limit status for specific IP
  - Request count in current window
  - Ban status
  - Historical data (if tracked)

POST /api/admin/security/ban-ip
  - Manually ban an IP address
  - Body: {ip, duration, reason}
  - Add to Redis ban list
  - Log admin action

DELETE /api/admin/security/ban-ip/{ip}
  - Unban an IP address
  - Remove from Redis
  - Log admin action

GET /api/admin/security/banned-ips
  - List all currently banned IPs
  - Include ban reasons and expiration
  - Pagination support
```

---

#### **7. Monitoring and Observability**

**Metrics to Track**:
- Total requests rate limited (per minute)
- Total IPs banned (per day)
- Average request count per IP
- Redis performance (latency, connection errors)
- Fallback activations (when Redis unavailable)

**Logging Events**:
```json
{
  "event": "rate_limit_exceeded",
  "ip": "192.168.1.100",
  "request_count": 75,
  "limit": 60,
  "window": "60s",
  "action": "rejected"
}

{
  "event": "ip_banned",
  "ip": "192.168.1.100",
  "request_count": 150,
  "ban_duration": 3600,
  "reason": "exceeded_ban_threshold"
}

{
  "event": "rate_limiter_fallback",
  "reason": "redis_unavailable",
  "fallback": "in_memory"
}
```

---

## 📄 Files to Create

### New Files (5 files):

1. `/app/backend/core/redis_rate_limiter.py` - Redis-backed rate limiter implementation
2. `/app/backend/tests/test_redis_rate_limiter.py` - Comprehensive rate limiter tests
3. `/app/backend/scripts/rate_limit_stats.py` - CLI tool for rate limit statistics
4. `/app/backend/scripts/test_redis_connection.py` - CLI tool to verify Redis is working

### Documentation:
5. `/app/docs/RATE_LIMITING_GUIDE.md` - Rate limiting documentation for operations

---

## 📝 Files to Modify

### Critical Modifications (10 files):

1. `/app/backend/core/redis_client.py`
   - Add helper methods for rate limiting operations
   - Add `zadd_with_ttl()` method
   - Add `get_ban()`, `set_ban()` methods
   - Improve error handling and reconnection logic

2. `/app/backend/middleware/rate_limiter.py`
   - **Major refactor**: Switch from in-memory to Redis
   - Integrate RedisRateLimiter
   - Implement fallback mechanism
   - Add rate limit headers to responses
   - Improve logging

3. `/app/backend/config.py`
   - Add rate limiting configuration variables
   - Add Redis fallback settings

4. `/app/backend/main.py`
   - Pass redis_client to RateLimiterMiddleware
   - Update middleware initialization
   - Add rate limiter startup validation
   - Log rate limiter configuration

5. `/app/backend/routes/admin_security.py`
   - Add new endpoints for ban management
   - Add rate limit statistics endpoint
   - Add manual ban/unban endpoints
   - Integrate with RedisRateLimiter

6. `/app/backend/.env`
   - Add RATE_LIMIT_* configuration variables
   - Document each variable

7. `/app/backend/tests/test_admin_security.py`
   - Add tests for new ban management endpoints

8. `/app/backend/README.md`
   - Document Redis requirement
   - Document rate limiting configuration
   - Add troubleshooting section for Redis

9. `/app/infra/k8s/` (if applicable)
   - Add Redis deployment configuration
   - Add Redis service definition
   - Update backend deployment to include Redis dependency

10. `/app/docker-compose.yml` (if exists)
    - Add Redis service definition for local development

---

## 🔄 Implementation Steps

### **Prerequisites** (REQUIRED):
1. ✅ Ensure Redis service is installed and running
2. ✅ Verify Redis connection using test script
3. ✅ Update .env with correct REDIS_URL

### **Phase 1: Redis Helper Methods** (Day 1)
1. Enhance `/app/backend/core/redis_client.py` with rate limiting methods
2. Add error handling and reconnection logic
3. Test Redis operations in isolation
4. Verify atomic operations work correctly

### **Phase 2: Rate Limiter Implementation** (Day 1-2)
1. Create `/app/backend/core/redis_rate_limiter.py`
2. Implement sliding window algorithm
3. Implement ban management
4. Add fallback mechanism for Redis unavailability
5. Unit test rate limiter logic

### **Phase 3: Middleware Integration** (Day 2)
1. Refactor `/app/backend/middleware/rate_limiter.py`
2. Integrate RedisRateLimiter
3. Add rate limit response headers
4. Implement graceful fallback
5. Test middleware integration

### **Phase 4: Admin API** (Day 2-3)
1. Add new endpoints to admin_security.py
2. Implement ban/unban functionality
3. Add rate limit statistics
4. Test admin endpoints

### **Phase 5: Testing and Validation** (Day 3)
1. Unit tests for RedisRateLimiter
2. Integration tests for middleware
3. Load testing (simulate high traffic)
4. Test Redis failure scenarios
5. Test ban persistence across restarts
6. Test distributed behavior (if multiple instances available)

### **Phase 6: Monitoring and Documentation** (Day 3-4)
1. Add comprehensive logging
2. Create monitoring dashboard queries
3. Write operational documentation
4. Update deployment docs with Redis requirement

---

## 🧪 Testing Strategy

### Unit Tests:

1. **Sliding Window Logic**:
   - Test request counting is accurate
   - Test old requests are removed
   - Test TTL is set correctly
   - Test window boundaries

2. **Ban Management**:
   - Test IP can be banned
   - Test IP can be unbanned
   - Test banned IPs are rejected
   - Test ban expiration works

3. **Fallback Mechanism**:
   - Test fallback to in-memory when Redis unavailable
   - Test recovery when Redis becomes available

### Integration Tests:

1. **End-to-End Rate Limiting**:
   - Send 60 requests, all should succeed
   - Send 61st request, should be rate limited
   - Wait 60 seconds, should reset
   - Send request, should succeed

2. **Ban Workflow**:
   - Send 150 requests rapidly
   - Verify IP gets banned
   - Verify ban persists across backend restart
   - Verify ban expires after duration

3. **Distributed Testing** (if multiple instances):
   - Start 2 backend instances
   - Send 30 requests to instance 1
   - Send 30 requests to instance 2
   - Verify total is counted correctly (60)
   - Send 1 more request, should be rate limited on both

### Load Tests:

1. **Performance**:
   - Measure rate limiter latency
   - Target: <5ms overhead per request
   - Test with 1000 concurrent connections

2. **Redis Performance**:
   - Monitor Redis CPU and memory usage
   - Verify Redis doesn't become bottleneck
   - Test Redis connection pool efficiency

3. **Failure Scenarios**:
   - Redis becomes unavailable mid-request
   - Redis is slow to respond
   - Redis connection drops

---

## 🔒 Security Considerations

### IP Spoofing Prevention:
- Trust X-Forwarded-For only if behind trusted proxy
- Validate X-Forwarded-For format
- Use rightmost IP in X-Forwarded-For chain
- Log suspicious X-Forwarded-For values

### Redis Security:
- Use Redis AUTH if Redis is network-accessible
- Use TLS for Redis connections in production
- Restrict Redis access to backend instances only
- Set Redis maxmemory policy (allkeys-lru recommended)

### Ban Evasion:
- Consider subnet bans for persistent abusers
- Track user_id in addition to IP (if authenticated)
- Implement fingerprinting for device tracking
- Log ban evasion attempts

---

## 📊 Success Criteria

1. ✅ Redis service is operational
2. ✅ In-memory rate limiter replaced with Redis-backed limiter
3. ✅ Sliding window algorithm implemented correctly
4. ✅ Ban list persists across backend restarts
5. ✅ Rate limiter works in distributed environment
6. ✅ Fallback to in-memory works when Redis unavailable
7. ✅ Admin can manually ban/unban IPs
8. ✅ Rate limit headers included in responses
9. ✅ Performance overhead <5ms per request
10. ✅ Comprehensive logging and monitoring in place
11. ✅ All tests passing (unit, integration, load)
12. ✅ Documentation complete

---

## ⚠️ Known Challenges

1. **Redis Dependency**: Application now depends on Redis for optimal rate limiting
   - **Mitigation**: Implement graceful fallback to in-memory limiter

2. **Redis Memory Usage**: Sorted sets can use significant memory with high traffic
   - **Mitigation**: Set appropriate TTLs, monitor memory usage, configure maxmemory policy

3. **Clock Synchronization**: Sliding window depends on accurate timestamps
   - **Mitigation**: Use NTP to synchronize clocks across instances

4. **IP Identification**: Accurate IP detection behind proxies/load balancers
   - **Mitigation**: Proper X-Forwarded-For handling, configuration validation

---

## 🔜 Future Enhancements

- Per-route rate limits (different limits for different endpoints)
- User-based rate limiting (in addition to IP-based)
- Dynamic rate limit adjustment based on load
- Whitelist for trusted IPs
- Rate limiting by API key
- Advanced analytics and visualization dashboard
- Integration with WAF (Web Application Firewall)
- Geolocation-based rate limits

---

## 📚 Dependencies

**Redis Installation** (if not present):
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install redis-server

# MacOS
brew install redis

# Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

**Python Packages** (already in requirements.txt):
```
redis==4.5.4  # Redis Python client (async support)
```

**No new Python packages required** - redis is already installed.

---

## 🕐 Estimated Implementation Time

**Prerequisite - Redis Setup**: 1-2 hours (if Redis not available)
- Install Redis: 30 minutes
- Configure Redis: 30 minutes
- Test connectivity: 30 minutes
- Update deployment configs: 30 minutes

**Implementation**:
- Redis helper methods: 2-3 hours
- Rate limiter implementation: 4-5 hours
- Middleware refactoring: 3-4 hours
- Admin API additions: 2-3 hours
- Testing (unit, integration, load): 4-5 hours
- Documentation: 2-3 hours

**Total: 17-23 hours of development time** (excluding Redis setup)

**With Redis setup: 18-25 hours total**

---

## 📋 Implementation Checklist

### Prerequisites:
- [ ] Redis service installed and running
- [ ] Redis connectivity verified
- [ ] .env updated with REDIS_URL
- [ ] Redis connection tested from backend

### Implementation:
- [ ] Enhance redis_client.py with rate limiting methods
- [ ] Create RedisRateLimiter class
- [ ] Implement sliding window algorithm
- [ ] Implement ban management
- [ ] Add fallback mechanism
- [ ] Refactor rate_limiter.py middleware
- [ ] Add rate limit response headers
- [ ] Create admin ban management endpoints
- [ ] Add rate limit statistics endpoint
- [ ] Update config.py with rate limiting settings
- [ ] Update main.py middleware initialization
- [ ] Create unit tests
- [ ] Create integration tests
- [ ] Perform load testing
- [ ] Test Redis failure scenarios
- [ ] Test ban persistence across restarts
- [ ] Add comprehensive logging
- [ ] Write operational documentation
- [ ] Update README with Redis requirement

---

**END OF DESIGN DOCUMENT**
