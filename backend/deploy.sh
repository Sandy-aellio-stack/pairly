#!/usr/bin/env bash
set -e

echo "🚀 Starting Pairly Backend Deployment..."

# Build and start containers
echo "📦 Building and starting containers..."
docker-compose up -d --build

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to start..."
sleep 10

# Initialize MongoDB replica set (only needed first time)
echo "🔧 Initializing MongoDB replica set..."
MONGO_CONTAINER=$(docker ps -qf "ancestor=mongo:6.0")
if [ -n "$MONGO_CONTAINER" ]; then
    docker exec -it $MONGO_CONTAINER mongosh --eval 'rs.initiate()' || echo "Replica set may already be initialized"
else
    echo "⚠️  MongoDB container not found, skipping replica set init"
fi

echo "✅ Deployment complete!"
echo "📡 API available at: http://localhost:8001"
echo "📊 Health check: curl http://localhost:8001/api/health"
