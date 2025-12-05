"""
Celery Moderation Worker

Processes quarantined content asynchronously.
"""

import os
import asyncio
from celery import Celery
from datetime import datetime
import requests
from backend.services.moderation.classifier_client import (
    analyze_text,
    analyze_image,
    should_block,
    should_publish,
    ModerationEngine
)

# Celery setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
celery_app = Celery(
    "moderation_worker",
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


@celery_app.task(name="moderation.process_quarantine")
def process_quarantine_task(content_id: str, content_type: str, content_data: dict):
    """
    Process quarantined content.
    
    Args:
        content_id: ID of the content (post_id, media_id, etc.)
        content_type: "text", "image", "post"
        content_data: Dict with content details
    
    Returns:
        Decision: "publish", "remove", or "escalate"
    """
    try:
        print(f"Processing quarantine: {content_type} - {content_id}")
        
        decision = "publish"
        moderation_result = None
        
        if content_type == "text":
            text = content_data.get("text", "")
            moderation_result = analyze_text(text, engine="local")
            
            if should_block(moderation_result):
                decision = "remove"
            elif should_publish(moderation_result):
                decision = "publish"
            else:
                # Still suspicious, escalate to human
                decision = "escalate"
        
        elif content_type == "image":
            image_url = content_data.get("image_url")
            if image_url:
                # Download image
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    image_bytes = response.content
                    moderation_result = analyze_image(image_bytes, engine="google_vision")
                    
                    if should_block(moderation_result):
                        decision = "remove"
                    elif should_publish(moderation_result):
                        decision = "publish"
                    else:
                        decision = "escalate"
                else:
                    print(f"Failed to download image: {response.status_code}")
                    decision = "escalate"
        
        elif content_type == "post":
            # Post with text and/or images
            text = content_data.get("text", "")
            media_urls = content_data.get("media_urls", [])
            
            # Analyze text
            text_result = analyze_text(text, engine="local")
            
            # Analyze images
            image_results = []
            for url in media_urls[:3]:  # Limit to first 3 images
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        image_bytes = response.content
                        img_result = analyze_image(image_bytes, engine="google_vision")
                        image_results.append(img_result)
                except Exception as e:
                    print(f"Error analyzing image {url}: {e}")
            
            # Combine results - take max score
            max_score = text_result.score
            combined_categories = list(text_result.categories)
            
            for img_result in image_results:
                if img_result.score > max_score:
                    max_score = img_result.score
                combined_categories.extend(img_result.categories)
            
            combined_categories = list(set(combined_categories))
            
            # Make decision
            if max_score >= 0.85:
                decision = "remove"
            elif max_score < 0.50:
                decision = "publish"
            else:
                decision = "escalate"
            
            moderation_result = text_result  # Store primary result
        
        # Log the decision
        print(f"Quarantine decision for {content_id}: {decision} (score: {moderation_result.score if moderation_result else 'N/A'})")
        
        # Update database (async operation)
        asyncio.run(update_content_moderation_status(
            content_id=content_id,
            content_type=content_type,
            decision=decision,
            moderation_result=moderation_result.to_dict() if moderation_result else {}
        ))
        
        return {
            "content_id": content_id,
            "decision": decision,
            "moderation_result": moderation_result.to_dict() if moderation_result else {},
            "processed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        print(f"Error processing quarantine {content_id}: {e}")
        return {
            "content_id": content_id,
            "decision": "escalate",
            "error": str(e),
            "processed_at": datetime.utcnow().isoformat()
        }


async def update_content_moderation_status(
    content_id: str,
    content_type: str,
    decision: str,
    moderation_result: dict
):
    """
    Update content moderation status in database.
    
    This is a placeholder - implement actual database update logic.
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from backend.config import settings
        
        client = AsyncIOMotorClient(settings.MONGO_URL)
        db = client[settings.DB_NAME]
        
        collection_map = {
            "text": "posts",
            "image": "media",
            "post": "posts"
        }
        
        collection_name = collection_map.get(content_type, "posts")
        collection = db[collection_name]
        
        update_data = {
            "moderation_status": decision,
            "moderation_score": moderation_result.get("score", 0.0),
            "moderation_engine": moderation_result.get("engine", "unknown"),
            "moderation_categories": moderation_result.get("categories", []),
            "moderation_processed_at": datetime.utcnow()
        }
        
        if decision == "remove":
            update_data["visibility"] = "removed"
            update_data["removed_reason"] = "policy_violation"
        elif decision == "publish":
            update_data["visibility"] = "public"
        elif decision == "escalate":
            update_data["visibility"] = "quarantined"
            update_data["requires_human_review"] = True
        
        await collection.update_one(
            {"id": content_id},
            {"$set": update_data}
        )
        
        print(f"Updated {content_type} {content_id} to {decision}")
        
        client.close()
    
    except Exception as e:
        print(f"Error updating database: {e}")


@celery_app.task(name="moderation.report_metrics")
def report_metrics_task():
    """
    Periodic task to report moderation metrics to Prometheus.
    
    Run every 5 minutes.
    """
    try:
        from prometheus_client import Counter, Gauge
        
        # Define metrics
        quarantined_total = Counter(
            "moderation_quarantined_total",
            "Total content quarantined",
            ["type"]
        )
        removed_total = Counter(
            "moderation_removed_total",
            "Total content removed",
            ["type"]
        )
        published_total = Counter(
            "moderation_published_total",
            "Total content published after review"
        )
        queue_length = Gauge(
            "moderation_quarantine_queue_length",
            "Current quarantine queue length"
        )
        
        # Query Redis for queue length
        import redis
        r = redis.from_url(REDIS_URL)
        queue_len = r.llen("moderation:quarantine_queue")
        queue_length.set(queue_len)
        
        print(f"Reported metrics: queue_length={queue_len}")
        
    except Exception as e:
        print(f"Error reporting metrics: {e}")


# Celery beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    "report-metrics-every-5-minutes": {
        "task": "moderation.report_metrics",
        "schedule": 300.0,  # 5 minutes
    },
}
