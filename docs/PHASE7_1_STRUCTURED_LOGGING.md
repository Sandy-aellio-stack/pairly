# 🔴 Phase 7.1: Structured Logging System

## 📋 Overview
Implementation design for a production-grade structured logging system across the entire Pairly backend. This system replaces all print statements, adds comprehensive request/response logging, error tracking, audit trails, and integrates structured logs into every service.

---

## 🎯 Objectives

1. **Replace all print statements** with structured logging
2. **Implement request/response logging** for all API endpoints
3. **Add error logging** with stack traces and context
4. **Create audit logging** for sensitive operations
5. **Integrate logging** into all services and middleware
6. **Support multiple output formats** (JSON for production, human-readable for development)
7. **Enable log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
8. **Add contextual information** (user_id, request_id, session_id, IP address)

---

## 🏗️ Architecture Design

### **1. Logging Configuration Module**

**Location**: `/app/backend/core/logging_config.py`

**Purpose**: Centralized logging configuration with support for:
- Structured JSON logging (production)
- Colored console logging (development)
- Log rotation policies
- Multiple output destinations (console, file, external services)
- Custom formatters for different log types

**Key Components**:
```
LoggingConfig class:
  - setup_logging()
    • Configure root logger
    • Set log level from environment
    • Add handlers (console, file, JSON)
    • Configure formatters
    • Set up log rotation
  
  - get_logger(name: str)
    • Return configured logger for module
    • Add contextual adapters
  
  - JSONFormatter class
    • Format logs as JSON
    • Include timestamp, level, message, context
    • Add request_id, user_id, trace_id
  
  - ColoredConsoleFormatter class
    • Human-readable format for development
    • Color-coded by log level
    • Include timestamps and module names
```

**Configuration via Environment Variables**:
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `LOG_FORMAT`: json, console (default: json in production)
- `LOG_FILE_PATH`: Path to log file (default: /var/log/pairly/app.log)
- `LOG_ROTATION_SIZE`: Max log file size before rotation (default: 100MB)
- `LOG_RETENTION_DAYS`: Days to keep old logs (default: 30)

---

### **2. Request Logging Middleware**

**Location**: `/app/backend/middleware/request_logger.py`

**Purpose**: Log all incoming HTTP requests and outgoing responses

**Features**:
- Log request method, path, headers, query params, body (sanitized)
- Log response status code, headers, body size
- Calculate and log request duration
- Add unique request_id to each request
- Sanitize sensitive data (passwords, tokens, credit cards)
- Log client IP, user agent
- Include authenticated user_id if available

**Log Structure**:
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "api.request",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "http_request",
  "method": "POST",
  "path": "/api/auth/login",
  "query_params": {},
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "user_id": null,
  "status_code": 200,
  "duration_ms": 145.23,
  "response_size_bytes": 1024
}
```

---

### **3. Error Logging**

**Location**: Integrated throughout the application

**Purpose**: Comprehensive error tracking with full context

**Features**:
- Automatic exception logging with stack traces
- Include request context in error logs
- Log user actions leading to errors
- Categorize errors by severity
- Include error codes for client communication
- Log external API failures (Stripe, Razorpay, S3)

**Error Log Structure**:
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "ERROR",
  "logger": "api.payments",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "exception",
  "error_type": "StripeAPIError",
  "error_message": "Card declined",
  "error_code": "card_declined",
  "stack_trace": "...",
  "user_id": "507f1f77bcf86cd799439011",
  "endpoint": "/api/payments/checkout",
  "additional_context": {
    "payment_amount": 2999,
    "payment_provider": "stripe"
  }
}
```

---

### **4. Audit Logging Enhancement**

**Location**: `/app/backend/services/audit.py` (enhanced)

**Purpose**: Structured audit logs for compliance and security

**Current State**: Basic audit logging exists but uses database only

**Enhancements**:
- Dual logging: Database + structured logs
- Include before/after state for data modifications
- Log all admin actions
- Track permission checks and authorization decisions
- Log security events (login, logout, 2FA, password changes)
- Include session and device fingerprint information

**Audit Log Structure**:
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "audit",
  "event": "user_suspended",
  "actor": {
    "user_id": "507f1f77bcf86cd799439011",
    "role": "admin",
    "ip_address": "192.168.1.100",
    "session_id": "abc123"
  },
  "target": {
    "user_id": "507f1f77bcf86cd799439012",
    "email": "user@example.com"
  },
  "action": "suspend_user",
  "reason": "Terms violation",
  "before_state": {"is_suspended": false},
  "after_state": {"is_suspended": true},
  "severity": "high"
}
```

---

### **5. Service-Level Logging**

**Purpose**: Add structured logging to all service modules

**Locations**:
- `/app/backend/services/token_utils.py`
- `/app/backend/services/twofa.py`
- `/app/backend/services/fingerprint.py`
- `/app/backend/services/risk.py`
- `/app/backend/services/credits_service.py`
- `/app/backend/services/presence.py`
- `/app/backend/services/ws_rate_limiter.py`
- `/app/backend/services/call_signaling.py`
- `/app/backend/services/matchmaking/`
- `/app/backend/workers/fraud_worker.py`

**Logging Events**:
- Service initialization
- Operation start/complete
- Errors and warnings
- Performance metrics
- External API calls
- Database operations

**Example - Token Service Logs**:
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "service.token",
  "event": "token_created",
  "user_id": "507f1f77bcf86cd799439011",
  "token_type": "access",
  "expires_at": "2025-01-15T11:00:45.123Z",
  "jti": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### **6. WebSocket Logging**

**Location**: `/app/backend/routes/messaging.py` (enhanced)

**Purpose**: Track WebSocket lifecycle and messages

**Logging Events**:
- Connection established
- Authentication success/failure
- Message sent/received
- Rate limit hits
- Credit transactions
- Connection closed
- Errors

**WebSocket Log Structure**:
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "websocket.messaging",
  "event": "ws_message_sent",
  "user_id": "507f1f77bcf86cd799439011",
  "recipient_id": "507f1f77bcf86cd799439012",
  "connection_id": "conn_abc123",
  "credits_charged": 5,
  "message_length": 128
}
```

---

### **7. Background Worker Logging**

**Location**: `/app/backend/workers/` (all workers)

**Purpose**: Track background job execution

**Logging Events**:
- Job started
- Job completed
- Job failed
- Retry attempts
- Processing metrics

---

### **8. Database Query Logging**

**Location**: `/app/backend/database.py` (enhanced)

**Purpose**: Optional query logging for debugging and performance monitoring

**Features**:
- Log slow queries (configurable threshold)
- Log query patterns
- Include execution time
- Track connection pool stats

---

## 📄 Files to Create

### New Files (9 files):
1. `/app/backend/core/logging_config.py` - Core logging configuration
2. `/app/backend/middleware/request_logger.py` - Request/response logging middleware
3. `/app/backend/utils/log_sanitizer.py` - Sanitize sensitive data from logs
4. `/app/backend/utils/request_context.py` - Request context management (request_id, user_id)
5. `/app/backend/tests/test_logging.py` - Logging system tests

### Documentation:
6. `/app/docs/LOGGING_GUIDE.md` - Developer guide for using the logging system
7. `/app/docs/LOG_ANALYSIS.md` - Guide for analyzing logs in production

---

## 📝 Files to Modify

### Critical Modifications (30+ files):

#### Core Application:
1. `/app/backend/main.py`
   - Import and initialize logging system
   - Add RequestLoggerMiddleware
   - Replace print statements with logger calls
   - Add startup/shutdown logging

2. `/app/backend/config.py`
   - Add logging configuration variables

3. `/app/backend/database.py`
   - Replace print statements with logger
   - Add database connection logging
   - Optional: Add query logging

#### Middleware:
4. `/app/backend/middleware/rate_limiter.py`
   - Replace print/no logging with structured logs
   - Log rate limit hits and bans

5. `/app/backend/middleware/content_moderation.py`
   - Add logging for moderation events

6. `/app/backend/middleware/failed_login.py`
   - Enhance with structured logging

#### Routes (15 files):
7. `/app/backend/routes/auth.py` - Log auth events
8. `/app/backend/routes/twofa.py` - Log 2FA events
9. `/app/backend/routes/profiles.py` - Log profile operations
10. `/app/backend/routes/discovery.py` - Log search operations
11. `/app/backend/routes/messaging.py` - Log WebSocket events
12. `/app/backend/routes/credits.py` - Log credit operations
13. `/app/backend/routes/payments.py` - Log payment events
14. `/app/backend/routes/payouts.py` - Log payout requests
15. `/app/backend/routes/media.py` - Log media uploads
16. `/app/backend/routes/posts.py` - Log post operations
17. `/app/backend/routes/feed.py` - Log feed operations
18. `/app/backend/routes/subscriptions.py` - Log subscription events
19. `/app/backend/routes/webhooks.py` - Log webhook processing
20. `/app/backend/routes/compliance.py` - Log compliance events
21. `/app/backend/routes/calls.py` - Log call events
22. `/app/backend/routes/matchmaking.py` - Log matchmaking operations

#### Admin Routes:
23. `/app/backend/admin/routes/admin_payouts.py` - Log admin actions
24. `/app/backend/routes/admin_security.py` - Log security actions
25. `/app/backend/routes/admin_analytics.py` - Log admin queries

#### Services (10+ files):
26. `/app/backend/services/token_utils.py` - Log token operations
27. `/app/backend/services/twofa.py` - Log 2FA operations
28. `/app/backend/services/fingerprint.py` - Log fingerprint analysis
29. `/app/backend/services/risk.py` - Log risk scoring
30. `/app/backend/services/audit.py` - Enhance with structured logging
31. `/app/backend/services/presence.py` - Log presence updates
32. `/app/backend/services/ws_rate_limiter.py` - Log rate limiting
33. `/app/backend/services/call_signaling.py` - Log signaling events
34. `/app/backend/services/credits_service.py` - Log credit operations
35. `/app/backend/services/matchmaking/` - All matchmaking services

#### Workers:
36. `/app/backend/workers/fraud_worker.py` - Log fraud detection

#### Core:
37. `/app/backend/core/redis_client.py` - Replace print with logger
38. `/app/backend/core/payment_clients.py` - Log payment API calls

---

## 🔄 Integration Steps

### Step 1: Core Logging Setup
1. Create `/app/backend/core/logging_config.py` with logging configuration
2. Create utility modules for sanitization and context management
3. Update `/app/backend/config.py` with logging environment variables
4. Test logging configuration in isolation

### Step 2: Middleware Integration
1. Create `/app/backend/middleware/request_logger.py`
2. Add middleware to `/app/backend/main.py`
3. Test request/response logging
4. Update existing middleware files with structured logging

### Step 3: Service Layer Integration
1. Update all service files to use structured logging
2. Replace print statements
3. Add operation logging
4. Add error logging with context

### Step 4: Route Layer Integration
1. Update all route files systematically
2. Add endpoint-specific logging
3. Log business operations
4. Log errors with full context

### Step 5: WebSocket and Background Jobs
1. Enhance WebSocket logging in messaging
2. Update worker logging
3. Add connection lifecycle logging

### Step 6: Database and External APIs
1. Add database operation logging
2. Log external API calls (Stripe, Razorpay, S3)
3. Track latencies and errors

### Step 7: Testing and Validation
1. Create comprehensive tests for logging system
2. Verify log output format
3. Test log rotation
4. Verify sensitive data sanitization
5. Load test logging overhead

---

## 🧪 Testing Strategy

### Unit Tests:
- Test log formatting (JSON, console)
- Test sanitization of sensitive data
- Test request_id propagation
- Test log level filtering

### Integration Tests:
- Test end-to-end request logging
- Verify logs for each API endpoint
- Test error logging with exceptions
- Verify audit logs are created

### Performance Tests:
- Measure logging overhead (<5% target)
- Test log rotation under load
- Verify no memory leaks

---

## 🔒 Security Considerations

### Data Sanitization:
- **Always sanitize**: passwords, tokens, API keys, credit card numbers, SSN
- **Conditional sanitization**: emails, IP addresses (based on privacy policy)
- **Never log**: Full credit card numbers, CVV, plaintext passwords

### Log Access Control:
- Restrict log file permissions (640, owned by app user)
- Encrypt logs at rest (production)
- Secure log transmission (TLS for external logging services)
- Implement log access auditing

---

## 📊 Monitoring and Observability

### Log Aggregation:
- **Development**: Local files + console
- **Production**: Consider integration with:
  - ELK Stack (Elasticsearch, Logstash, Kibana)
  - Datadog
  - Splunk
  - CloudWatch (AWS)
  - Loki + Grafana

### Alerts:
- High error rate (>1% of requests)
- Slow response times (>2s)
- Authentication failures spike
- Payment failures
- WebSocket connection drops

---

## 🎯 Success Criteria

1. ✅ Zero print statements remaining in codebase
2. ✅ All HTTP requests/responses logged
3. ✅ All errors logged with full context
4. ✅ All admin actions logged
5. ✅ Sensitive data properly sanitized
6. ✅ Log format is structured (JSON)
7. ✅ Request_id tracked throughout request lifecycle
8. ✅ Performance overhead <5%
9. ✅ Log rotation working correctly
10. ✅ Documentation complete

---

## ⚠️ Known Challenges

1. **Performance**: Logging can add latency; use async logging where possible
2. **Log Volume**: High-traffic endpoints will generate large log volumes; implement sampling for verbose endpoints
3. **Sensitive Data**: Requires careful sanitization to avoid logging PII/PCI data
4. **Backward Compatibility**: Some services may break if logging initialization fails; implement graceful degradation

---

## 🔜 Future Enhancements

- Distributed tracing integration (OpenTelemetry)
- Real-time log streaming to external services
- Log-based metrics and dashboards
- Automated log analysis and anomaly detection
- Cost optimization for log storage

---

## 📚 Dependencies

**New Python Packages** (add to requirements.txt):
```
python-json-logger==2.0.7     # Structured JSON logging
colorlog==6.8.2                # Colored console logs (dev)
python-logging-loki==0.3.1    # Optional: Loki integration
```

**No breaking changes to existing functionality**

---

## 🕐 Estimated Implementation Time

- Core logging setup: 2-3 hours
- Middleware integration: 1-2 hours
- Service layer updates: 3-4 hours
- Route layer updates: 4-6 hours
- Testing and validation: 2-3 hours
- Documentation: 1-2 hours

**Total: 13-20 hours of development time**

---

## 📋 Checklist for Implementation

- [ ] Create core logging configuration module
- [ ] Create request logger middleware
- [ ] Create utility modules (sanitizer, context)
- [ ] Update config.py with logging settings
- [ ] Replace all print statements in core files
- [ ] Update all route files with structured logging
- [ ] Update all service files with structured logging
- [ ] Update all middleware files
- [ ] Update worker files
- [ ] Enhance WebSocket logging
- [ ] Add database query logging (optional)
- [ ] Create unit tests
- [ ] Create integration tests
- [ ] Write developer documentation
- [ ] Write log analysis guide
- [ ] Validate log sanitization
- [ ] Performance test
- [ ] Update main.py startup sequence

---

**END OF DESIGN DOCUMENT**
