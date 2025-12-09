# PHASE 8 INFRASTRUCTURE PRE-CHECKS

**Status:** Validation Required Before Implementation  
**Date:** December 9, 2025  
**Critical:** All items must be ✅ before proceeding with Phase 8

---

## CRITICAL BLOCKER CHECKLIST

### 1. Redis Production Readiness ⚠️

**Status:** PARTIAL - Redis client exists but service availability uncertain

**Requirements:**
- [ ] Redis service running and accessible
- [ ] Minimum 2GB RAM allocated
- [ ] Persistence enabled (AOF or RDB)
- [ ] Max memory policy: allkeys-lru
- [ ] Replication configured (master-replica)
- [ ] Monitoring and alerts configured

**Current State:**
```bash
# Check Redis status
Redis Client: Implemented (/app/backend/core/redis_client.py)
Service Status: Unknown (graceful degradation active)
Connection String: REDIS_URL in .env
```

**Verification Commands:**
```bash
# 1. Check Redis is running
redis-cli ping
# Expected: PONG

# 2. Check memory configuration
redis-cli CONFIG GET maxmemory
redis-cli CONFIG GET maxmemory-policy

# 3. Check persistence
redis-cli CONFIG GET save
redis-cli CONFIG GET appendonly

# 4. Test connectivity from backend
python3 -c "import asyncio; from backend.core.redis_client import redis_client; asyncio.run(redis_client.connect())"
```

**Action Items:**
1. Install/configure production Redis instance
2. Set maxmemory to 2GB minimum
3. Enable AOF persistence: `appendonly yes`
4. Set maxmemory-policy: `allkeys-lru`
5. Configure monitoring (memory usage, connection count, ops/sec)

**Deployment Options:**
```yaml
# Option A: Docker Compose (Development)
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

# Option B: Kubernetes (Production)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 2
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        args:
          - --appendonly yes
          - --maxmemory 2gb
          - --maxmemory-policy allkeys-lru
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

---

### 2. Celery / Worker Infrastructure ⚠️

**Status:** NOT IMPLEMENTED - No Celery infrastructure detected

**Requirements:**
- [ ] Celery broker (Redis or RabbitMQ)
- [ ] Celery result backend configured
- [ ] Worker deployment (k8s or supervisor)
- [ ] Beat scheduler for periodic tasks
- [ ] Monitoring (Flower or Prometheus)
- [ ] Auto-scaling configured

**Current State:**
```
Celery: Not installed
Worker Process: Not configured
Scheduled Tasks: Not implemented
```

**Action Items:**

1. **Install Celery:**
```bash
cd /app/backend
pip install celery[redis]==5.3.4
pip freeze > requirements.txt
```

2. **Create Celery Configuration:**
```python
# File: /app/backend/celery_app.py
from celery import Celery
from backend.config import settings

celery_app = Celery(
    'pairly',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000
)

# Autodiscover tasks
celery_app.autodiscover_tasks(['backend.workers'])
```

3. **Worker Deployment (Kubernetes):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: worker
        image: pairly-backend:latest
        command: ["celery", "-A", "backend.celery_app", "worker", "--loglevel=info"]
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis:6379/0"
        - name: CELERY_RESULT_BACKEND
          value: "redis://redis:6379/1"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
spec:
  replicas: 1
  selector:
    matchLabels:
      app: celery-beat
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
      - name: beat
        image: pairly-backend:latest
        command: ["celery", "-A", "backend.celery_app", "beat", "--loglevel=info"]
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis:6379/0"
```

4. **Supervisor Configuration (Development):**
```ini
# File: /etc/supervisor/conf.d/celery.conf
[program:celery_worker]
command=/usr/local/bin/celery -A backend.celery_app worker --loglevel=info
directory=/app
user=root
numprocs=1
stdout_logfile=/var/log/supervisor/celery_worker.log
stderr_logfile=/var/log/supervisor/celery_worker.err.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
priority=998

[program:celery_beat]
command=/usr/local/bin/celery -A backend.celery_app beat --loglevel=info
directory=/app
user=root
numprocs=1
stdout_logfile=/var/log/supervisor/celery_beat.log
stderr_logfile=/var/log/supervisor/celery_beat.err.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
priority=999
```

**Environment Variables Required:**
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

---

### 3. Secrets Management ⚠️

**Status:** PARTIAL - SecretsManager exists but payment keys not configured

**Requirements:**
- [ ] Stripe API keys (secret + publishable)
- [ ] Stripe webhook signing secret
- [ ] Razorpay API keys (key_id + key_secret)
- [ ] Razorpay webhook secret
- [ ] All keys stored in secure secrets manager
- [ ] Key rotation policy documented
- [ ] No keys committed to repository

**Current State:**
```python
# Existing: /app/backend/core/secrets_manager.py
SecretsManager: Implemented ✅
JWT_SECRET: Configured ✅
MONGODB_URI: Configured ✅
Payment Keys: NOT CONFIGURED ❌
```

**Required Secrets:**

1. **Stripe (Test Mode - for development):**
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

2. **Stripe (Live Mode - for production):**
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

3. **Razorpay (Test Mode):**
```bash
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

4. **Razorpay (Live Mode):**
```bash
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

**Action Items:**

1. **Obtain API Keys:**
   - Stripe: https://dashboard.stripe.com/apikeys
   - Razorpay: https://dashboard.razorpay.com/app/keys

2. **Configure Webhook Endpoints:**
   - Stripe Dashboard → Webhooks → Add endpoint
     - URL: `https://your-domain.com/api/payments/webhook/stripe`
     - Events: `payment_intent.succeeded`, `payment_intent.failed`, `charge.refunded`
   - Razorpay Dashboard → Webhooks → Add webhook
     - URL: `https://your-domain.com/api/payments/webhook/razorpay`
     - Events: `payment.captured`, `payment.failed`, `refund.created`

3. **Store Secrets:**

**Option A: Kubernetes Secrets**
```bash
kubectl create secret generic payment-secrets \
  --from-literal=STRIPE_SECRET_KEY='sk_test_...' \
  --from-literal=STRIPE_PUBLISHABLE_KEY='pk_test_...' \
  --from-literal=STRIPE_WEBHOOK_SECRET='whsec_...' \
  --from-literal=RAZORPAY_KEY_ID='rzp_test_...' \
  --from-literal=RAZORPAY_KEY_SECRET='...' \
  --from-literal=RAZORPAY_WEBHOOK_SECRET='...'
```

**Option B: .env File (Development Only - Never Commit)**
```bash
# Add to /app/backend/.env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

4. **Update SecretsManager:**
```python
# Add to /app/backend/core/secrets_manager.py
REQUIRED_SECRETS = [
    'JWT_SECRET',
    'MONGODB_URI',
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'RAZORPAY_KEY_ID',
    'RAZORPAY_KEY_SECRET'
]
```

5. **Verify .gitignore:**
```bash
# Ensure these patterns are in .gitignore
*.env
*.key
*.secret
.env.local
.env.production
```

**Key Rotation Policy:**
- Rotate every 90 days
- Immediate rotation if compromised
- Use dual-secret validation during rotation (24-hour grace period)
- Log all key rotations in AdminAuditLog

---

### 4. MongoDB Transactions Configuration ⚠️

**Status:** UNKNOWN - Need to verify replica set and transactions enabled

**Requirements:**
- [ ] MongoDB replica set (minimum 3 nodes)
- [ ] Motor driver configured for transactions
- [ ] Connection string includes replica set name
- [ ] Transaction timeout configured
- [ ] Monitoring for failed transactions

**Current State:**
```python
# Database connection exists
Driver: Motor (async MongoDB driver)
Connection: Via MONGODB_URI
Replica Set: Unknown
Transactions: Not tested
```

**Verification Commands:**
```bash
# 1. Check if replica set is configured
mongosh "$MONGODB_URI" --eval "rs.status()"

# 2. Check replica set configuration
mongosh "$MONGODB_URI" --eval "rs.conf()"

# 3. Test transaction support
mongosh "$MONGODB_URI" --eval "
  session = db.getMongo().startSession();
  session.startTransaction();
  print('Transactions supported!');
  session.abortTransaction();
"
```

**Expected Output:**
```json
{
  "set": "rs0",
  "members": [
    {"_id": 0, "name": "mongo-0:27017", "stateStr": "PRIMARY"},
    {"_id": 1, "name": "mongo-1:27017", "stateStr": "SECONDARY"},
    {"_id": 2, "name": "mongo-2:27017", "stateStr": "SECONDARY"}
  ]
}
```

**Action Items:**

1. **If Using MongoDB Atlas:**
   - Transactions enabled by default ✅
   - Ensure connection string includes `?retryWrites=true`

2. **If Self-Hosted MongoDB:**

**Initialize Replica Set:**
```bash
# Connect to primary MongoDB instance
mongosh

# Initialize replica set
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo-0:27017" },
    { _id: 1, host: "mongo-1:27017" },
    { _id: 2, host: "mongo-2:27017" }
  ]
})

# Verify
rs.status()
```

3. **Update Connection String:**
```bash
# Before (no replica set)
MONGODB_URI=mongodb://localhost:27017/pairly

# After (with replica set)
MONGODB_URI=mongodb://mongo-0:27017,mongo-1:27017,mongo-2:27017/pairly?replicaSet=rs0&retryWrites=true
```

4. **Docker Compose Configuration:**
```yaml
services:
  mongo-0:
    image: mongo:7
    command: mongod --replSet rs0 --bind_ip_all
    ports:
      - "27017:27017"
    volumes:
      - mongo0_data:/data/db

  mongo-1:
    image: mongo:7
    command: mongod --replSet rs0 --bind_ip_all
    ports:
      - "27018:27017"
    volumes:
      - mongo1_data:/data/db

  mongo-2:
    image: mongo:7
    command: mongod --replSet rs0 --bind_ip_all
    ports:
      - "27019:27017"
    volumes:
      - mongo2_data:/data/db
```

5. **Test Transaction Support in Code:**
```python
# File: /app/backend/tests/test_mongodb_transactions.py
import pytest
from backend.database import db_client
from backend.models.user import User

@pytest.mark.asyncio
async def test_mongodb_transactions():
    """Verify MongoDB transactions work"""
    async with await db_client.start_session() as session:
        async with session.start_transaction():
            # Create test user
            user = User(email="test@tx.com", name="Test", credits_balance=100)
            await user.insert(session=session)
            
            # Abort transaction
            await session.abort_transaction()
        
        # Verify user was NOT created (transaction rolled back)
        found = await User.find_one(User.email == "test@tx.com")
        assert found is None, "Transaction rollback failed!"
```

**Motor Driver Configuration:**
```python
# Ensure in /app/backend/database.py
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    settings.MONGODB_URI,
    retryWrites=True,
    w='majority',  # Write concern for transactions
    readConcernLevel='majority'  # Read concern for transactions
)
```

---

### 5. Logging & Observability ⚠️

**Status:** IMPLEMENTED - Phase 7 structured logging active

**Requirements:**
- [✅] Structured JSON logging
- [✅] Log aggregation pipeline
- [ ] Payment-specific log filters
- [ ] Real-time log monitoring
- [ ] Alerting on payment failures
- [ ] Log retention policy (90 days minimum)

**Current State:**
```
Structured Logging: Active ✅ (Phase 7)
Format: JSON
Log File: /var/log/pairly/app.log
Rotation: 100MB, 5 backups
Aggregation: Not configured
```

**Action Items:**

1. **Verify Logging is Active:**
```bash
# Check recent logs
tail -f /var/log/pairly/app.log | jq .

# Filter payment-related logs
tail -f /var/log/pairly/app.log | jq 'select(.logger | contains("payment"))'
```

2. **Add Payment-Specific Loggers:**
```python
# Ensure these loggers exist:
logger = logging.getLogger('payment.intent')
logger = logging.getLogger('payment.webhook')
logger = logging.getLogger('payment.fraud')
logger = logging.getLogger('payment.reconciliation')
```

3. **Configure Log Aggregation (Choose One):**

**Option A: Elasticsearch + Kibana (ELK)**
```yaml
# Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/pairly/app.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "pairly-logs-%{+yyyy.MM.dd}"
```

**Option B: Loki + Grafana**
```yaml
# Promtail configuration
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: pairly
    static_configs:
      - targets:
          - localhost
        labels:
          job: pairly
          __path__: /var/log/pairly/app.log
```

**Option C: AWS CloudWatch**
```python
# Add CloudWatch handler to logging
import watchtower

cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group='pairly-production',
    stream_name='backend'
)
root_logger.addHandler(cloudwatch_handler)
```

4. **Configure Alerts:**

**Critical Alerts:**
- Payment webhook signature verification failures (>5/min)
- Payment intent creation failures (>10/min)
- Database transaction failures (>1/min)
- Reconciliation discrepancies (any)
- Webhook DLQ depth (>50 events)

**Alert Configuration (Prometheus):**
```yaml
groups:
  - name: payments
    rules:
      - alert: HighPaymentFailureRate
        expr: rate(payment_intent_failures_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High payment failure rate detected"
          
      - alert: WebhookSignatureFailures
        expr: rate(webhook_signature_failures_total[1m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Multiple webhook signature failures"
```

---

### 6. Legal & Compliance Checklist ⚠️

**Status:** DESIGN COMPLIANT - Implementation requires legal review

**Requirements:**
- [ ] PCI-DSS compliance verified (no card storage)
- [ ] Payment processor agreements signed
- [ ] Data retention policy documented
- [ ] Privacy policy updated (payment data handling)
- [ ] Terms of service include payment terms
- [ ] Refund policy documented
- [ ] Dispute resolution process defined

**PCI-DSS Compliance Verification:**

✅ **Level 4 Merchant (SAQ A)**
- No card data stored ✅
- All payments via Stripe/Razorpay ✅
- Only store provider tokens ✅
- No CVV/CVC storage ✅
- TLS for all communication ✅

**Action Items:**

1. **Payment Processor Agreements:**
   - [ ] Sign Stripe merchant agreement
   - [ ] Sign Razorpay merchant agreement
   - [ ] Configure payout accounts
   - [ ] Verify account limits (daily/monthly)

2. **Data Retention Policy:**
```
Payment Intents: 7 years (financial records)
Webhook Events: 90 days
Financial Ledger: Permanent (immutable)
Audit Logs: 7 years
Failed Transactions: 1 year
```

3. **Documentation Requirements:**
   - Privacy Policy: Add section on payment data handling
   - Terms of Service: Add payment terms, refund policy
   - Refund Policy: Document refund eligibility and process
   - Dispute Process: Document chargeback handling

4. **Regulatory Compliance (India-specific):**
   - [ ] RBI guidelines for payment aggregators
   - [ ] GST registration for services
   - [ ] TDS compliance for creator payouts

---

## VERIFICATION SCRIPT

```bash
#!/bin/bash
# File: /app/scripts/verify_phase8_infra.sh

echo "=== Phase 8 Infrastructure Pre-Check ==="
echo ""

# 1. Redis
echo "[1/6] Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis is running"
    MEMORY=$(redis-cli CONFIG GET maxmemory | tail -1)
    echo "  Memory: $MEMORY"
else
    echo "  ❌ Redis is not running"
    EXIT_CODE=1
fi
echo ""

# 2. MongoDB Replica Set
echo "[2/6] Checking MongoDB..."
if mongosh "$MONGODB_URI" --quiet --eval "rs.status().ok" 2>/dev/null | grep -q "1"; then
    echo "  ✅ MongoDB replica set is configured"
else
    echo "  ❌ MongoDB replica set not configured or not accessible"
    EXIT_CODE=1
fi
echo ""

# 3. Celery
echo "[3/6] Checking Celery..."
if command -v celery > /dev/null 2>&1; then
    echo "  ✅ Celery is installed"
else
    echo "  ❌ Celery is not installed"
    EXIT_CODE=1
fi
echo ""

# 4. Secrets
echo "[4/6] Checking Secrets..."
MISSING_SECRETS=""
for SECRET in STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET RAZORPAY_KEY_ID RAZORPAY_KEY_SECRET; do
    if [ -z "${!SECRET}" ]; then
        MISSING_SECRETS="$MISSING_SECRETS $SECRET"
    fi
done

if [ -z "$MISSING_SECRETS" ]; then
    echo "  ✅ All payment secrets configured"
else
    echo "  ❌ Missing secrets:$MISSING_SECRETS"
    EXIT_CODE=1
fi
echo ""

# 5. Logging
echo "[5/6] Checking Logging..."
if [ -f "/var/log/pairly/app.log" ]; then
    echo "  ✅ Log file exists"
    RECENT_LOGS=$(tail -1 /var/log/pairly/app.log 2>/dev/null)
    if [ -n "$RECENT_LOGS" ]; then
        echo "  ✅ Recent logs present"
    else
        echo "  ⚠️  No recent logs"
    fi
else
    echo "  ❌ Log file not found"
    EXIT_CODE=1
fi
echo ""

# 6. Python Dependencies
echo "[6/6] Checking Python Dependencies..."
REQUIRED_PACKAGES="stripe razorpay celery motor redis"
for PACKAGE in $REQUIRED_PACKAGES; do
    if python3 -c "import $PACKAGE" 2>/dev/null; then
        echo "  ✅ $PACKAGE installed"
    else
        echo "  ❌ $PACKAGE not installed"
        EXIT_CODE=1
    fi
done
echo ""

if [ -z "$EXIT_CODE" ]; then
    echo "✅ All pre-checks passed! Ready for Phase 8 implementation."
    exit 0
else
    echo "❌ Pre-checks failed. Fix blockers before proceeding."
    exit 1
fi
```

---

## SUMMARY

### Current Status:

| Component | Status | Priority |
|-----------|--------|----------|
| Redis | ⚠️ Unknown | CRITICAL |
| Celery | ❌ Not Installed | CRITICAL |
| Payment Secrets | ❌ Not Configured | CRITICAL |
| MongoDB Transactions | ⚠️ Unknown | CRITICAL |
| Logging | ✅ Active | HIGH |
| Legal/Compliance | ⚠️ Pending Review | HIGH |

### Estimated Time to Resolve:

- Redis Setup: 2-4 hours
- Celery Configuration: 4-6 hours
- Secrets Management: 1-2 hours
- MongoDB Verification: 1-2 hours
- Logging Configuration: 2-3 hours
- Legal Review: Depends on organization

**Total:** 1-2 days for infrastructure setup

### Go/No-Go Decision:

**Status:** 🟡 NO-GO (blockers present)

**Action:** Resolve 4 critical blockers (Redis, Celery, Secrets, MongoDB) before Phase 8 implementation.

**Next Step:** Run verification script and address failures.

---

**Document Status:** Complete  
**Last Updated:** December 9, 2025  
**Next Review:** After blocker resolution
