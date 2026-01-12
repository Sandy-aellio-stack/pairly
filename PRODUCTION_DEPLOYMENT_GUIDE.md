# TrueBond Production Deployment Guide

**Version:** 1.0.0
**Last Updated:** January 12, 2026
**Status:** Production Ready for Beta Launch

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Redis Setup](#redis-setup)
6. [Application Deployment](#application-deployment)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Monitoring Setup](#monitoring-setup)
9. [Security Hardening](#security-hardening)
10. [Post-Deployment Verification](#post-deployment-verification)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Services

- **MongoDB Atlas** (or MongoDB server)
- **Redis Cloud** (or Redis server)
- **Domain name** with DNS configured
- **Server/VM** with:
  - Ubuntu 22.04 LTS or newer
  - 2+ CPU cores
  - 4GB+ RAM
  - 50GB+ storage
  - Docker & Docker Compose installed

### Required Tools

```bash
# On your deployment server
sudo apt update
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx git
```

### Optional but Recommended

- **Sentry account** for error tracking
- **SendGrid/AWS SES** for email notifications
- **Uptime monitoring** (e.g., UptimeRobot, Pingdom)
- **Backup solution** (automated database backups)

---

## Infrastructure Setup

### 1. Server Provisioning

**Recommended Providers:**
- DigitalOcean (Droplet - $24/month)
- AWS (EC2 t3.medium)
- Google Cloud (e2-medium)
- Hetzner (CX31)

**Server Requirements:**
```
OS: Ubuntu 22.04 LTS
RAM: 4GB minimum
CPU: 2 cores minimum
Storage: 50GB SSD
Bandwidth: Unlimited or 2TB+
```

### 2. Initial Server Setup

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Create non-root user
adduser truebond
usermod -aG sudo truebond
usermod -aG docker truebond

# Switch to new user
su - truebond

# Setup firewall
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

---

## Environment Configuration

### 1. Clone Repository

```bash
cd /home/truebond
git clone https://github.com/your-org/truebond.git
cd truebond
```

### 2. Create Production Environment File

```bash
cp .env.production.example .env.production
nano .env.production
```

### 3. Fill in Production Values

**Critical Variables (MUST be changed):**

```bash
# Environment
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.com

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET=your-64-character-random-secret-here

# MongoDB (from MongoDB Atlas)
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/truebond?retryWrites=true&w=majority

# Redis (from Redis Cloud or Upstash)
REDIS_URL=redis://default:password@redis-host:port

# Sentry (for error tracking)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

**Email Configuration (Recommended):**

```bash
EMAIL_ENABLED=true
EMAIL_FROM=noreply@yourdomain.com
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

### 4. Generate Strong Secrets

```bash
# Generate JWT secret (64 characters)
openssl rand -hex 32

# Generate admin password
openssl rand -base64 24
```

---

## Database Setup

### MongoDB Atlas Setup

1. **Create Account**
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for free tier or paid plan

2. **Create Cluster**
   - Choose region closest to your server
   - Select M10 or higher for production
   - Enable backup (Atlas auto-backup)

3. **Configure Security**
   ```
   - Network Access: Add your server IP
   - Database Access: Create user with read/write permissions
   - Connection String: Copy and add to .env.production
   ```

4. **Create Database**
   ```
   Database name: truebond
   Collections: Will be created automatically by Beanie ODM
   ```

5. **Enable Monitoring**
   - Enable Atlas monitoring
   - Setup alerts for:
     - High CPU usage (>80%)
     - High connection count
     - Slow queries (>100ms)

### Database Indexes

Database indexes are created automatically by Beanie ODM. Verify after first deployment:

```bash
# Connect to MongoDB
mongosh "your-connection-string"

# Check indexes
use truebond
db.tb_users.getIndexes()
db.tb_messages.getIndexes()
db.tb_conversations.getIndexes()
```

---

## Redis Setup

### Redis Cloud Setup (Recommended)

1. **Create Account**
   - Go to https://redis.com/cloud/ or https://upstash.com

2. **Create Database**
   - Select region closest to your server
   - Choose size: 256MB minimum
   - Enable eviction policy: allkeys-lru

3. **Get Connection String**
   ```
   Format: redis://default:password@host:port
   Add to .env.production
   ```

### Self-Hosted Redis (Alternative)

```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf

# Set password
requirepass your-redis-password

# Set maxmemory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

---

## Application Deployment

### 1. Build Docker Images

```bash
cd /home/truebond/truebond

# Build production Docker image
docker build -f backend/Dockerfile.production -t truebond-backend:latest backend/

# Verify build
docker images | grep truebond
```

### 2. Start Services

```bash
# Load environment variables
export $(cat .env.production | xargs)

# Start with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose -f docker-compose.production.yml logs -f
```

### 3. Verify Services

```bash
# Check running containers
docker ps

# Health check
curl http://localhost:8000/api/health

# Detailed health check
curl http://localhost:8000/api/health/detailed

# Readiness check
curl http://localhost:8000/api/ready
```

---

## SSL/TLS Configuration

### Using Certbot (Let's Encrypt) - Recommended

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is configured automatically via cron
```

### Update Nginx Configuration

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-available/truebond

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### SSL Configuration in nginx.conf

Already configured in `nginx/nginx.conf`:
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS header (optional, enable after testing)

---

## Monitoring Setup

### 1. Sentry Configuration

```bash
# Already configured in .env.production
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
```

**Sentry Setup:**
1. Create account at https://sentry.io
2. Create new project (Python/FastAPI)
3. Copy DSN to .env.production
4. Deploy application
5. Verify errors are captured

### 2. Health Check Monitoring

Setup external monitoring for:
- **Primary endpoint:** `https://yourdomain.com/api/health`
- **Check interval:** 1 minute
- **Alert after:** 3 failed checks

**Recommended services:**
- UptimeRobot (free)
- Pingdom
- Better Uptime
- StatusCake

### 3. Log Monitoring

```bash
# View application logs
docker-compose -f docker-compose.production.yml logs -f backend

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Setup log rotation
sudo nano /etc/logrotate.d/truebond
```

Logrotate configuration:
```
/var/log/truebond/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 truebond truebond
}
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Check firewall status
sudo ufw status

# Only allow necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Block everything else
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable firewall
sudo ufw enable
```

### 2. SSH Hardening

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Recommended settings:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no
AllowUsers truebond

# Restart SSH
sudo systemctl restart sshd
```

### 3. Automatic Security Updates

```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades

# Enable automatic security updates
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. Fail2Ban (Brute Force Protection)

```bash
# Install Fail2Ban
sudo apt install fail2ban

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# Enable and start
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 5. Security Headers

Already configured in application:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy`

### 6. Rate Limiting

Already configured:
- API endpoints: 60 requests/minute per user
- Authentication endpoints: 10 requests/minute per IP
- Message sending: 30 messages/minute per user
- WebSocket typing: 30 events/minute per user

---

## Post-Deployment Verification

### 1. Functional Tests

```bash
# Health checks
curl https://yourdomain.com/api/health
curl https://yourdomain.com/api/health/detailed
curl https://yourdomain.com/api/ready

# API endpoint test
curl https://yourdomain.com/api/auth/health

# Expected response:
# {"status":"healthy","service":"truebond","version":"1.0.0"}
```

### 2. WebSocket Test

```javascript
// Test WebSocket connection
const io = require('socket.io-client');

const socket = io('https://yourdomain.com', {
  auth: { token: 'valid-jwt-token' },
  transports: ['websocket']
});

socket.on('connect', () => {
  console.log('✅ WebSocket connected');
});

socket.on('connect_error', (error) => {
  console.error('❌ WebSocket failed:', error);
});
```

### 3. Security Headers Test

```bash
# Check security headers
curl -I https://yourdomain.com

# Expected headers:
# Strict-Transport-Security
# X-Content-Type-Options
# X-Frame-Options
# X-XSS-Protection
```

### 4. SSL Test

Visit: https://www.ssllabs.com/ssltest/
Enter your domain and verify A or A+ rating

### 5. Performance Test

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Load test (100 requests, 10 concurrent)
ab -n 100 -c 10 https://yourdomain.com/api/health

# Expected:
# - Requests per second: >100
# - Time per request: <100ms
# - No failed requests
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs backend

# Common issues:
# 1. Environment variables not set
# 2. MongoDB connection failed
# 3. Redis connection failed
# 4. Port 8000 already in use

# Restart services
docker-compose -f docker-compose.production.yml restart
```

### MongoDB Connection Failed

```bash
# Test MongoDB connection
mongosh "your-connection-string"

# Common issues:
# 1. IP not whitelisted in MongoDB Atlas
# 2. Wrong username/password
# 3. Firewall blocking outbound connections
# 4. Connection string typo
```

### Redis Connection Failed

```bash
# Test Redis connection
redis-cli -h host -p port -a password ping

# Expected: PONG

# Common issues:
# 1. Wrong password
# 2. Firewall blocking port 6379
# 3. Redis server not running
```

### WebSocket Not Working

```bash
# Check Nginx WebSocket configuration
sudo nginx -t
sudo systemctl status nginx

# Common issues:
# 1. Missing WebSocket upgrade headers
# 2. Nginx proxy timeout too short
# 3. Firewall blocking WebSocket connections
```

### High Memory Usage

```bash
# Check container memory
docker stats

# Reduce workers if needed (in Dockerfile.production)
# Change: --workers 4
# To: --workers 2
```

### 502 Bad Gateway

```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Common issues:
# 1. Backend container crashed
# 2. Wrong upstream configuration
# 3. Backend not listening on correct port
```

---

## Backup & Recovery

### MongoDB Backups

**MongoDB Atlas** (Automated):
- Continuous backups enabled by default
- Point-in-time recovery available
- Restore from Atlas UI

**Manual Backup:**
```bash
# Export database
mongodump --uri="your-connection-string" --out=/backup/truebond-$(date +%Y%m%d)

# Compress backup
tar -czf truebond-$(date +%Y%m%d).tar.gz /backup/truebond-$(date +%Y%m%d)
```

### Application State Backups

```bash
# Backup environment configuration
cp .env.production .env.production.backup

# Backup Redis (if self-hosted)
redis-cli --rdb /backup/redis-$(date +%Y%m%d).rdb
```

### Automated Backup Script

```bash
#!/bin/bash
# /home/truebond/scripts/backup.sh

DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/backup/truebond"

# MongoDB backup (if not using Atlas)
mongodump --uri="$MONGO_URL" --out="$BACKUP_DIR/mongo-$DATE"

# Redis backup (if self-hosted)
redis-cli --rdb "$BACKUP_DIR/redis-$DATE.rdb"

# Compress
tar -czf "$BACKUP_DIR/truebond-$DATE.tar.gz" "$BACKUP_DIR/mongo-$DATE" "$BACKUP_DIR/redis-$DATE.rdb"

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "truebond-*.tar.gz" -mtime +30 -delete

# Upload to S3 (optional)
# aws s3 cp "$BACKUP_DIR/truebond-$DATE.tar.gz" s3://your-bucket/backups/
```

---

## Performance Tuning

### 1. Uvicorn Workers

```bash
# In Dockerfile.production
# Adjust based on CPU cores (2x cores recommended)
--workers 4
```

### 2. MongoDB Connection Pool

```python
# Already optimized in backend/tb_database.py
# maxPoolSize: 50
# minPoolSize: 10
```

### 3. Redis Memory

```bash
# Adjust based on usage
maxmemory 512mb
```

### 4. Nginx Optimization

Already configured in `nginx.conf`:
- Worker connections: 2048
- Gzip compression enabled
- Keepalive enabled
- Client body size: 10MB

---

## Maintenance

### Regular Tasks

**Daily:**
- Check error logs
- Monitor Sentry dashboard
- Check uptime monitor

**Weekly:**
- Review application logs
- Check database performance
- Update dependencies (if security patches)

**Monthly:**
- Review access logs
- Check disk space usage
- Review backup integrity
- Test disaster recovery

### Updates & Patches

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# Check for Python dependency updates
pip list --outdated
```

---

## Support & Documentation

**Internal Documentation:**
- Architecture: `/docs/BACKEND_ARCHITECTURE.md`
- Phase 3A Real-time: `/PHASE3A_REALTIME_MESSAGING_COMPLETE.md`
- Real-time guide: `/REALTIME_MESSAGING_GUIDE.md`

**External Resources:**
- FastAPI docs: https://fastapi.tiangolo.com
- MongoDB docs: https://docs.mongodb.com
- Redis docs: https://redis.io/docs
- Socket.IO docs: https://socket.io/docs

---

## Deployment Checklist

Use the **BETA_LAUNCH_CHECKLIST.md** for pre-launch verification.

---

**End of Production Deployment Guide**

*For beta launch checklist and rollback procedures, see:*
- `BETA_LAUNCH_CHECKLIST.md`
- `ROLLBACK_PLAN.md`
