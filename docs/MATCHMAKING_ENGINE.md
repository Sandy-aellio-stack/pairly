# Matchmaking Engine Documentation

## Overview

The Matchmaking Engine is a sophisticated recommendation system that generates personalized match suggestions for users based on demographic preferences, behavioral signals, and similarity scoring.

**Status**: ✅ Fully Integrated and Tested

---

## Architecture

### Components

1. **User Preferences Model** (`backend/models/user_preferences.py`)
   - Stores user matching criteria and behavioral signals
   - Tracks engagement metrics and activity patterns

2. **Match Feedback Model** (`backend/models/match_feedback.py`)
   - Records user reactions (like, skip, super_like, block)
   - Tracks position and score at time of recommendation

3. **Match Recommendation Model** (`backend/models/match_recommendation.py`)
   - Caches pre-computed recommendations
   - 24-hour TTL with metadata and performance metrics

4. **Scoring Engine** (`backend/services/matchmaking/scoring_engine.py`)
   - Multi-factor compatibility scoring algorithm
   - Haversine distance calculation for location filtering

5. **Recommendation Pipeline** (`backend/services/matchmaking/recommendation_pipeline.py`)
   - Multi-stage recommendation generation
   - Hard filters, soft ranking, diversity injection, cold-start handling

6. **Profile Embedder** (`backend/services/matchmaking/profile_embedder.py`)
   - Converts user profiles to 128-dimensional vectors
   - Cosine similarity calculation for ML-based scoring

7. **Background Worker** (`backend/services/matchmaking/recommendation_worker.py`)
   - Celery tasks for batch and on-demand recommendation generation
   - Graceful degradation if worker unavailable

---

## Scoring Algorithm

### Formula

```
Total Score = (0.25 × demographic) + (0.30 × interests) + (0.20 × behavioral) + (0.25 × ml_similarity)
```

### Components

#### 1. Demographic Compatibility (0-1, weight 0.25)
- **Age compatibility** (0-0.4): Preference match with penalty for large gaps
- **Gender preference** (0-0.3): Match with preferred genders
- **Relationship goals** (0-0.3): Alignment of dating intentions

#### 2. Interest Overlap (0-1, weight 0.30)
- **Jaccard similarity**: `|intersection| / |union|` of interest sets
- Neutral score (0.5) for users with no interests specified

#### 3. Behavioral Compatibility (0-1, weight 0.20)
- **Activity level alignment** (0-0.5): Similar engagement patterns
- **Recency bonus** (0-0.5):
  - Active within 24h: +0.5
  - Active within 72h: +0.3
  - Active within 7d: +0.1

#### 4. ML Similarity (0-1, weight 0.25)
- Profile embedding cosine similarity
- 128-dimensional feature vector encoding

---

## Recommendation Pipeline

### Stage 1: Hard Filtering
Candidates must pass ALL filters:
- Not the user themselves
- Age within user's min/max range
- Distance within max_distance_km (if locations available)
- Not previously blocked or skipped
- Active within last 30 days
- Limit: 500 candidates max for performance

### Stage 2: Score Calculation
- Calculate full compatibility score for each candidate
- Generate match score breakdown and human-readable reasons

### Stage 3: Soft Filtering & Ranking
- Remove candidates below minimum threshold (0.3)
- Sort by score descending

### Stage 4: Diversity Injection
- Top 80% from highest scores
- Bottom 20% sampled from next tier for variety
- Prevents repetitive, homogeneous recommendations

### Stage 5: Cold-Start Handling
- If < 10 recommendations, boost with popular/active users
- Helps new users with sparse data

### Stage 6: Caching
- Store recommendations in database with 24-hour TTL
- Return cached results unless force_refresh requested
- Computation time tracked for performance monitoring

---

## API Endpoints

### 1. Get User Preferences
```
GET /api/matchmaking/preferences
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "string",
  "min_age": 18,
  "max_age": 99,
  "preferred_genders": ["male", "female"],
  "max_distance_km": 50,
  "interests": ["hiking", "movies"],
  "lifestyle_tags": ["vegan", "active"],
  "relationship_goals": ["serious"],
  "location_city": "New York",
  "engagement_score": 42.5
}
```

### 2. Update User Preferences
```
PUT /api/matchmaking/preferences
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "min_age": 25,
  "max_age": 35,
  "preferred_genders": ["male"],
  "max_distance_km": 30,
  "interests": ["hiking", "travel", "photography"],
  "lifestyle_tags": ["active", "foodie"],
  "relationship_goals": ["serious"],
  "latitude": 40.7128,
  "longitude": -74.0060,
  "location_city": "New York"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preferences updated"
}
```

**Note**: Triggers async recommendation refresh (if worker available)

### 3. Get Recommendations
```
GET /api/matchmaking/recommendations?limit=20&skip=0&force_refresh=false
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit`: Number of recommendations (max 50, default 20)
- `skip`: Pagination offset (default 0)
- `force_refresh`: Bypass cache (default false)

**Response:**
```json
{
  "recommendations": [
    {
      "user_id": "693366ec8bed7d7319a02817",
      "score": 0.82,
      "breakdown": {
        "demographic": 0.85,
        "interests": 0.75,
        "behavioral": 0.80,
        "ml_similarity": 0.88,
        "total": 0.82
      },
      "reasons": [
        "Great age and lifestyle match",
        "Shared interests",
        "Active user"
      ]
    }
  ],
  "total": 1,
  "limit": 20,
  "skip": 0,
  "generated_at": "2025-12-05T23:15:07.183897",
  "algorithm_version": "v1",
  "computation_time_ms": 10.45
}
```

### 4. Submit Feedback
```
POST /api/matchmaking/feedback
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "target_user_id": "693366ec8bed7d7319a02817",
  "feedback_type": "like",
  "match_score": 0.82,
  "position": 0
}
```

**Feedback Types:**
- `like`: Positive signal
- `skip`: Negative signal
- `super_like`: Strong positive signal
- `block`: Exclude from future recommendations

**Response:**
```json
{
  "success": true,
  "feedback_id": "69336785ca268b2a4a0136d3",
  "feedback_type": "like"
}
```

**Effect:**
- Updates user engagement score
- Excludes blocked/skipped users from future recommendations
- Logged for future ML model training

### 5. Get Feedback Stats
```
GET /api/matchmaking/feedback/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_likes": 42,
  "total_skips": 18,
  "engagement_score": 156.0,
  "total_messages_sent": 25,
  "total_calls_made": 3
}
```

### 6. Admin: Recompute Recommendations
```
POST /api/admin/matchmaking/recompute
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_ids": ["user1", "user2"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Queued recomputation for 2 users"
}
```

### 7. Admin: Debug User Recommendations
```
GET /api/admin/matchmaking/debug/{user_id}
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "user_id": "string",
  "preferences": {
    "age_range": "25-35",
    "max_distance_km": 30,
    "interests": ["hiking", "movies"],
    "relationship_goals": ["serious"],
    "engagement_score": 42.5
  },
  "cached_recommendations": {
    "count": 15,
    "generated_at": "2025-12-05T23:00:00",
    "expires_at": "2025-12-06T23:00:00",
    "computation_time_ms": 12.3
  },
  "recent_feedback": [
    {
      "target_user_id": "string",
      "feedback_type": "like",
      "timestamp": "2025-12-05T22:45:00"
    }
  ]
}
```

---

## Database Schema

### UserPreferences Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  min_age: Number (default: 18),
  max_age: Number (default: 99),
  preferred_genders: Array<String>,
  max_distance_km: Number (default: 50),
  interests: Array<String>,
  lifestyle_tags: Array<String>,
  relationship_goals: Array<String>,
  latitude: Number,
  longitude: Number,
  location_city: String,
  total_likes: Number (default: 0),
  total_skips: Number (default: 0),
  total_messages_sent: Number (default: 0),
  total_calls_made: Number (default: 0),
  engagement_score: Number (default: 0.0),
  last_active_at: DateTime,
  created_at: DateTime,
  updated_at: DateTime
}
```

### MatchFeedback Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  target_user_id: ObjectId,
  feedback_type: String,
  match_score: Number,
  position_in_list: Number,
  timestamp: DateTime
}
```

### MatchRecommendation Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  recommendations: Array<Object>,
  total_candidates: Number,
  algorithm_version: String,
  generated_at: DateTime,
  expires_at: DateTime,
  computation_time_ms: Number
}
```

---

## Configuration

### Tunable Parameters

**Scoring Weights** (`scoring_engine.py`):
```python
WEIGHTS = {
    "demographic": 0.25,
    "interests": 0.30,
    "behavioral": 0.20,
    "ml_similarity": 0.25
}
```

**Pipeline Configuration** (`recommendation_pipeline.py`):
```python
DEFAULT_RECOMMENDATION_COUNT = 50
CACHE_TTL_HOURS = 24
MIN_SCORE_THRESHOLD = 0.3
DIVERSITY_FACTOR = 0.2
```

---

## Testing

### Manual Testing Checklist
- [x] Create user and get default preferences
- [x] Update preferences with various combinations
- [x] Generate recommendations with multiple users
- [x] Submit feedback (like, skip, block)
- [x] Verify engagement score updates
- [x] Test pagination (limit/skip)
- [x] Test force_refresh flag
- [x] Admin debug endpoint
- [x] Graceful degradation without Celery/Redis

---

## Summary

The Matchmaking Engine is a production-ready, multi-factor recommendation system that:
- ✅ Supports complex user preferences
- ✅ Tracks behavioral signals
- ✅ Uses weighted scoring algorithm
- ✅ Implements hard filtering, soft ranking, diversity, and cold-start logic
- ✅ Provides on-demand and batch recommendation generation
- ✅ Caches results with 24-hour TTL
- ✅ Exposes comprehensive APIs
- ✅ Gracefully degrades without background worker
- ✅ Fully tested and integrated

**Files Created:**
- `backend/models/user_preferences.py`
- `backend/models/match_feedback.py`
- `backend/models/match_recommendation.py`
- `backend/routes/matchmaking.py`
- `backend/services/matchmaking/scoring_engine.py`
- `backend/services/matchmaking/recommendation_pipeline.py`
- `backend/services/matchmaking/profile_embedder.py`
- `backend/services/matchmaking/recommendation_worker.py`
- `backend/services/matchmaking/__init__.py`
- `backend/tests/test_matchmaking.py`
- `docs/MATCHMAKING_ENGINE.md`
