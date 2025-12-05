# Incident Response Template

## Overview
This document provides emergency procedures and quick reference commands for incident response on the Pairly platform.

## Emergency JWT Rotation

If JWT secrets are compromised or there's a security breach requiring token invalidation:

### Quick JWT Rotation Commands

```bash
# 1) Generate new secret and store in secret manager
export NEW_JWT_SECRET="$(openssl rand -base64 48)"

# 2) Push to secret manager / k8s secret
kubectl create secret generic pairly-secrets \
  --from-literal=jwt-secret="$NEW_JWT_SECRET" \
  --dry-run=client -o yaml | kubectl apply -f -

# 3) Restart backend deployment with rolling update
kubectl rollout restart deployment/pairly-backend

# 4) Monitor rollout status
kubectl rollout status deployment/pairly-backend

# 5) Verify new pods are running with new secret
kubectl get pods -l app=pairly-backend
```

### Emergency Token Revocation

If you need to revoke all active tokens immediately:

```bash
# Option 1: Flush all JWT revocation keys in Redis
kubectl exec -it deployment/redis -- redis-cli FLUSHDB

# Option 2: Implement global token epoch (requires code deployment)
# Add a global token_epoch check in the verify_token flow
# This allows immediate invalidation of all tokens issued before a specific time
```

## Incident Response Checklist

### 1. Security Breach Detection
- [ ] Identify the scope of the breach
- [ ] Check audit logs for unauthorized access
- [ ] Review Redis keys for suspicious patterns
- [ ] Check database access logs

### 2. Immediate Actions
- [ ] Rotate JWT secrets (see above)
- [ ] Review and revoke suspicious sessions
- [ ] Enable additional rate limiting if needed
- [ ] Alert security team

### 3. Investigation
- [ ] Review application logs: `kubectl logs -l app=pairly-backend --tail=1000`
- [ ] Check Redis for revoked tokens: `redis-cli KEYS "revoked_jwt:*"`
- [ ] Review audit events in MongoDB
- [ ] Check for failed login attempts

### 4. Recovery
- [ ] Restore from backup if data integrity is compromised
- [ ] Apply security patches
- [ ] Update firewall rules if needed
- [ ] Communicate with affected users

### 5. Post-Incident
- [ ] Document the incident
- [ ] Update security policies
- [ ] Conduct team retrospective
- [ ] Update monitoring alerts

## Key Monitoring Queries

### Check for Suspicious Activity

```bash
# High volume of failed logins
kubectl exec -it deployment/mongodb -- mongosh pairly --eval \
  'db.audit_logs.find({action: "login_failed"}).sort({timestamp: -1}).limit(100)'

# Recently revoked tokens
kubectl exec -it deployment/redis -- redis-cli KEYS "revoked_jwt:*" | wc -l

# Active sessions per user (detect session hijacking)
kubectl exec -it deployment/mongodb -- mongosh pairly --eval \
  'db.sessions.aggregate([{$match: {revoked: false}}, {$group: {_id: "$user_id", count: {$sum: 1}}}, {$sort: {count: -1}}])'
```

## Contact Information

- **Security Team Lead**: [email]
- **DevOps On-Call**: [phone/pagerduty]
- **Incident Slack Channel**: #security-incidents

## Related Documentation

- [RUNBOOK.md](./RUNBOOK.md) - Operational procedures
- [SECURITY.md](../docs/PHASE6_SECURITY.md) - Security architecture
- [HOW_TO_DEPLOY.md](./HOW_TO_DEPLOY.md) - Deployment procedures
