# 🏗️ TrueBond Infrastructure Setup Guide

**Quick Reference for Production Deployment**

---

## 📋 INFRASTRUCTURE CHECKLIST

- [ ] Redis (Cache & Pub/Sub)
- [ ] MongoDB Replica Set (Transactions)
- [ ] Celery Workers (Background Jobs)
- [ ] Cloud Storage (S3/GCS)
- [ ] Email Service (SendGrid/SES)
- [ ] SMS Service (Twilio/MSG91)
- [ ] WebRTC (STUN/TURN)
- [ ] Monitoring (Sentry/APM)
- [ ] CDN (CloudFlare/CloudFront)
- [ ] Load Balancer

---

## 1️⃣ REDIS SETUP

### Option A: Docker (Development/Testing)
```bash
# Start Redis container
docker run -d \
  --name truebond-redis \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --appendonly yes

# Test connection
docker exec -it truebond-redis redis-cli ping
# Should return: PONG
```

### Option B: Redis Cloud (Production)
```bash
# 1. Go to https://redis.com/try-free/
# 2. Create free account
# 3. Create database
# 4. Copy connection URL

# Update .env
REDIS_URL=redis://username:password@host:port
```

### Update Backend Configuration
```python
# backend/config.py
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
```

### Test Redis Connection
```bash
curl http://localhost:8000/api/health/redis
```

**Time:** 30 minutes
**Cost:** Free (development), $10-50/mo (production)

---

## 2️⃣ MONGODB REPLICA SET

### Current Status
- ✅ MongoDB Atlas connected (single node)
- ❌ Replica set NOT enabled (no transactions)

### Upgrade to Replica Set

#### Step 1: Upgrade Atlas Cluster
```
1. Go to MongoDB Atlas dashboard
2. Click your cluster
3. Click "Upgrade" or "Modify"
4. Select M10 or higher (M0 doesn't support replica sets)
5. Enable "Configure additional settings"
6. Under "Replication", ensure it's set to 3 nodes minimum
7. Click "Apply Changes"
```

#### Step 2: Update Connection String
```bash
# .env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/truebond?retryWrites=true&w=majority
```

#### Step 3: Enable Transactions in Code
```python
# backend/tb_database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReadPreference

client = AsyncIOMotorClient(
    MONGO_URL,
    replicaSet="atlas-xxxxx-shard-0",  # Your replica set name
    readPreference=ReadPreference.PRIMARY
)

# Test transaction support
async def test_transactions():
    async with await client.start_session() as session:
        async with session.start_transaction():
            # Test transaction
            print("✅ Transactions supported!")
```

#### Step 4: Update Payment Code
```python
# backend/services/payments/manager.py
# Transactions now work!
async with await client.start_session() as session:
    async with session.start_transaction():
        # Update payment intent
        # Add credits
        # Both succeed or both fail (atomic)
```

**Time:** 30 minutes
**Cost:** M10 cluster: $57/month (required for replica set)

---

## 3️⃣ CELERY WORKERS

### Install Dependencies
```bash
pip install celery redis
```

### Create Celery App
```python
# backend/celery_app.py
from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

app = Celery(
    'truebond',
    broker=REDIS_URL,
    backend=REDIS_URL
)

app.config_from_object('backend.celery_config')

# Auto-discover tasks
app.autodiscover_tasks(['backend.workers'])
```

### Create Config
```python
# backend/celery_config.py
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Kolkata'
enable_utc = True

# Task routing
task_routes = {
    'backend.workers.webhooks.*': {'queue': 'webhooks'},
    'backend.workers.notifications.*': {'queue': 'notifications'},
    'backend.workers.billing.*': {'queue': 'billing'},
}
```

### Create Workers
```python
# backend/workers/webhook_worker.py
from backend.celery_app import app

@app.task(bind=True, max_retries=3)
def process_stripe_webhook(self, event_data):
    try:
        # Process webhook
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### Start Workers
```bash
# Terminal 1: Default worker
celery -A backend.celery_app worker \
  --loglevel=info \
  --concurrency=4

# Terminal 2: Webhook worker
celery -A backend.celery_app worker \
  --loglevel=info \
  --queues=webhooks \
  --concurrency=2

# Terminal 3: Beat scheduler (for scheduled tasks)
celery -A backend.celery_app beat \
  --loglevel=info
```

### Production: Supervisor Config
```ini
# /etc/supervisor/conf.d/celery.conf
[program:celery-worker]
command=/path/to/venv/bin/celery -A backend.celery_app worker --loglevel=info
directory=/app/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery-worker.log

[program:celery-beat]
command=/path/to/venv/bin/celery -A backend.celery_app beat --loglevel=info
directory=/app/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery-beat.log
```

**Time:** 4 hours
**Cost:** Included in server costs

---

## 4️⃣ CLOUD STORAGE (AWS S3)

### Create S3 Bucket
```bash
# Using AWS CLI
aws s3 mb s3://truebond-media-prod

# Set bucket policy (public read for profile pics)
aws s3api put-bucket-policy \
  --bucket truebond-media-prod \
  --policy file://bucket-policy.json
```

### Bucket Policy (bucket-policy.json)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::truebond-media-prod/public/*"
    }
  ]
}
```

### Install SDK
```bash
pip install boto3
```

### Configure Backend
```python
# backend/config.py
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET", "truebond-media-prod")

# .env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
S3_BUCKET=truebond-media-prod
```

### Create Upload Service
```python
# backend/services/storage_service.py
import boto3
from botocore.exceptions import ClientError

class StorageService:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

    async def upload_file(self, file_data, file_name, content_type):
        key = f"uploads/{user_id}/{file_name}"
        self.s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=file_data,
            ContentType=content_type,
            ACL='public-read'
        )
        return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
```

**Time:** 2 hours
**Cost:** $3-30/month (depends on usage)

---

## 5️⃣ EMAIL SERVICE (SendGrid)

### Sign Up
```
1. Go to https://sendgrid.com/
2. Create free account (100 emails/day free)
3. Go to Settings > API Keys
4. Create API key with "Full Access"
5. Copy key
```

### Install SDK
```bash
pip install sendgrid
```

### Configure Backend
```python
# backend/config.py
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@truebond.com")

# .env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
FROM_EMAIL=noreply@truebond.com
```

### Create Email Service
```python
# backend/services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(SENDGRID_API_KEY)

    async def send_password_reset(self, to_email, reset_token):
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject='Reset Your Password',
            html_content=f'''
                <h1>Reset Your Password</h1>
                <p>Click the link below to reset your password:</p>
                <a href="https://truebond.com/reset?token={reset_token}">
                    Reset Password
                </a>
            '''
        )
        self.sg.send(message)
```

**Time:** 2 hours
**Cost:** Free (100/day), $20/mo (100k emails)

---

## 6️⃣ SMS SERVICE (Twilio)

### Sign Up
```
1. Go to https://twilio.com/
2. Create account ($15 free credit)
3. Get phone number
4. Copy Account SID and Auth Token
```

### Install SDK
```bash
pip install twilio
```

### Configure Backend
```python
# backend/config.py
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# .env
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+1234567890
```

### Create SMS Service
```python
# backend/services/sms_service.py
from twilio.rest import Client

class SMSService:
    def __init__(self):
        self.client = Client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN
        )

    async def send_otp(self, phone_number, otp_code):
        message = self.client.messages.create(
            body=f'Your TrueBond verification code is: {otp_code}',
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return message.sid
```

**Time:** 1 hour
**Cost:** $15 free credit, then $0.0075/SMS in India

---

## 7️⃣ WebRTC (STUN/TURN)

### Option A: Free STUN Servers
```javascript
// frontend/src/services/webrtc.js
const iceServers = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
  { urls: 'stun:stun2.l.google.com:19302' }
];
```

### Option B: Self-Hosted TURN (coturn)
```bash
# Install coturn
apt-get install coturn

# Configure
# /etc/turnserver.conf
listening-port=3478
fingerprint
lt-cred-mech
user=truebond:yourpassword
realm=truebond.com
```

### Option C: Managed Service (100ms)
```
1. Go to https://www.100ms.live/
2. Create account
3. Get API key
4. Copy app credentials
```

```javascript
// frontend
import { HMSReactiveStore } from '@100mslive/hms-video-store';

const hmsStore = new HMSReactiveStore();
const hmsActions = hmsStore.getActions();

// Join room
await hmsActions.join({
  userName: user.name,
  authToken: token,
  settings: {
    isAudioMuted: false,
    isVideoMuted: false
  }
});
```

**Time:** 6 hours (managed), 2 days (self-hosted)
**Cost:** Free (Google STUN), $150/mo (100ms for 1000 hours)

---

## 8️⃣ MONITORING (Sentry)

### Sign Up
```
1. Go to https://sentry.io/
2. Create free account (5k events/month)
3. Create new project (Python)
4. Copy DSN
```

### Install SDK
```bash
pip install sentry-sdk[fastapi]
```

### Configure Backend
```python
# backend/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "production")
)

# .env
SENTRY_DSN=https://xxxx@sentry.io/yyyy
```

### Frontend (Optional)
```javascript
// frontend/src/main.jsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay()
  ],
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1
});
```

**Time:** 1 hour
**Cost:** Free (5k events), $29/mo (Team)

---

## 9️⃣ CDN (CloudFlare)

### Set Up
```
1. Go to https://cloudflare.com/
2. Add your domain
3. Update nameservers at registrar
4. Enable "Proxy" (orange cloud) for domain
5. Configure SSL (Full or Full Strict)
```

### Cache Rules
```
# CloudFlare Dashboard > Caching > Cache Rules

# Cache static assets
Rule 1: URI Path matches "^/assets/.*"
  → Cache everything, TTL: 1 month

# Cache images
Rule 2: File Extension matches "jpg|png|gif|svg|webp"
  → Cache everything, TTL: 1 week

# Don't cache API
Rule 3: URI Path starts with "/api/"
  → Bypass cache
```

### Page Rules (Optional)
```
# API subdomain: api.truebond.com
Rule: Cache Level: Bypass

# Assets subdomain: assets.truebond.com
Rule: Cache Level: Cache Everything
```

**Time:** 1 hour
**Cost:** Free (basic), $20/mo (Pro)

---

## 🔟 LOAD BALANCER (nginx)

### Install
```bash
apt-get install nginx
```

### Configure
```nginx
# /etc/nginx/sites-available/truebond
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;  # If running multiple instances
}

upstream frontend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name truebond.com www.truebond.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name truebond.com www.truebond.com;

    ssl_certificate /etc/letsencrypt/live/truebond.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/truebond.com/privkey.pem;

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /socket.io/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}
```

### Enable Site
```bash
ln -s /etc/nginx/sites-available/truebond /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

**Time:** 2 hours
**Cost:** Included in server

---

## 📦 COMPLETE SETUP SCRIPT

```bash
#!/bin/bash
# setup_infrastructure.sh

echo "🚀 Setting up TrueBond infrastructure..."

# 1. Install dependencies
pip install redis celery boto3 sendgrid twilio sentry-sdk

# 2. Start Redis (Docker)
docker run -d --name truebond-redis -p 6379:6379 redis:7-alpine

# 3. Update .env with all credentials
cat >> .env << EOF

# Redis
REDIS_URL=redis://localhost:6379

# MongoDB (update with your Atlas URL)
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/truebond?retryWrites=true&w=majority

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
S3_BUCKET=truebond-media-prod

# SendGrid
SENDGRID_API_KEY=SG.xxxxx
FROM_EMAIL=noreply@truebond.com

# Twilio
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+1234567890

# Sentry
SENTRY_DSN=https://xxxx@sentry.io/yyyy

# Stripe (production)
STRIPE_SECRET_KEY=sk_live_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx

# Razorpay (production)
RAZORPAY_KEY_ID=rzp_live_xxxx
RAZORPAY_KEY_SECRET=xxxx
RAZORPAY_WEBHOOK_SECRET=xxxx
EOF

echo "✅ Infrastructure setup complete!"
echo "📝 Remember to:"
echo "  1. Update MongoDB to replica set (M10+)"
echo "  2. Fill in actual credentials in .env"
echo "  3. Start Celery workers"
echo "  4. Configure domain and SSL"
```

**Time:** 1 day (full setup)
**Cost:** ~$350/month (initial scale)

---

## ✅ VERIFICATION CHECKLIST

After setup, verify each service:

```bash
# Redis
redis-cli ping

# MongoDB transactions
curl http://localhost:8000/api/health/db

# Celery
celery -A backend.celery_app inspect active

# S3
aws s3 ls s3://truebond-media-prod

# Email (send test)
curl -X POST http://localhost:8000/api/test/email

# SMS (send test)
curl -X POST http://localhost:8000/api/test/sms

# Sentry (trigger error)
curl http://localhost:8000/api/test/sentry

# All services health check
curl http://localhost:8000/api/health/detailed
```

---

## 🆘 TROUBLESHOOTING

### Redis Connection Failed
```bash
# Check if running
docker ps | grep redis

# Check logs
docker logs truebond-redis

# Test connection
redis-cli -h localhost -p 6379 ping
```

### MongoDB Transaction Error
```
Error: This MongoDB deployment does not support transactions
Solution: Upgrade to M10+ cluster (replica set required)
```

### Celery Worker Not Starting
```bash
# Check broker connection
python -c "from celery import Celery; app = Celery(broker='redis://localhost:6379'); print(app.broker_connection())"

# Check logs
celery -A backend.celery_app worker --loglevel=debug
```

### S3 Upload Permission Denied
```bash
# Verify credentials
aws sts get-caller-identity

# Check bucket policy
aws s3api get-bucket-policy --bucket truebond-media-prod
```

---

## 📞 SUPPORT CONTACTS

- **MongoDB Atlas:** support@mongodb.com
- **Redis Cloud:** support@redis.com
- **AWS:** https://aws.amazon.com/support
- **SendGrid:** support@sendgrid.com
- **Twilio:** support@twilio.com
- **Sentry:** support@sentry.io

---

*Last Updated: January 12, 2026*
