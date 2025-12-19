from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import Field
import uuid

from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["TrueBond Notifications"])


class TBNotification(Document):
    """User notification"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    body: str
    notification_type: str = "general"  # general, match, message, credit, system
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tb_notifications"


@router.get("")
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    user: TBUser = Depends(get_current_user)
):
    """Get user's notifications"""
    query = {"user_id": str(user.id)}
    if unread_only:
        query["is_read"] = False
    
    notifications = await TBNotification.find(query).sort("-created_at").limit(limit).to_list()
    
    return {
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "type": n.notification_type,
                "isRead": n.is_read,
                "createdAt": n.created_at.isoformat()
            }
            for n in notifications
        ]
    }


@router.get("/unread-count")
async def get_unread_count(
    user: TBUser = Depends(get_current_user)
):
    """Get count of unread notifications"""
    count = await TBNotification.find(
        TBNotification.user_id == str(user.id),
        TBNotification.is_read == False
    ).count()
    
    return {"count": count}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user: TBUser = Depends(get_current_user)
):
    """Mark notification as read"""
    notification = await TBNotification.find_one(
        TBNotification.id == notification_id,
        TBNotification.user_id == str(user.id)
    )
    
    if notification:
        notification.is_read = True
        await notification.save()
        return {"success": True}
    
    return {"success": False, "message": "Notification not found"}


@router.post("/mark-all-read")
async def mark_all_as_read(
    user: TBUser = Depends(get_current_user)
):
    """Mark all notifications as read"""
    await TBNotification.find(
        TBNotification.user_id == str(user.id),
        TBNotification.is_read == False
    ).update({"$set": {"is_read": True}})
    
    return {"success": True}


# Helper function to create notifications
async def create_notification(
    user_id: str,
    title: str,
    body: str,
    notification_type: str = "general"
):
    """Create a new notification for a user"""
    notification = TBNotification(
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type
    )
    await notification.insert()
    return notification
