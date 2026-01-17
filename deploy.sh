#!/bin/bash
# ============================================
# LUVELOOP VPS DEPLOYMENT SCRIPT
# ============================================
# Run on your VPS at: /var/www/pairly/deploy.sh

set -e

echo "🚀 Starting Luveloop Deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/var/www/pairly"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 1. Backend Setup
echo -e "${YELLOW}📦 Setting up Backend...${NC}"
cd $BACKEND_DIR

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt --quiet

# Copy production env if not exists
if [ ! -f ".env" ]; then
    echo -e "${RED}⚠️  Backend .env not found! Create it manually.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend setup complete${NC}"

# 2. Frontend Setup
echo -e "${YELLOW}📦 Setting up Frontend...${NC}"
cd $FRONTEND_DIR

# Install dependencies
npm install --silent

# Build for production
npm run build

echo -e "${GREEN}✅ Frontend build complete${NC}"

# 3. Nginx Configuration
echo -e "${YELLOW}🔧 Configuring Nginx...${NC}"

# Copy nginx config if exists
if [ -f "$PROJECT_DIR/nginx-luveloop.conf" ]; then
    sudo cp $PROJECT_DIR/nginx-luveloop.conf /etc/nginx/sites-available/luveloop
    sudo ln -sf /etc/nginx/sites-available/luveloop /etc/nginx/sites-enabled/
fi

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

echo -e "${GREEN}✅ Nginx configured${NC}"

# 4. Start/Restart Backend with PM2 or systemd
echo -e "${YELLOW}🔄 Starting Backend Service...${NC}"

cd $BACKEND_DIR
source venv/bin/activate

# Option A: Using PM2
if command -v pm2 &> /dev/null; then
    pm2 delete luveloop-backend 2>/dev/null || true
    pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name luveloop-backend
    pm2 save
    echo -e "${GREEN}✅ Backend started with PM2${NC}"
# Option B: Direct start (use screen or tmux in production)
else
    echo -e "${YELLOW}Starting backend directly... (Use PM2 in production)${NC}"
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /var/log/luveloop-backend.log 2>&1 &
    echo -e "${GREEN}✅ Backend started${NC}"
fi

# 5. Final Checks
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "📌 Checklist:"
echo "   [ ] SSL certificate active (https://luveloop.com)"
echo "   [ ] Backend running on port 8000"
echo "   [ ] Frontend served from /var/www/pairly/frontend/dist"
echo "   [ ] MongoDB Atlas connected"
echo "   [ ] Redis running locally"
echo ""
echo "🔗 URLs:"
echo "   Frontend: https://luveloop.com"
echo "   API: https://luveloop.com/api"
echo "   Health: https://luveloop.com/api/health"
echo ""
