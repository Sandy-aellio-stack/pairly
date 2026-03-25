"""
Luveloop Notifications API

All notification *model* code lives in backend.models.tb_notification.
This module only contains routing logic.

IMPORTANT — route ordering:
  Static routes (/unread-count, /mark-all-read) MUST be registered BEFORE
  parameterised routes (/{notification_id}/...) to prevent FastAPI from
  treating the literal string as a path variable.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from backend.models.tb_user import TBUser
from backend.models.tb_notification import TBNotification
from backend.routes.tb_auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Luveloop Notifications"])


# ---------------------------------------------------------------------------
# Static routes first (must precede /{notification_id} routes)
# ---------------------------------------------------------------------------

@router.get("/unread-count")
async def get_unread_count(user: TBUser = Depends(get_current_user)):
    """Get count of unread notifications."""
    count = await TBNotification.find(
        {"user_id": str(user.id), "is_read": False}
    ).count()
    return {"count": count}


@router.post("/mark-all-read")
async def mark_all_as_read(user: TBUser = Depends(get_current_user)):
    """Mark all notifications as read."""
    await TBNotification.find(
        {"user_id": str(user.id), "is_read": False}
    ).update({"$set": {"is_read": True}})
    return {"success": True}


@router.delete("")
async def delete_all_notifications(user: TBUser = Depends(get_current_user)):
    """Delete ALL notifications for the current user."""
    result = await TBNotification.find({"user_id": str(user.id)}).delete()
    deleted_count = result.deleted_count if result else 0
    return {"success": True, "deleted": deleted_count}


# ---------------------------------------------------------------------------
# Collection endpoints
# ---------------------------------------------------------------------------

@router.get("")
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    user: TBUser = Depends(get_current_user),
):
    """Get user's notifications."""
    query: dict = {"user_id": str(user.id)}
    if unread_only:
        query["is_read"] = False

    notifications = (
        await TBNotification.find(query).sort("-created_at").limit(limit).to_list()
    )

    return {
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "type": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }


# ---------------------------------------------------------------------------
# Per-notification endpoints (parameterised — keep AFTER static routes)
# ---------------------------------------------------------------------------

@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user: TBUser = Depends(get_current_user),
):
    """Mark a single notification as read."""
    notification = await TBNotification.find_one(
        {"id": notification_id, "user_id": str(user.id)}
    )
    if notification:
        notification.is_read = True
        await notification.save()
        return {"success": True}
    return {"success": False, "message": "Notification not found"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user: TBUser = Depends(get_current_user),
):
    """Delete a single notification."""
    notification = await TBNotification.find_one(
        {"id": notification_id, "user_id": str(user.id)}
    )
    if notification:
        await notification.delete()
        return {"success": True}
    return {"success": False, "message": "Notification not found"}


# ---------------------------------------------------------------------------
# Internal helper — used by other services to create notifications
# ---------------------------------------------------------------------------

async def create_notification(
    user_id: str,
    title: str,
    body: str,
    notification_type: str = "general",
) -> TBNotification:
    """Create and persist a notification. Safe to call from any service."""
    notification = TBNotification(
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type,
    )
    await notification.insert()
    return notification
