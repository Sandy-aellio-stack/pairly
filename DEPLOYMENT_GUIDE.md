# Luveloop Deployment Guide

## 🚀 Production Deployment

This guide covers deploying Luveloop in a production environment with Docker, environment configuration, and scaling considerations.

## 📋 Prerequisites

### Infrastructure Requirements
- **Docker & Docker Compose** installed
- **MongoDB** database (Atlas or self-hosted)
- **Redis** server (ElastiCache or self-hosted)
- **Load Balancer** (Nginx, ALB, or Cloudflare)
- **SSL Certificate** (Let's Encrypt or managed)
- **Domain name** configured

### Cloud Storage Setup
Choose one of the following:
- **AWS S3** with IAM credentials
- **Cloudflare R2** with API tokens
- **Supabase Storage** with service keys

### TURN Server (for WebRTC)
- **coturn** server or managed TURN service
- **Static IP address** recommended
- **SSL certificates** for TURN over TLS

## 🔧 Environment Configuration

### 1. Backend Environment (.env)
```bash
# Application
ENVIRONMENT=production
DEBUG=false
FRONTEND_URL=https://yourapp.com

# Database
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/luveloop
REDIS_URL=redis://user:pass@redis-cluster:6379

# Authentication
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_REFRESH_SECRET=your-refresh-secret-key
JWT_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7

# Storage (AWS S3)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_BUCKET_NAME=luveloop-media-prod
AWS_REGION=us-east-1

# Storage (Cloudflare R2 - alternative)
AWS_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com

# Push Notifications
FCM_SERVER_KEY=AAAA...:...

# TURN Server (WebRTC)
TURN_SERVER_URL=turn:turn.yourapp.com:3478
TURN_USERNAME=turnuser
TURN_PASSWORD=turnpass

# Security
CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com
ALLOWED_HOSTS=yourapp.com,www.yourapp.com
```

### 2. Frontend Environment (.env.production)
```bash
VITE_API_URL=https://api.yourapp.com
VITE_SOCKET_URL=https://api.yourapp.com
VITE_APP_NAME=Luveloop
VITE_APP_VERSION=1.0.0
```

## 🐳 Docker Configuration

### 1. Production Dockerfile
```dockerfile
# backend/Dockerfile.production
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main_production:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Docker Compose Production
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.production
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend

volumes:
  redis_data:
```

## 🌐 Nginx Configuration

### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=socket:10m rate=5r/s;

    server {
        listen 80;
        server_name yourapp.com www.yourapp.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourapp.com www.yourapp.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Frontend static files
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Socket.IO with sticky sessions
        location /socket.io/ {
            limit_req zone=socket burst=10 nodelay;
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 🔄 Deployment Process

### 1. Automated Deployment Script
```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Deploying Luveloop..."

# Pull latest code
git pull origin main

# Build and deploy
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

# Wait for services to start
sleep 30

# Health check
echo "🔍 Checking health..."
if curl -f http://localhost:8000/api/health; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

echo "✅ Deployment complete!"
```

### 2. CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/deploy.yml
name: Deploy Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/luveloop
            git pull origin main
            ./deploy.sh
```

## 📊 Monitoring & Logging

### 1. Application Monitoring
```bash
# Health checks
curl https://api.yourapp.com/api/health
curl https://api.yourapp.com/api/health/detailed

# Log monitoring
docker-compose -f docker-compose.production.yml logs -f backend
```

### 2. System Monitoring
- **Prometheus** for metrics collection
- **Grafana** for dashboards
- **Alertmanager** for notifications
- **ELK Stack** for log aggregation

### 3. Key Metrics to Monitor
- API response times
- Socket.IO connection counts
- Message throughput
- Call success rates
- Error rates
- Resource usage (CPU, memory, disk)

## 🔒 Security Hardening

### 1. Network Security
- **Firewall rules** to restrict access
- **VPN** for admin access
- **DDoS protection** (Cloudflare)
- **WAF** rules for common attacks

### 2. Application Security
- **Environment variables** for secrets
- **Regular security updates**
- **Dependency scanning**
- **Static code analysis**

### 3. Database Security
- **MongoDB authentication** enabled
- **Redis password** protection
- **Network isolation** for databases
- **Regular backups**

## 🌍 Scaling Strategy

### 1. Horizontal Scaling
```yaml
# Scale backend instances
docker-compose -f docker-compose.production.yml up -d --scale backend=3
```

### 2. Database Scaling
- **MongoDB replica set** for high availability
- **Redis cluster** for horizontal scaling
- **Read replicas** for read-heavy workloads

### 3. CDN Configuration
- **CloudFront** or **Cloudflare** for static assets
- **Media caching** for images/videos
- **Geographic distribution**

## 🔄 Backup & Recovery

### 1. Database Backups
```bash
# MongoDB backup
mongodump --uri="mongodb://user:pass@cluster.mongodb.net/luveloop" --out=/backup/$(date +%Y%m%d)

# Redis backup
redis-cli --rdb /backup/redis-$(date +%Y%m%d).rdb
```

### 2. Automated Backup Script
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/$DATE"

mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --uri="$MONGODB_URL" --out="$BACKUP_DIR/mongodb"

# Backup Redis
redis-cli --rdb "$BACKUP_DIR/redis.rdb"

# Compress backup
tar -czf "/backup/luveloop_backup_$DATE.tar.gz" -C /backup $DATE

# Cleanup old backups (keep 7 days)
find /backup -name "luveloop_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: luveloop_backup_$DATE.tar.gz"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Socket.IO Connection Issues
```bash
# Check nginx configuration
nginx -t

# Verify WebSocket upgrade headers
curl -I -H "Connection: Upgrade" -H "Upgrade: websocket" https://api.yourapp.com/socket.io/
```

#### 2. Database Connection Issues
```bash
# Test MongoDB connection
mongosh "$MONGODB_URL"

# Test Redis connection
redis-cli -u "$REDIS_URL" ping
```

#### 3. Storage Upload Issues
```bash
# Test S3 credentials
aws s3 ls s3://$AWS_BUCKET_NAME

# Check bucket permissions
aws s3api get-bucket-policy --bucket $AWS_BUCKET_NAME
```

### Performance Optimization

#### 1. Database Indexing
```javascript
// MongoDB indexes for messages
db.tb_messages.createIndex({ "sender_id": 1, "receiver_id": 1, "created_at": -1 })
db.tb_messages.createIndex({ "receiver_id": 1, "is_read": 1 })
```

#### 2. Redis Optimization
```bash
# Redis memory optimization
redis-cli config set maxmemory-policy allkeys-lru
```

## 📞 Support

For deployment issues:
1. Check the logs: `docker-compose logs backend`
2. Verify environment variables
3. Test database connections
4. Review nginx configuration
5. Check SSL certificates

---

**Ready for production deployment! 🚀**
