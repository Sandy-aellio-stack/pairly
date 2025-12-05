# 🚀 Phase 1: Post/Feed System - Setup & Run Guide

This guide covers setting up and running the Phase 1 features: Post/Feed system with subscription scaffolding.

---

## 📋 **What Was Added**

### **New Models:**
- `backend/models/post.py` - Creator posts with media
- `backend/models/subscription.py` - Subscription tiers and user subscriptions

### **New Routes:**
- `backend/routes/posts.py` - Post CRUD operations
- `backend/routes/feed.py` - Home feed and creator timelines

### **New Utilities:**
- `backend/utils/media.py` - Media validation
- `backend/migrations/0001_add_post_and_subscription.py` - Database migration

### **DevOps:**
- `Dockerfile` - Production container
- `.github/workflows/ci.yml` - CI/CD pipeline
- `backend/tests/test_posts.py` - Test suite

---

## 🔧 **Local Development Setup**

### **1. Install Dependencies**

```bash
cd /app/backend
pip install -r requirements.txt
```

### **2. Run Database Migration**

```bash
# Make sure MongoDB is running
python -m backend.migrations.0001_add_post_and_subscription
```

This creates indexes for:
- Posts (creator timeline, public feed, active posts)
- Subscription tiers (creator lookup, tier lookup)
- User subscriptions (user subs, creator subscribers, payment provider lookups)

### **3. Restart Backend Server**

```bash
# If using supervisor (production)
sudo supervisorctl restart backend

# OR for local development
cd /app
uvicorn backend.server:app --reload --host 0.0.0.0 --port 8001
```

### **4. Verify Installation**

```bash
# Test health endpoint
curl http://localhost:8001/api/health

# Test posts endpoint (should return 401 without auth)
curl http://localhost:8001/api/posts

# Test feed endpoint (should return 401 without auth)
curl http://localhost:8001/api/feed/home
```

---

## 🧪 **Running Tests**

### **Run All Tests:**

```bash
cd /app/backend
pytest tests/test_posts.py -v
```

### **Run Specific Test:**

```bash
pytest tests/test_posts.py::TestPostCreation::test_create_public_post -v
```

### **Run with Coverage:**

```bash
pytest tests/test_posts.py --cov=backend.routes.posts --cov-report=html
```

---

## 🐳 **Docker Setup**

### **Build Image:**

```bash
cd /app
docker build -t pairly-backend:latest .
```

### **Run Container:**

```bash
docker run -d \
  --name pairly-backend \
  -p 8000:8000 \
  -e MONGO_URL=mongodb://host.docker.internal:27017/pairly \
  -e JWT_SECRET=your-secret-key \
  pairly-backend:latest
```

### **Check Logs:**

```bash
docker logs pairly-backend
```

### **Stop Container:**

```bash
docker stop pairly-backend
docker rm pairly-backend
```

---

## 📡 **API Usage Examples**

### **1. Create a Post**

```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"creator@example.com","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Create public post
curl -X POST http://localhost:8001/api/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My first post!",
    "media": [
      {
        "type": "image",
        "url": "https://example.s3.amazonaws.com/photo.jpg",
        "meta": {
          "mime": "image/jpeg",
          "size_bytes": 1024000
        }
      }
    ],
    "visibility": "public"
  }'
```

### **2. Get Post by ID**

```bash
curl http://localhost:8001/api/posts/{post_id}
```

### **3. Get Home Feed**

```bash
curl -X GET http://localhost:8001/api/feed/home \
  -H "Authorization: Bearer $TOKEN"
```

### **4. Get Home Feed with Pagination**

```bash
# First page
curl "http://localhost:8001/api/feed/home?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Next page (use cursor from response)
curl "http://localhost:8001/api/feed/home?cursor=2024-12-05T10:30:00.000000::507f1f77bcf86cd799439011&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### **5. Get Creator Timeline**

```bash
curl http://localhost:8001/api/feed/creator/{creator_id} \
  -H "Authorization: Bearer $TOKEN"
```

### **6. Update Post**

```bash
curl -X PATCH http://localhost:8001/api/posts/{post_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Updated post text",
    "visibility": "subscribers"
  }'
```

### **7. Delete Post (Soft Delete)**

```bash
curl -X DELETE http://localhost:8001/api/posts/{post_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔍 **Testing Subscription Gating**

### **Create Subscriber-Only Post:**

```bash
# This will fail if creator has no active subscription tiers
curl -X POST http://localhost:8001/api/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Exclusive content for subscribers!",
    "visibility": "subscribers"
  }'
```

### **Create Subscription Tier (Admin/Creator):**

```bash
# First, manually insert a subscription tier via MongoDB or create an endpoint
# Then subscriber-only posts will work
```

---

## 🔐 **Feature Flags**

Add to `.env` to control subscription feature:

```bash
# Enable subscription system (default: false)
FEATURE_SUBSCRIPTIONS=true
```

This allows dual-mode operation:
- **Credits system** (existing) - Pay per message
- **Subscription system** (new) - Monthly/yearly tiers

---

## 📊 **Database Indexes**

Phase 1 creates these indexes automatically:

```javascript
// Posts collection
db.posts.createIndex({ creator: 1, created_at: -1 })  // Creator timeline
db.posts.createIndex({ visibility: 1, created_at: -1 })  // Public feed
db.posts.createIndex({ is_archived: 1, created_at: -1 })  // Active posts

// Subscription tiers
db.subscription_tiers.createIndex({ creator_id: 1, active: 1 })
db.subscription_tiers.createIndex({ tier_id: 1 })

// User subscriptions
db.user_subscriptions.createIndex({ user_id: 1, status: 1 })
db.user_subscriptions.createIndex({ creator_id: 1, status: 1 })
db.user_subscriptions.createIndex({ stripe_subscription_id: 1 })
db.user_subscriptions.createIndex({ razorpay_subscription_id: 1 })
```

---

## 🐛 **Troubleshooting**

### **Import Errors:**

```bash
# Make sure all new models are in database.py
grep "from backend.models.post" backend/database.py
grep "from backend.models.subscription" backend/database.py
```

### **Circular Import Errors:**

```python
# Models use forward references:
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.profile import Profile
```

### **Migration Fails:**

```bash
# Check MongoDB connection
mongosh mongodb://localhost:27017/pairly

# Verify database name
python3 -c "from backend.config import settings; print(settings.MONGODB_URI)"
```

### **Tests Fail:**

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Set test environment variables
export MONGO_URL=mongodb://localhost:27017
export DB_NAME=test_pairly
export JWT_SECRET=test-secret

# Run tests
pytest backend/tests/test_posts.py -v
```

---

## 📈 **Performance Tips**

### **1. Feed Optimization:**

For production with thousands of posts, use MongoDB aggregation:

```python
# Replace find() with aggregation pipeline
pipeline = [
    {"$match": {"is_archived": False}},
    {"$sort": {"created_at": -1}},
    {"$limit": 20},
    {"$lookup": {
        "from": "profiles",
        "localField": "creator",
        "foreignField": "_id",
        "as": "creator_info"
    }}
]
```

### **2. Cursor Pagination:**

Current implementation uses timestamp + ID:
- Efficient for time-based feeds
- Handles concurrent inserts correctly
- No offset issues

### **3. Media Validation:**

Validate media BEFORE upload to S3:
- Client-side validation first
- Pre-signed URL with size limits
- Server verification after upload

---

## 🚀 **Next Steps**

1. **Test all endpoints** with Postman/curl
2. **Create subscription tiers** for creators
3. **Test subscriber-gated posts**
4. **Verify feed pagination** works correctly
5. **Run migration** on production database
6. **Deploy Docker image**

---

## 📞 **Support**

- **Migration issues**: Check `/app/backend/migrations/0001_add_post_and_subscription.py`
- **API issues**: Check `/app/backend/routes/posts.py` and `/app/backend/routes/feed.py`
- **Test failures**: Check `/app/backend/tests/test_posts.py`

---

## ✅ **Verification Checklist**

- [ ] Dependencies installed
- [ ] Migration run successfully
- [ ] Backend server restarted
- [ ] Health endpoint responds
- [ ] Can create public post
- [ ] Feed returns posts
- [ ] Cursor pagination works
- [ ] Tests pass
- [ ] Docker image builds
- [ ] CI pipeline passes

**Phase 1 is complete when all checks pass!** ✨
