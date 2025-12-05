"""
Compliance & Reporting Routes

User reporting system and admin moderation panel.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum
from backend.models.user import User, Role
from backend.routes.auth import get_current_user
from beanie import PydanticObjectId
from beanie import Document


router = APIRouter()


class ContentType(str, Enum):
    POST = "post"
    PROFILE = "profile"
    MESSAGE = "message"
    MEDIA = "media"


class ReportReason(str, Enum):
    SEXUAL_CONTENT = "sexual_content"
    NUDITY = "nudity"
    VIOLENCE = "violence"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    SPAM = "spam"
    MINOR = "minor"
    OTHER = "other"


class ReportStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationAction(str, Enum):
    REMOVE = "remove"
    DISMISS = "dismiss"
    BAN_USER = "ban_user"
    WARN_USER = "warn_user"


class Report(Document):
    id: str
    reporter_id: str
    reported_user_id: Optional[str] = None
    content_id: str
    content_type: ContentType
    reason: ReportReason
    details: str
    status: ReportStatus = ReportStatus.PENDING
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    moderator_notes: Optional[str] = None
    action_taken: Optional[ModerationAction] = None
    
    class Settings:
        name = "reports"


class ReportRequest(BaseModel):
    content_id: str
    content_type: ContentType
    reason: ReportReason
    details: str


class ReportActionRequest(BaseModel):
    action: ModerationAction
    moderator_notes: str


@router.post("/api/report")
async def submit_report(
    req: ReportRequest,
    user: User = Depends(get_current_user)
):
    """
    Submit a content report.
    
    Users can report posts, profiles, messages, or media that violate policy.
    """
    try:
        # Create report
        report = Report(
            id=str(PydanticObjectId()),
            reporter_id=user.id,
            content_id=req.content_id,
            content_type=req.content_type,
            reason=req.reason,
            details=req.details,
            status=ReportStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        await report.insert()
        
        # Log audit event
        from backend.services.audit import log_event
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="content_reported",
            details={
                "report_id": report.id,
                "content_id": req.content_id,
                "content_type": req.content_type,
                "reason": req.reason
            },
            severity="warning"
        )
        
        return {
            "report_id": report.id,
            "status": "submitted",
            "message": "Thank you for your report. Our moderation team will review it within 24-48 hours."
        }
    
    except Exception as e:
        print(f"Error submitting report: {e}")
        raise HTTPException(500, "Failed to submit report")


@router.get("/api/admin/reports")
async def get_reports(
    status: Optional[ReportStatus] = Query(None),
    content_type: Optional[ContentType] = Query(None),
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    user: User = Depends(get_current_user)
):
    """
    Get reports for admin review.
    
    Admin only. Returns paginated list of reports.
    """
    if user.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    try:
        # Build query
        query = {}
        if status:
            query["status"] = status
        if content_type:
            query["content_type"] = content_type
        
        # Get reports
        reports = await Report.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
        
        return {
            "reports": [
                {
                    "id": r.id,
                    "reporter_id": r.reporter_id,
                    "reported_user_id": r.reported_user_id,
                    "content_id": r.content_id,
                    "content_type": r.content_type,
                    "reason": r.reason,
                    "details": r.details,
                    "status": r.status,
                    "created_at": r.created_at.isoformat(),
                    "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                    "reviewed_by": r.reviewed_by,
                    "moderator_notes": r.moderator_notes,
                    "action_taken": r.action_taken
                }
                for r in reports
            ],
            "limit": limit,
            "skip": skip,
            "total": await Report.find(query).count()
        }
    
    except Exception as e:
        print(f"Error fetching reports: {e}")
        raise HTTPException(500, "Failed to fetch reports")


@router.post("/api/admin/reports/{report_id}/action")
async def take_moderation_action(
    report_id: str,
    req: ReportActionRequest,
    user: User = Depends(get_current_user)
):
    """
    Take action on a report.
    
    Admin only. Actions: remove, dismiss, ban_user, warn_user.
    """
    if user.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    
    try:
        # Get report
        report = await Report.find_one(Report.id == report_id)
        if not report:
            raise HTTPException(404, "Report not found")
        
        # Update report status
        report.status = ReportStatus.RESOLVED if req.action != ModerationAction.DISMISS else ReportStatus.DISMISSED
        report.reviewed_at = datetime.utcnow()
        report.reviewed_by = user.id
        report.moderator_notes = req.moderator_notes
        report.action_taken = req.action
        
        await report.save()
        
        # Take action on content/user
        if req.action == ModerationAction.REMOVE:
            # Remove the content
            await remove_content(report.content_id, report.content_type)
        
        elif req.action == ModerationAction.BAN_USER:
            # Ban the reported user
            if report.reported_user_id:
                await ban_user(report.reported_user_id, reason=f"Report: {report.reason}")
        
        elif req.action == ModerationAction.WARN_USER:
            # Send warning to user
            if report.reported_user_id:
                await warn_user(report.reported_user_id, reason=f"Report: {report.reason}")
        
        # Log audit event
        from backend.services.audit import log_event
        await log_event(
            actor_user_id=user.id,
            actor_ip=None,
            action="moderation_action_taken",
            details={
                "report_id": report_id,
                "action": req.action,
                "content_id": report.content_id
            },
            severity="info"
        )
        
        return {
            "report_id": report_id,
            "action": req.action,
            "status": report.status,
            "message": f"Action '{req.action}' completed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error taking moderation action: {e}")
        raise HTTPException(500, "Failed to take moderation action")


async def remove_content(content_id: str, content_type: ContentType):
    """
    Remove content by ID and type.
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from backend.config import settings
        
        client = AsyncIOMotorClient(settings.MONGO_URL)
        db = client[settings.DB_NAME]
        
        collection_map = {
            ContentType.POST: "posts",
            ContentType.PROFILE: "profiles",
            ContentType.MESSAGE: "messages",
            ContentType.MEDIA: "media"
        }
        
        collection_name = collection_map.get(content_type)
        if collection_name:
            collection = db[collection_name]
            await collection.update_one(
                {"id": content_id},
                {"$set": {
                    "visibility": "removed",
                    "removed_reason": "policy_violation",
                    "removed_at": datetime.utcnow()
                }}
            )
        
        client.close()
    except Exception as e:
        print(f"Error removing content: {e}")


async def ban_user(user_id: str, reason: str):
    """
    Ban a user.
    """
    try:
        target_user = await User.get(user_id)
        if target_user:
            target_user.is_suspended = True
            await target_user.save()
            
            # Log event
            from backend.services.audit import log_event
            await log_event(
                actor_user_id=None,
                actor_ip=None,
                action="user_banned",
                details={"user_id": user_id, "reason": reason},
                severity="critical"
            )
    except Exception as e:
        print(f"Error banning user: {e}")


async def warn_user(user_id: str, reason: str):
    """
    Send warning to user.
    """
    try:
        # In production, send email/notification
        # For now, log the warning
        from backend.services.audit import log_event
        await log_event(
            actor_user_id=user_id,
            actor_ip=None,
            action="user_warned",
            details={"user_id": user_id, "reason": reason},
            severity="warning"
        )
        
        print(f"Warning sent to user {user_id}: {reason}")
    except Exception as e:
        print(f"Error warning user: {e}")
