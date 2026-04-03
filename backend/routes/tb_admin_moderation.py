from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import datetime, timezone
from beanie import PydanticObjectId
import logging

from backend.models.tb_report import TBReport, ReportStatus, ReportType
from backend.models.tb_user import TBUser
from backend.models.tb_message import TBMessage
from backend.routes.tb_admin_auth import get_current_admin, check_super_admin
from backend.utils.objectid_utils import validate_object_id
from backend.socket_server import sio

router = APIRouter(prefix="/api/admin/moderation", tags=["Luveloop Admin Moderation"])
logger = logging.getLogger("moderation")


@router.get("/reports")
async def list_reports(
    status: Optional[str] = Query("pending", regex="^(pending|approved|removed|banned|all)$"),
    report_type: Optional[str] = Query(None, regex="^(photo|profile|message)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(get_current_admin)
):
    """List content reports"""
    query = {}
    
    if status and status != "all":
        query["status"] = status
    
    if report_type:
        query["report_type"] = report_type
    
    total = await TBReport.find(query).count()
    skip = (page - 1) * limit
    
    reports = await TBReport.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
    
    # Enrich with user names
    result = []
    for report in reports:
        reported_user = await TBUser.find_one({"_id": report.reported_user_id})
        reporter = await TBUser.find_one({"_id": report.reported_by_user_id})
        
        result.append({
            "id": str(report.id),
            "type": report.report_type,
            "reportedUser": reported_user.name if reported_user else "Unknown",
            "reportedUserId": str(report.reported_user_id),
            "reportedBy": reporter.name if reporter else "Unknown",
            "reason": report.reason,
            "content": report.content,
            "status": report.status,
            "timestamp": report.created_at.isoformat()
        })
    
    return {
        "reports": result,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/stats")
async def get_moderation_stats(
    admin: dict = Depends(get_current_admin)
):
    """Get moderation queue stats"""
    pending = await TBReport.find(TBReport.status == ReportStatus.PENDING).count()
    photo_reports = await TBReport.find(
        TBReport.status == ReportStatus.PENDING,
        TBReport.report_type == ReportType.PHOTO
    ).count()
    profile_reports = await TBReport.find(
        TBReport.status == ReportStatus.PENDING,
        TBReport.report_type == ReportType.PROFILE
    ).count()
    message_reports = await TBReport.find(
        TBReport.status == ReportStatus.PENDING,
        TBReport.report_type == ReportType.MESSAGE
    ).count()
    
    return {
        "pending": pending,
        "photoReports": photo_reports,
        "profileReports": profile_reports,
        "messageReports": message_reports
    }


@router.post("/reports/{report_id}/approve")
async def approve_content(
    report_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Approve content - no action needed"""
    report_oid = validate_object_id(report_id, "Report")
    report = await TBReport.get(report_oid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = ReportStatus.APPROVED
    report.reviewed_by = admin["email"]
    report.reviewed_at = datetime.now(timezone.utc)
    await report.save()

    await sio.emit("admin_update", {"action": "report_approved", "report_id": report_id})

    return {"success": True, "message": "Content approved - no action taken"}


@router.post("/reports/{report_id}/remove")
async def remove_content(
    report_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Remove reported content"""
    report_oid = validate_object_id(report_id, "Report")
    report = await TBReport.get(report_oid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Actually remove the content based on type
    if report.report_type == ReportType.PHOTO:
        # Remove the specific photo from user's profile
        user = await TBUser.get(report.reported_user_id)
        if user and report.content in user.profile_pictures:
            user.profile_pictures.remove(report.content)
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
            logger.info(f"Admin {admin['email']} removed photo from user {user.id}")
            
    elif report.report_type == ReportType.PROFILE:
        # Suspend the user for profile violations
        user = await TBUser.get(report.reported_user_id)
        if user:
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
            logger.info(f"Admin {admin['email']} suspended user {user.id} due to profile report")
            
    elif report.report_type == ReportType.MESSAGE:
        # Delete the specific reported message
        # Since we only have content, we find messages with this content between these users
        await TBMessage.find({
            "sender_id": report.reported_user_id,
            "receiver_id": report.reported_by_user_id,
            "content": report.content
        }).delete()
        logger.info(f"Admin {admin['email']} removed reported message from {report.reported_user_id}")
    
    report.status = ReportStatus.REMOVED
    report.reviewed_by = admin["email"]
    report.reviewed_at = datetime.now(timezone.utc)
    await report.save()

    await sio.emit("admin_update", {"action": "content_removed", "report_id": report_id})

    return {"success": True, "message": "Content removed and violation recorded"}


@router.post("/reports/{report_id}/ban")
async def ban_user_from_report(
    report_id: str,
    admin: dict = Depends(check_super_admin)
):
    """Ban user based on report"""
    report_oid = validate_object_id(report_id, "Report")
    report = await TBReport.get(report_oid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    user = await TBUser.get(report.reported_user_id)
    if user:
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await user.save()
        logger.info(f"Admin {admin['email']} BANNED user {user.id} from report {report.id}")
        
    report.status = ReportStatus.BANNED
    report.reviewed_by = admin["email"]
    report.reviewed_at = datetime.now(timezone.utc)
    await report.save()

    await sio.emit("admin_update", {"action": "user_banned", "report_id": report_id, "user_id": str(report.reported_user_id) if report.reported_user_id else None})

    return {"success": True, "message": "User has been banned"}
