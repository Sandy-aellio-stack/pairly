# 🔴 Phase 7.2: Security Hardening - JWT, CORS, Secrets

## 📋 Overview
Comprehensive security hardening focused on strengthening JWT secret generation, restricting CORS to production domains, implementing secure environment variable handling, establishing secret rotation policies, and removing all weak security defaults.

---

## 🎯 Objectives

1. **Strong JWT Secret Generation**: Replace weak default JWT secrets with cryptographically secure secrets
2. **CORS Restriction**: Lock down CORS to only allow trusted production domains
3. **Secrets Management**: Implement secure environment variable handling with validation
4. **Secret Rotation**: Establish policies and mechanisms for rotating secrets
5. **Remove Weak Defaults**: Eliminate all hardcoded secrets and weak defaults
6. **Security Headers**: Add comprehensive security headers to all responses
7. **Token Security**: Enhance JWT token security with additional claims and validation

---

## 🏗️ Architecture Design

### **1. JWT Secret Hardening**

**Current Issues**:
```python
# /app/backend/config.py
JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-secret-key-in-production")
```

**Problems**:
- Weak default secret that could be used in production
- No validation of secret strength
- No mechanism for secret rotation
- Secret may be reused across environments

**Solution Design**:

#### a) Strong Secret Generation
Create utility for generating cryptographically secure secrets

**Location**: `/app/backend/utils/secret_generator.py`

**Features**:
- Generate secrets using `secrets` module (CSPRNG)
- Minimum length requirements (64 characters for JWT)
- Character set validation (alphanumeric + special chars)
- Secret strength checking
- CLI tool for generating secrets

**Secret Generation Function**:
```
generate_jwt_secret():
  - Use secrets.token_urlsafe(64) for 512-bit secret
  - Return base64-encoded random bytes
  - Ensure URL-safe characters only
  
validate_secret_strength(secret):
  - Check minimum length (64 chars)
  - Verify entropy (>= 256 bits)
  - Check character diversity
  - Reject common patterns
  - Return strength score (weak/medium/strong)
```

#### b) Secret Validation on Startup
**Location**: `/app/backend/core/security_validator.py`

**Purpose**: Validate all security-critical configuration on application startup

**Validation Checks**:
```
validate_jwt_secret():
  - Verify JWT_SECRET is set (not empty)
  - Reject default/weak secrets
  - Check minimum length (64 characters)
  - Verify not in common secrets list
  - Fail fast if invalid in production
  
validate_all_secrets():
  - Check JWT_SECRET
  - Check STRIPE_SECRET_KEY format
  - Check RAZORPAY_KEY_SECRET format
  - Check AWS credentials
  - Verify no secrets in code
```

#### c) Environment-Specific Secrets
**Location**: `/app/backend/.env` (enhanced validation)

**Strategy**:
- Development: Auto-generate secure secret if not provided
- Staging: Require unique secret, different from dev
- Production: Mandatory secret with high strength requirements
- Never commit .env files to git

---

### **2. CORS Security Hardening**

**Current Configuration** (in `/app/backend/main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ Too permissive!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Security Issues**:
- `allow_origins=["*"]` permits any domain to make requests
- Combined with `allow_credentials=True` is a security risk
- Allows CSRF attacks
- Enables data exfiltration from malicious sites

**Solution Design**:

#### a) Environment-Based CORS Configuration

**Location**: `/app/backend/config.py` (add settings)

**Configuration**:
```
Environment Variables:
  CORS_ORIGINS: Comma-separated list of allowed origins
  FRONTEND_URL: Primary frontend URL
  ENVIRONMENT: development, staging, production
  
Default Values by Environment:
  development:
    - http://localhost:3000
    - http://localhost:3001
    - http://127.0.0.1:3000
  
  staging:
    - https://staging.pairly.app
    - https://staging-admin.pairly.app
  
  production:
    - https://pairly.app
    - https://www.pairly.app
    - https://admin.pairly.app
```

#### b) CORS Middleware Configuration

**Location**: `/app/backend/middleware/cors_config.py` (new file)

**Features**:
- Load allowed origins from environment
- Validate origin format (must be https:// in production)
- Support wildcard subdomains for trusted domains (*.pairly.app)
- Reject unknown origins
- Log CORS rejections for monitoring

**Implementation Strategy**:
```
CORSConfig class:
  - get_allowed_origins() -> List[str]
    • Load from CORS_ORIGINS env var
    • Validate each origin
    • Add default frontend URL
    • Ensure HTTPS in production
  
  - validate_origin(origin: str) -> bool
    • Check against whitelist
    • Support subdomain wildcards
    • Log rejections
  
  - get_cors_middleware_config() -> dict
    • Return FastAPI CORS config
    • Set allow_origins to whitelist
    • Keep allow_credentials=True
    • Restrict methods if needed
    • Add exposed headers
```

#### c) Update Main Application

**Location**: `/app/backend/main.py`

**Changes**:
- Import CORSConfig
- Load allowed origins on startup
- Apply restrictive CORS settings
- Log CORS configuration (not origins in production)
- Add CORS error handling

---

### **3. Secrets Management System**

**Current Issues**:
- Secrets hardcoded in config.py with weak defaults
- No validation of secret format
- Secrets may be logged accidentally
- No distinction between required and optional secrets

**Solution Design**:

#### a) Secrets Manager

**Location**: `/app/backend/core/secrets_manager.py`

**Purpose**: Centralized secrets management with validation and security

**Features**:
```
SecretsManager class:
  - load_secrets()
    • Load from environment variables
    • Validate required secrets exist
    • Validate secret formats
    • Mask secrets in logs
    • Fail fast on missing required secrets
  
  - get_secret(key: str) -> str
    • Return secret value
    • Never log the value
    • Track access for auditing
  
  - validate_secret_format(key: str, value: str) -> bool
    • Validate Stripe key format (sk_live_, sk_test_)
    • Validate Razorpay format
    • Validate AWS credentials format
    • Check minimum lengths
  
  - is_production_ready() -> bool
    • Check all required secrets are set
    • Verify production-grade secrets
    • Return readiness status
```

#### b) Secret Categories

**Required Secrets** (Application won't start without these):
- `JWT_SECRET`: Minimum 64 characters, high entropy
- `MONGODB_URI`: Valid MongoDB connection string

**Payment Secrets** (Required if payments enabled):
- `STRIPE_SECRET_KEY`: Must match sk_live_* or sk_test_*
- `STRIPE_PUBLISHABLE_KEY`: Must match pk_live_* or pk_test_*
- `RAZORPAY_KEY_ID`: Must match rzp_live_* or rzp_test_*
- `RAZORPAY_KEY_SECRET`: Minimum 32 characters

**Storage Secrets** (Required if S3 enabled):
- `AWS_ACCESS_KEY_ID`: 20 characters
- `AWS_SECRET_ACCESS_KEY`: 40 characters
- `S3_BUCKET`: Valid bucket name
- `S3_REGION`: Valid AWS region

**Optional Secrets**:
- `REDIS_URL`: Redis connection string (graceful degradation)
- `SMTP_PASSWORD`: Email service password
- `SENTRY_DSN`: Error tracking (optional)

#### c) Secret Redaction Utility

**Location**: `/app/backend/utils/secret_redactor.py`

**Purpose**: Prevent secrets from appearing in logs or error messages

**Features**:
```
SecretRedactor class:
  - redact_secret(value: str) -> str
    • Return masked value: "***...last4chars"
    • Handle different secret types
    • Preserve enough for debugging
  
  - sanitize_dict(data: dict) -> dict
    • Recursively sanitize dictionary
    • Redact keys: password, secret, token, key, authorization
    • Return sanitized copy
  
  - is_secret_key(key: str) -> bool
    • Check if key name indicates secret
    • Patterns: *secret*, *password*, *token*, *key*
```

---

### **4. Secret Rotation Policy**

**Purpose**: Establish procedures and automation for rotating secrets

**Design**:

#### a) Rotation Schedule
- **JWT_SECRET**: Rotate every 90 days
- **Payment Secrets**: Rotate every 180 days or on compromise
- **Database Passwords**: Rotate every 180 days
- **API Keys**: Rotate every 90 days
- **AWS Credentials**: Rotate every 90 days

#### b) Rotation Mechanism

**Location**: `/app/backend/core/secret_rotation.py`

**Features**:
```
SecretRotation class:
  - supports_graceful_rotation(secret_type: str) -> bool
    • Check if secret can be rotated without downtime
    • JWT: Yes (with dual-secret validation period)
    • Payment: No (immediate cutover)
  
  - rotate_jwt_secret(new_secret: str):
    • Add new secret to validation list
    • Keep old secret valid for 24 hours
    • Allow both secrets to validate tokens
    • After 24h, remove old secret
  
  - validate_token_with_rotation(token: str):
    • Try validation with current secret
    • If fails, try previous secret (if in grace period)
    • Log rotation validation attempts
```

#### c) Rotation Tracking

**Location**: `/app/backend/models/secret_rotation_log.py`

**Purpose**: Track secret rotation history for audit

**Model**:
```
SecretRotationLog:
  - secret_type: str (e.g., "JWT_SECRET", "STRIPE_KEY")
  - rotated_at: datetime
  - rotated_by: str (user_id or "automated")
  - reason: str ("scheduled", "compromise", "manual")
  - old_secret_hash: str (SHA256 hash for identification)
  - new_secret_hash: str
  - rotation_id: str (unique identifier)
```

---

### **5. Security Headers**

**Purpose**: Add HTTP security headers to all responses

**Location**: `/app/backend/middleware/security_headers.py` (new file)

**Headers to Add**:
```
Security Headers:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security: max-age=31536000; includeSubDomains
  - Content-Security-Policy: default-src 'self'
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy: geolocation=(), microphone=(), camera=()
```

**Implementation**:
```
SecurityHeadersMiddleware:
  - async def dispatch(request, call_next):
    • Call next middleware
    • Add security headers to response
    • Return response
```

---

### **6. Enhanced JWT Token Security**

**Current Token Structure** (in `/app/backend/services/token_utils.py`):
```python
def create_access_token(user_id: str, role: str, rtid: str, minutes: int = 30):
    exp = datetime.utcnow() + timedelta(minutes=minutes)  # ❌ Uses deprecated utcnow
    jti = str(uuid4())
    payload = {
        "sub": user_id,
        "role": role,
        "rtid": rtid,
        "jti": jti,
        "iss": "pairly",
        "aud": "pairly-api",
        "token_type": "access",
        "exp": exp
    }
    return jwt.encode(payload, SECRET, algorithm=ALG)
```

**Issues**:
- Uses `datetime.utcnow()` instead of timezone-aware datetime
- Missing issued-at claim (iat)
- No not-before claim (nbf)
- Algorithm hardcoded (should be configurable)
- Missing token fingerprint for additional security

**Enhanced Token Design**:

#### a) Add Missing JWT Claims
```
Enhanced JWT Payload:
  - sub: user_id (existing)
  - role: user role (existing)
  - rtid: refresh token id (existing)
  - jti: unique token id (existing)
  - iss: "pairly" (existing)
  - aud: "pairly-api" (existing)
  - token_type: "access" or "refresh" (existing)
  - exp: expiration timestamp (existing, but fix timezone)
  - iat: issued at timestamp (NEW)
  - nbf: not before timestamp (NEW, same as iat)
  - fingerprint: SHA256 hash of user agent + IP (NEW, optional)
  - session_id: link to session record (NEW)
```

#### b) Token Validation Enhancements
```
Enhanced verify_token():
  - Verify signature with current secret
  - If fails and rotation active, try previous secret
  - Check expiration (exp)
  - Check not-before (nbf)
  - Check issued-at (iat) is not in future
  - Verify issuer (iss)
  - Verify audience (aud)
  - Check token type matches expected
  - Optional: Validate fingerprint matches request
  - Check if jti is revoked (JWT revocation list)
```

#### c) Token Security Features

**Location**: `/app/backend/core/token_security.py` (new file)

**Features**:
```
TokenSecurity class:
  - generate_token_fingerprint(user_agent: str, ip: str) -> str
    • Hash user agent + IP
    • Return SHA256 hash
    • Used to bind token to device
  
  - validate_token_fingerprint(token: dict, request: Request) -> bool
    • Extract fingerprint from token
    • Calculate current fingerprint
    • Compare hashes
    • Reject if mismatch
  
  - is_token_revoked(jti: str) -> bool
    • Check JWT revocation list (Redis or DB)
    • Return True if revoked
  
  - revoke_token(jti: str, reason: str):
    • Add token to revocation list
    • Set TTL to token expiration
    • Log revocation event
```

---

## 📄 Files to Create

### New Files (10 files):

1. `/app/backend/utils/secret_generator.py` - Secret generation utilities
2. `/app/backend/core/security_validator.py` - Security validation on startup
3. `/app/backend/core/secrets_manager.py` - Centralized secrets management
4. `/app/backend/utils/secret_redactor.py` - Redact secrets from logs
5. `/app/backend/core/secret_rotation.py` - Secret rotation mechanisms
6. `/app/backend/middleware/cors_config.py` - CORS configuration
7. `/app/backend/middleware/security_headers.py` - Security headers middleware
8. `/app/backend/core/token_security.py` - Enhanced token security
9. `/app/backend/models/secret_rotation_log.py` - Secret rotation tracking model
10. `/app/backend/tests/test_security_hardening.py` - Security tests

### Documentation:
11. `/app/docs/SECURITY_GUIDE.md` - Security best practices guide
12. `/app/docs/SECRET_ROTATION_GUIDE.md` - Secret rotation procedures

### CLI Tools:
13. `/app/backend/scripts/generate_secrets.py` - CLI for generating secrets
14. `/app/backend/scripts/rotate_secret.py` - CLI for secret rotation

---

## 📝 Files to Modify

### Critical Modifications (15 files):

1. `/app/backend/config.py`
   - Remove weak default for JWT_SECRET
   - Add CORS_ORIGINS configuration
   - Add ENVIRONMENT variable
   - Add secret validation flags
   - Integrate SecretsManager

2. `/app/backend/main.py`
   - Import security validators
   - Run security validation on startup
   - Update CORS middleware configuration
   - Add security headers middleware
   - Add startup security checks
   - Log security configuration (redacted)

3. `/app/backend/services/token_utils.py`
   - Fix `datetime.utcnow()` → `datetime.now(timezone.utc)`
   - Add iat and nbf claims
   - Add fingerprint generation (optional)
   - Add session_id to tokens
   - Implement dual-secret validation for rotation
   - Add token revocation check

4. `/app/backend/routes/auth.py`
   - Generate token fingerprints on login
   - Store session_id in tokens
   - Add security logging for auth events
   - Validate token fingerprints (if enabled)

5. `/app/backend/.env`
   - Add secure JWT_SECRET (must be generated)
   - Add CORS_ORIGINS
   - Add ENVIRONMENT variable
   - Remove or comment weak defaults
   - Add documentation comments

6. `/app/backend/.env.example` (create if not exists)
   - Provide template for all required secrets
   - Show format examples
   - Add comments explaining each variable
   - Never include actual secret values

7. `/app/backend/database.py`
   - Use SecretsManager for MONGODB_URI
   - Add connection validation
   - Redact connection string in logs

8. `/app/backend/core/redis_client.py`
   - Replace print statements
   - Use SecretsManager for REDIS_URL
   - Add connection security validation

9. `/app/backend/core/payment_clients.py`
   - Use SecretsManager for payment keys
   - Validate key formats
   - Redact keys in error messages
   - Add key validation on initialization

10. `/app/backend/utils/media.py`
    - Use SecretsManager for AWS credentials
    - Validate credentials format
    - Redact credentials in logs

11. `/app/backend/utils/jwt_revocation.py`
    - Enhance with token fingerprint validation
    - Add revocation reason tracking
    - Integrate with new token security

12. `/app/backend/middleware/rate_limiter.py`
    - Use SecretsManager (if needed)
    - Add security event logging

13. `/app/backend/routes/twofa.py`
    - Add security logging
    - Redact OTP codes in logs

14. `/app/README.md`
    - Update setup instructions
    - Add secret generation steps
    - Add security configuration guide

15. `/app/backend/requirements.txt`
    - Add: `cryptography==42.0.5` (for secret generation)
    - Ensure: `pyjwt[crypto]>=2.10.1` (for RSA support if needed)

---

## 🔄 Implementation Steps

### Phase 1: Secret Generation and Validation (Day 1)
1. Create secret_generator.py with CSPRNG-based generation
2. Create security_validator.py for startup validation
3. Create secrets_manager.py for centralized management
4. Create secret_redactor.py for log safety
5. Test secret generation and validation
6. Generate production-grade secrets for all environments

### Phase 2: JWT Security Hardening (Day 1-2)
1. Create token_security.py with enhanced features
2. Update token_utils.py with timezone-aware datetime
3. Add iat, nbf, fingerprint claims
4. Implement dual-secret validation for rotation
5. Add token revocation integration
6. Test token generation and validation thoroughly

### Phase 3: CORS Hardening (Day 2)
1. Create cors_config.py with environment-based configuration
2. Update config.py with CORS settings
3. Update main.py with restrictive CORS
4. Test CORS with allowed and rejected origins
5. Verify CORS works with frontend

### Phase 4: Security Headers (Day 2)
1. Create security_headers.py middleware
2. Add middleware to main.py
3. Test headers are present in responses
4. Verify headers don't break functionality

### Phase 5: Secret Rotation (Day 3)
1. Create secret_rotation.py with rotation logic
2. Create secret_rotation_log.py model
3. Create CLI tools for rotation
4. Implement JWT dual-secret validation
5. Test rotation process
6. Document rotation procedures

### Phase 6: Integration and Testing (Day 3-4)
1. Update all files to use SecretsManager
2. Remove all weak defaults
3. Test application startup with missing secrets
4. Test with valid secrets
5. Verify secrets are redacted in logs
6. Performance test
7. Security audit

### Phase 7: Documentation (Day 4)
1. Create SECURITY_GUIDE.md
2. Create SECRET_ROTATION_GUIDE.md
3. Update README.md
4. Create .env.example
5. Document all security features

---

## 🧪 Testing Strategy

### Security Tests:

1. **Weak Secret Detection**:
   - Test that weak JWT_SECRET is rejected in production
   - Test that default secrets are rejected
   - Test short secrets are rejected

2. **CORS Validation**:
   - Test allowed origins can make requests
   - Test disallowed origins are rejected
   - Test wildcard subdomain matching
   - Test HTTPS enforcement in production

3. **Secret Redaction**:
   - Test secrets are not in logs
   - Test error messages don't leak secrets
   - Test sanitize_dict works correctly

4. **JWT Security**:
   - Test timezone-aware datetime works
   - Test iat, nbf claims are validated
   - Test fingerprint validation works
   - Test token revocation works
   - Test dual-secret validation during rotation

5. **Secret Rotation**:
   - Test JWT rotation with grace period
   - Test old tokens still work during grace period
   - Test old tokens fail after grace period
   - Test rotation logging works

### Integration Tests:
- Full authentication flow with hardened tokens
- Payment flow with validated keys
- CORS with real frontend requests
- Secret rotation end-to-end

### Penetration Tests:
- CORS bypass attempts
- JWT manipulation attempts
- Weak secret brute force simulation
- Token replay attacks

---

## 🔒 Security Checklist

- [ ] JWT_SECRET is cryptographically secure (64+ chars)
- [ ] No weak defaults remain in code
- [ ] CORS restricted to production domains
- [ ] All secrets validated on startup
- [ ] Secrets never appear in logs
- [ ] Security headers added to all responses
- [ ] JWT tokens include iat, nbf claims
- [ ] JWT tokens use timezone-aware datetime
- [ ] Token fingerprinting implemented (optional)
- [ ] Token revocation working
- [ ] Secret rotation mechanism in place
- [ ] Secret rotation documented
- [ ] Payment keys validated for format
- [ ] AWS credentials validated
- [ ] MongoDB URI not logged
- [ ] .env.example created (no actual secrets)
- [ ] README updated with security setup
- [ ] Security tests passing
- [ ] Penetration tests passed

---

## ⚠️ Migration Notes

### For Existing Deployments:

1. **Generate New JWT Secret**:
   ```bash
   python backend/scripts/generate_secrets.py --type jwt
   ```

2. **Update .env File**:
   - Add new JWT_SECRET
   - Add CORS_ORIGINS
   - Add ENVIRONMENT=production

3. **Restart Application**:
   - Application will validate new secret
   - Old JWT tokens will become invalid
   - Users will need to log in again

4. **Alternative: Graceful Migration**:
   - Enable dual-secret validation
   - Add new secret as JWT_SECRET_NEW
   - Keep old secret as JWT_SECRET_OLD
   - After 24 hours, swap secrets
   - Remove old secret after all tokens expire

---

## 📊 Success Criteria

1. ✅ All weak defaults removed from codebase
2. ✅ JWT_SECRET is cryptographically secure
3. ✅ CORS restricted to whitelist only
4. ✅ Security validation passes on startup
5. ✅ Secrets never appear in logs or errors
6. ✅ Security headers present in all responses
7. ✅ JWT tokens use timezone-aware datetime
8. ✅ Token fingerprinting available (optional feature)
9. ✅ Secret rotation documented and tested
10. ✅ Security audit passes with no critical issues

---

## 🔜 Future Enhancements

- HSM (Hardware Security Module) integration for secret storage
- Vault integration (HashiCorp Vault, AWS Secrets Manager)
- Automated secret rotation on schedule
- Secret expiration warnings
- Multi-factor authentication for secret access
- Encrypted environment variables at rest

---

## 📚 Dependencies

**New Python Packages** (add to requirements.txt):
```
cryptography==42.0.5       # Secure secret generation and encryption
pyjwt[crypto]>=2.10.1     # JWT with cryptographic algorithms (already present)
```

**No breaking changes to API contracts**

---

## 🕐 Estimated Implementation Time

- Secret generation and validation: 3-4 hours
- JWT security hardening: 3-4 hours
- CORS hardening: 2-3 hours
- Security headers: 1-2 hours
- Secret rotation mechanism: 3-4 hours
- Testing and validation: 4-5 hours
- Documentation: 2-3 hours

**Total: 18-25 hours of development time**

---

**END OF DESIGN DOCUMENT**
