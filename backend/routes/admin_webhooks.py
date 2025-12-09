from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from backend.models.user import User
from backend.models.webhook_event import WebhookEvent, WebhookEventStatus, WebhookDLQ
from backend.routes.auth import get_current_user
from backend.services.webhooks import get_webhook_processor
import logging

logger = logging.getLogger('routes.admin_webhooks')

router = APIRouter(prefix="/api/admin/webhooks", tags=["admin-webhooks"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RetryWebhookRequest(BaseModel):
    """Request to retry a webhook"""
    webhook_event_id: str


# ============================================================================
# Helper Functions
# ============================================================================

def check_admin_access(user: User):
    """Check if user has admin access"""
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")


# ============================================================================
# Admin Webhook Endpoints
# ============================================================================

@router.get("/list")
async def list_webhooks(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    provider: Optional[str] = None,
    status: Optional[str] = None,
    event_type: Optional[str] = None
):
    """
    List all webhook events with filtering.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    # Build query
    query_filters = []
    
    if provider:
        query_filters.append(WebhookEvent.provider == provider)
    
    if status:
        try:
            query_filters.append(WebhookEvent.status == WebhookEventStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    
    if event_type:
        query_filters.append(WebhookEvent.event_type == event_type)
    
    # Execute query
    skip = (page - 1) * limit
    
    if query_filters:
        from functools import reduce
        import operator
        combined_query = reduce(operator.and_, query_filters)
        webhooks = await WebhookEvent.find(combined_query).sort("-created_at").skip(skip).limit(limit).to_list()
        total = await WebhookEvent.find(combined_query).count()
    else:
        webhooks = await WebhookEvent.find_all().sort("-created_at").skip(skip).limit(limit).to_list()
        total = await WebhookEvent.find_all().count()
    
    logger.info(
        f"Admin listed webhooks",
        extra={
            "admin_user_id": str(user.id),
            "filters": {"provider": provider, "status": status, "page": page},
            "results": len(webhooks)
        }
    )
    
    return {
        "webhooks": [wh.to_dict() for wh in webhooks],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }


@router.post("/retry")
async def retry_webhook(
    req: RetryWebhookRequest,
    user: User = Depends(get_current_user)
):
    """
    Manually retry a failed webhook event.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    processor = get_webhook_processor(mock_mode=True)
    success, message = await processor.retry_webhook_event(req.webhook_event_id)
    
    if not success:
        raise HTTPException(400, message)
    
    logger.info(
        f"Admin retried webhook",
        extra={
            "admin_user_id": str(user.id),
            "webhook_event_id": req.webhook_event_id
        }
    )
    
    return {
        "success": True,
        "message": message,
        "webhook_event_id": req.webhook_event_id
    }


@router.get("/pending")
async def get_pending_webhooks(
    user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get all pending webhook events.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    pending_webhooks = await WebhookEvent.find(
        WebhookEvent.status == WebhookEventStatus.PENDING
    ).sort("-created_at").limit(limit).to_list()
    
    return {
        "count": len(pending_webhooks),
        "webhooks": [wh.to_dict() for wh in pending_webhooks]
    }


@router.get("/failed")
async def get_failed_webhooks(
    user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get all failed webhook events.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    failed_webhooks = await WebhookEvent.find(
        WebhookEvent.status == WebhookEventStatus.FAILED
    ).sort("-created_at").limit(limit).to_list()
    
    return {
        "count": len(failed_webhooks),
        "webhooks": [wh.to_dict() for wh in failed_webhooks]
    }


@router.get("/stats")
async def get_webhook_stats(
    user: User = Depends(get_current_user),
    provider: Optional[str] = None
):
    """
    Get webhook statistics.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    # Build query
    query_filter = WebhookEvent.provider == provider if provider else None
    
    # Get webhooks
    if query_filter:
        webhooks = await WebhookEvent.find(query_filter).to_list()
    else:
        webhooks = await WebhookEvent.find_all().to_list()
    
    # Calculate stats
    total_webhooks = len(webhooks)
    processed = sum(1 for wh in webhooks if wh.status == WebhookEventStatus.PROCESSED)
    failed = sum(1 for wh in webhooks if wh.status == WebhookEventStatus.FAILED)
    pending = sum(1 for wh in webhooks if wh.status == WebhookEventStatus.PENDING)
    retrying = sum(1 for wh in webhooks if wh.status == WebhookEventStatus.RETRYING)
    
    # Count by provider
    stripe_count = sum(1 for wh in webhooks if wh.provider == "stripe")
    razorpay_count = sum(1 for wh in webhooks if wh.provider == "razorpay")
    
    # Count by event type
    from collections import Counter
    event_types = Counter(wh.event_type for wh in webhooks)
    
    return {
        "total_webhooks": total_webhooks,
        "by_status": {
            "processed": processed,
            "failed": failed,
            "pending": pending,
            "retrying": retrying
        },
        "by_provider": {
            "stripe": stripe_count,
            "razorpay": razorpay_count
        },
        "by_event_type": dict(event_types.most_common(10)),
        "success_rate": round(processed / total_webhooks * 100, 2) if total_webhooks > 0 else 0
    }


@router.get("/dlq")
async def get_dlq_entries(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    resolved: Optional[bool] = None
):
    """
    Get Dead Letter Queue entries.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    # Build query
    skip = (page - 1) * limit
    
    if resolved is not None:
        dlq_entries = await WebhookDLQ.find(
            WebhookDLQ.resolved == resolved
        ).sort("-created_at").skip(skip).limit(limit).to_list()
        total = await WebhookDLQ.find(WebhookDLQ.resolved == resolved).count()
    else:
        dlq_entries = await WebhookDLQ.find_all().sort("-created_at").skip(skip).limit(limit).to_list()
        total = await WebhookDLQ.find_all().count()
    
    return {
        "dlq_entries": [
            {
                "id": str(entry.id),
                "webhook_event_id": entry.webhook_event_id,
                "event_id": entry.event_id,
                "provider": entry.provider,
                "event_type": entry.event_type,
                "error_reason": entry.error_reason,
                "retry_count": entry.retry_count,
                "max_retries": entry.max_retries,
                "can_retry": entry.can_retry(),
                "resolved": entry.resolved,
                "created_at": entry.created_at.isoformat()
            }
            for entry in dlq_entries
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }


@router.get("/event/{webhook_event_id}")
async def get_webhook_event(
    webhook_event_id: str,
    user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific webhook event.
    
    Admin only endpoint.
    """
    check_admin_access(user)
    
    webhook_event = await WebhookEvent.find_one(WebhookEvent.id == webhook_event_id)
    
    if not webhook_event:
        raise HTTPException(404, f"Webhook event not found: {webhook_event_id}")
    
    # Get DLQ entry if exists
    dlq_entry = await WebhookDLQ.find_one(
        WebhookDLQ.webhook_event_id == webhook_event_id
    )
    
    result = {
        "webhook_event": webhook_event.to_dict(),
        "raw_payload": webhook_event.raw_payload,
        "signature_header": webhook_event.signature_header,
        "dlq_entry": None
    }
    
    if dlq_entry:
        result["dlq_entry"] = {
            "id": str(dlq_entry.id),
            "error_reason": dlq_entry.error_reason,
            "retry_count": dlq_entry.retry_count,
            "can_retry": dlq_entry.can_retry(),
            "resolved": dlq_entry.resolved
        }
    
    return result
