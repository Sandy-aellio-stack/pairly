"""Celery worker for batch recommendation generation."""

import os
from celery import Celery
from datetime import datetime, timedelta

from backend.models.user import User
from backend.services.matchmaking.recommendation_pipeline import RecommendationPipeline

# Celery setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
celery_app = Celery(
    "recommendation_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="matchmaking.generate_batch")
def generate_batch_recommendations():
    """
    Batch job to generate recommendations for all active users.
    
    Runs daily to pre-compute recommendations.
    """
    import asyncio
    asyncio.run(_generate_batch())


async def _generate_batch():
    """Async implementation of batch generation."""
    try:
        print("\U0001f4cd Starting batch recommendation generation...")
        
        # Get active users (active in last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users = await User.find().limit(1000).to_list()
        
        count = 0
        for user in active_users:
            try:
                await RecommendationPipeline.generate_recommendations(
                    user_id=user.id,
                    force_refresh=True
                )
                count += 1
                
                if count % 10 == 0:
                    print(f"\u2705 Generated recommendations for {count} users")
            
            except Exception as e:
                print(f"\u274c Error for user {user.id}: {e}")
                continue
        
        print(f"\U0001f389 Batch complete: {count} users processed")
    
    except Exception as e:
        print(f"\u274c Batch generation error: {e}")


@celery_app.task(name="matchmaking.refresh_user")
def refresh_user_recommendations(user_id: str):
    """Refresh recommendations for a single user."""
    import asyncio
    asyncio.run(_refresh_user(user_id))


async def _refresh_user(user_id: str):
    """Async implementation of user refresh."""
    from beanie import PydanticObjectId
    
    try:
        await RecommendationPipeline.generate_recommendations(
            user_id=PydanticObjectId(user_id),
            force_refresh=True
        )
        print(f"\u2705 Refreshed recommendations for user {user_id}")
    except Exception as e:
        print(f"\u274c Error refreshing user {user_id}: {e}")


# Celery beat schedule
celery_app.conf.beat_schedule = {
    "generate-recommendations-daily": {
        "task": "matchmaking.generate_batch",
        "schedule": 86400.0,  # 24 hours
    },
}
