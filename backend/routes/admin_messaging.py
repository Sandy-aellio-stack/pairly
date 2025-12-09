from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime, timezone
from backend.models.message_v2 import MessageV2, ModerationStatus, MessageStatus
from backend.services.admin_rbac import AdminRBACService
from backend.services.admin_logging import AdminLoggingService
from backend.models.user import User

logger = logging.getLogger('routes.admin_messaging')

router = APIRouter(prefix="/api/admin/messages", tags=["Admin - Messaging"])

class ModerateMessageRequest(BaseModel):
    moderation_status: ModerationStatus
    reason: Optional[str] = None

class MessageSearchResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    message_type: str
    status: str
    moderation_status: str
    created_at: str

@router.get("/search")
async def search_messages(
    user_id: Optional[str] = Query(None, description="Filter by user (sender or receiver)"),
    sender_id: Optional[str] = Query(None, description="Filter by sender"),
    receiver_id: Optional[str] = Query(None, description="Filter by receiver"),
    moderation_status: Optional[ModerationStatus] = Query(None),
    limit: int = Query(50, le=200),
    skip: int = Query(0, ge=0),
    admin: User = Depends(AdminRBACService.require_permission("moderation.view"))
):
    """
    Search and filter messages (admin only)
    Requires: moderation.view permission
    """
    query = {"is_deleted": False}
    
    # Build query based on filters
    if user_id:
        query["$or"] = [
            {"sender_id": user_id},
            {"receiver_id": user_id}
        ]
    
    if sender_id and not user_id:
        query["sender_id"] = sender_id
    
    if receiver_id and not user_id:
        query["receiver_id"] = receiver_id
    
    if moderation_status:
        query["moderation_status"] = moderation_status
    
    # Execute query
    messages = await MessageV2.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
    total = await MessageV2.find(query).count()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="search_messages",
        target_type="message",
        metadata={
            "filters": {
                "user_id": user_id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "moderation_status": moderation_status.value if moderation_status else None
            },
            "results": len(messages)
        }
    )
    
    return {
        "messages": [
            MessageSearchResponse(
                id=msg.id,
                sender_id=msg.sender_id,
                receiver_id=msg.receiver_id,
                content=msg.content[:200],  # Truncate for privacy
                message_type=msg.message_type.value,
                status=msg.status.value,
                moderation_status=msg.moderation_status.value,
                created_at=msg.created_at.isoformat()
            )
            for msg in messages
        ],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "limit": limit
    }

@router.get("/conversation/{user1_id}/{user2_id}")
async def view_conversation(
    user1_id: str,
    user2_id: str,
    limit: int = Query(100, le=500),
    admin: User = Depends(AdminRBACService.require_permission("moderation.view"))
):
    """
    View full conversation between two users (admin only)
    Requires: moderation.view permission
    """
    messages = await MessageV2.find(
        MessageV2.is_deleted == False,
        (
            ((MessageV2.sender_id == user1_id) & (MessageV2.receiver_id == user2_id)) |
            ((MessageV2.sender_id == user2_id) & (MessageV2.receiver_id == user1_id))
        )
    ).sort("-created_at").limit(limit).to_list()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="view_conversation",
        target_type="message",
        metadata={
            "user1_id": user1_id,
            "user2_id": user2_id,
            "message_count": len(messages)
        }
    )
    
    return {
        "messages": [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "message_type": msg.message_type.value,
                "status": msg.status.value,
                "moderation_status": msg.moderation_status.value,
                "created_at": msg.created_at.isoformat(),
                "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                "read_at": msg.read_at.isoformat() if msg.read_at else None
            }
            for msg in reversed(messages)
        ],
        "total": len(messages)
    }

@router.post("/{message_id}/moderate")
async def moderate_message(
    message_id: str,
    request: ModerateMessageRequest,
    admin: User = Depends(AdminRBACService.require_permission("moderation.action"))
):
    """
    Moderate a message (flag, block, or approve)
    Requires: moderation.action permission
    """
    message = await MessageV2.find_one(MessageV2.id == message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    old_status = message.moderation_status
    message.moderation_status = request.moderation_status
    message.updated_at = datetime.now(timezone.utc)
    await message.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="moderate_message",
        target_type="message",
        target_id=message_id,
        before_state={"moderation_status": old_status.value},
        after_state={"moderation_status": request.moderation_status.value},
        reason=request.reason,
        metadata={
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id
        },
        severity="warning" if request.moderation_status == ModerationStatus.BLOCKED else "info"
    )
    
    return {
        "success": True,
        "message_id": message_id,
        "moderation_status": request.moderation_status.value,
        "message": "Message moderation updated"
    }

@router.get("/stats/overview")
async def get_messaging_stats(
    admin: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """
    Get overall messaging statistics (admin only)
    Requires: analytics.view permission
    """
    total_messages = await MessageV2.find().count()
    
    # Status breakdown
    sent = await MessageV2.find(MessageV2.status == MessageStatus.SENT).count()
    delivered = await MessageV2.find(MessageV2.status == MessageStatus.DELIVERED).count()
    read = await MessageV2.find(MessageV2.status == MessageStatus.READ).count()
    failed = await MessageV2.find(MessageV2.status == MessageStatus.FAILED).count()
    
    # Moderation breakdown
    pending = await MessageV2.find(MessageV2.moderation_status == ModerationStatus.PENDING).count()
    approved = await MessageV2.find(MessageV2.moderation_status == ModerationStatus.APPROVED).count()
    flagged = await MessageV2.find(MessageV2.moderation_status == ModerationStatus.FLAGGED).count()
    blocked = await MessageV2.find(MessageV2.moderation_status == ModerationStatus.BLOCKED).count()
    
    deleted = await MessageV2.find(MessageV2.is_deleted == True).count()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="view_messaging_stats",
        target_type="analytics",
        metadata={"total_messages": total_messages}
    )
    
    return {
        "total_messages": total_messages,
        "status_breakdown": {
            "sent": sent,
            "delivered": delivered,
            "read": read,
            "failed": failed
        },
        "moderation_breakdown": {
            "pending": pending,
            "approved": approved,
            "flagged": flagged,
            "blocked": blocked
        },
        "deleted": deleted
    }

@router.get("/export")
async def export_messages(
    user_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(1000, le=5000),
    admin: User = Depends(AdminRBACService.require_permission("analytics.export"))
):
    """
    Export message data for analysis (admin only)
    Requires: analytics.export permission
    """
    query = {}
    
    if user_id:
        query["$or"] = [
            {"sender_id": user_id},
            {"receiver_id": user_id}
        ]
    
    if start_date:
        if "created_at" not in query:
            query["created_at"] = {}
        query["created_at"]["$gte"] = datetime.fromisoformat(start_date)
    
    if end_date:
        if "created_at" not in query:
            query["created_at"] = {}
        query["created_at"]["$lte"] = datetime.fromisoformat(end_date)
    
    messages = await MessageV2.find(query).limit(limit).to_list()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="export_messages",
        target_type="message",
        metadata={
            "filters": {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date
            },
            "exported_count": len(messages)
        },
        severity="warning"  # Data export is sensitive
    )
    
    return {
        "messages": [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "message_type": msg.message_type.value,
                "status": msg.status.value,
                "moderation_status": msg.moderation_status.value,
                "credits_cost": msg.credits_cost,
                "created_at": msg.created_at.isoformat(),
                "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                "read_at": msg.read_at.isoformat() if msg.read_at else None,
                "is_deleted": msg.is_deleted
            }
            for msg in messages
        ],
        "total_exported": len(messages),
        "export_timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.delete("/{message_id}/hard-delete")
@require_permission("super_admin")
async def hard_delete_message(
    message_id: str,
    admin: User = Depends(require_permission("super_admin"))
):
    """
    Permanently delete a message (super admin only)
    Requires: super_admin role
    """
    message = await MessageV2.find_one(MessageV2.id == message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="hard_delete_message",
        target_type="message",
        target_id=message_id,
        metadata={
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content_preview": message.content[:50]
        },
        severity="critical"
    )
    
    await message.delete()
    
    return {
        "success": True,
        "message": "Message permanently deleted"
    }
