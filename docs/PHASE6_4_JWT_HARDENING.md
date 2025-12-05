# Phase 6.4: JWT Revocation & Security Hardening

## Overview
This phase implements Redis-backed JWT revocation, refresh token JTI validation, hardened encryption key loading, and CI/CD security gates to enhance the security posture of the Pairly platform.

## Features Implemented

### 1. JWT Revocation System
**Files:** `backend/utils/jwt_revocation.py`

- Redis-backed token revocation with JTI (JWT ID) tracking
- Graceful degradation when Redis is unavailable
- Efficient revocation with TTL-based expiration
- Support for individual token revocation and bulk user revocation

**Key Functions:**
- `revoke_token(jti, ttl_seconds)` - Revoke a specific token
- `is_token_revoked(jti)` - Check if a token is revoked
- `revoke_all_for_user(user_id)` - Revoke all tokens for a user

### 2. Refresh Token JTI Store
**Files:** `backend/utils/refresh_store.py`

- Per-user refresh token JTI tracking
- Prevents refresh token reuse attacks
- Validates refresh tokens against stored JTI
- Automatic fallback to permissive mode when Redis unavailable

**Key Functions:**
- `set_user_refresh_jti(user_id, jti, ttl_days)` - Store refresh JTI
- `validate_user_refresh_jti(user_id, jti)` - Validate refresh JTI

### 3. Enhanced Token Claims
**Files:** `backend/services/token_utils.py`

All tokens now include:
- `jti` - Unique JWT ID for revocation tracking
- `iss` - Issuer claim ("pairly")
- `aud` - Audience claim ("pairly-api")
- `token_type` - Type of token (access/refresh)
- `exp` - Expiration timestamp

### 4. Hardened Encryption Key Loading
**Files:** `backend/utils/encryption.py`

- Fails fast in production if `ENCRYPTION_KEY` is not set
- Development fallback with explicit warning
- Automatic key normalization and Fernet cipher setup
- Hash-based fallback for invalid key formats

### 5. Updated Authentication Flow
**Files:** `backend/routes/auth.py`

**Signup/Login/2FA:**
- Generate tokens with JTI
- Store refresh token JTI in Redis
- Track session and audit events

**Refresh:**
- Validate refresh JTI before issuing new tokens
- Rotate refresh token on each refresh
- Store new refresh JTI

**Logout:**
- Revoke access token JTI
- Mark session as revoked
- Log revocation event

**Token Validation (get_current_user):**
- Check JTI revocation before accepting token
- Validate issuer and audience claims

### 6. CI/CD Security Gates
**Files:** `.github/workflows/ci.yml`

Added two new jobs:

**security-scan** (non-blocking):
- Runs Semgrep for SAST
- Runs Bandit for Python security issues
- Runs pip-audit for dependency vulnerabilities

**security-block** (blocking):
- Blocks deployment on critical security findings
- Validates JWT_SECRET configuration
- Ensures security tools pass before build

### 7. Incident Response Procedures
**Files:** `infra/docs/INCIDENT_RESPONSE_TEMPLATE.md`

Comprehensive incident response guide including:
- Emergency JWT rotation procedures
- Token revocation strategies
- Incident response checklist
- Key monitoring queries
- Recovery procedures

## Security Improvements

1. **Token Revocation**: Administrators can now revoke tokens immediately upon security incidents
2. **Refresh Token Security**: Prevents token reuse and replay attacks
3. **Token Tracking**: All tokens have unique identifiers for audit trails
4. **Production Safety**: System fails fast if critical security config is missing
5. **Automated Security Scanning**: CI/CD pipeline catches vulnerabilities before deployment

## Testing Results

### Security Scans Performed

**Semgrep (SAST):**
- Scanned 55 files with 1063 rules
- Found 1 finding (CORS wildcard - expected for development)
- ✅ No blocking security issues

**Bandit (Python Security):**
- Scanned 4457 lines of code
- ✅ No high-severity issues identified
- 41 low-severity issues (informational)

**pip-audit (Dependency Vulnerabilities):**
- Found 7 known vulnerabilities in 5 packages:
  - ecdsa 0.19.1
  - mcp 1.16.0 → 1.23.0
  - pymongo 4.5.0 → 4.6.3
  - starlette 0.37.2 → 0.40.0, 0.47.2
  - urllib3 2.5.0 → 2.6.0

**Recommendation:** Upgrade dependencies to fix vulnerabilities

### Functional Testing

**✅ JWT Claims:**
- Tokens include JTI, iss, and aud
- Token type correctly set

**✅ Signup Flow:**
- Creates tokens with proper claims
- Stores refresh JTI (when Redis available)

**✅ Refresh Flow:**
- Validates refresh JTI
- Issues new tokens with rotation
- Stores new refresh JTI

**✅ Logout Flow:**
- Revokes access token
- Marks session as revoked
- Logs audit event

**⚠️ Degraded Mode:**
- System works without Redis
- Token revocation not enforced (by design)
- Warning messages logged

## Configuration

### Environment Variables

**Required in Production:**
- `ENCRYPTION_KEY` - Must be set (32+ bytes recommended)
- `JWT_SECRET` - Must be set (32+ characters recommended)
- `REDIS_URL` - Required for token revocation (optional for basic functionality)

**Development:**
- System auto-generates encryption key with warning
- Redis connection failures are gracefully handled

### Redis Keys Used

- `revoked_jwt:{jti}` - Revoked access token (TTL: access token lifetime)
- `user_refresh:{user_id}` - Current valid refresh JTI (TTL: 7 days)
- `user_tokens:{user_id}:*` - Pattern for bulk user revocation

## Emergency Procedures

### Rotate JWT Secret

```bash
# Generate new secret
export NEW_JWT_SECRET="$(openssl rand -base64 48)"

# Update Kubernetes secret
kubectl create secret generic pairly-secrets \
  --from-literal=jwt-secret="$NEW_JWT_SECRET" \
  --dry-run=client -o yaml | kubectl apply -f -

# Rolling restart
kubectl rollout restart deployment/pairly-backend
```

### Revoke All Tokens

```bash
# Option 1: Flush Redis revocation DB
kubectl exec -it deployment/redis -- redis-cli FLUSHDB

# Option 2: Rotate JWT secret (see above)
```

## Next Steps

1. **Dependency Updates**: Upgrade vulnerable dependencies
2. **Redis Setup**: Configure Redis in production for full revocation support
3. **Monitoring**: Set up alerts for revocation patterns
4. **Admin UI**: Build admin panel for token management
5. **Audit Reports**: Generate security audit reports from logs

## Files Modified/Created

**Created:**
- `backend/utils/jwt_revocation.py`
- `backend/utils/refresh_store.py`
- `backend/utils/encryption.py`
- `infra/docs/INCIDENT_RESPONSE_TEMPLATE.md`
- `docs/PHASE6_4_JWT_HARDENING.md`

**Modified:**
- `backend/services/token_utils.py` - Added JTI, iss, aud claims
- `backend/routes/auth.py` - Integrated revocation and refresh validation
- `.github/workflows/ci.yml` - Added security scan and security-block jobs

## Known Limitations

1. **Redis Dependency**: Token revocation requires Redis. System degrades gracefully without it.
2. **No Global Revocation**: Currently no "revoke all tokens before timestamp" mechanism (can be added via token epoch)
3. **Test Coverage**: Unit tests need Redis mock for comprehensive coverage

## References

- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP JWT Security](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Redis Key Expiration](https://redis.io/commands/expire)
