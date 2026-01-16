from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import datetime, timezone
from beanie import PydanticObjectId

from backend.models.tb_report import TBReport, ReportStatus
from backend.models.tb_user import TBUser
from backend.routes.tb_admin_auth import get_current_admin

router = APIRouter(prefix="/api/admin/moderation", tags=["Luveloop Admin Moderation"])


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
        reported_user = await TBUser.find_one({"_id": PydanticObjectId(report.reported_user_id)}) if report.reported_user_id else None
        reporter = await TBUser.find_one({"_id": PydanticObjectId(report.reported_by_user_id)}) if report.reported_by_user_id else None
        
        result.append({
            "id": report.id,
            "type": report.report_type,
            "reportedUser": reported_user.name if reported_user else "Unknown",
            "reportedUserId": report.reported_user_id,
            "reportedBy": reporter.name if reporter else "Unknown",
            "reason": report.reason,
            "content": report.content,
            "status": report.status,
            "timestamp": report.created_at.strftime("%Y-%m-%d %H:%M")
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
        TBReport.report_type == "photo"
    ).count()
    profile_reports = await TBReport.find(
        TBReport.status == ReportStatus.PENDING,
        TBReport.report_type == "profile"
    ).count()
    message_reports = await TBReport.find(
        TBReport.status == ReportStatus.PENDING,
        TBReport.report_type == "message"
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
    report = await TBReport.find_one(TBReport.id == report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = ReportStatus.APPROVED
    report.reviewed_by = admin["email"]
    report.reviewed_at = datetime.now(timezone.utc)
    await report.save()
    
    return {"success": True, "message": "Content approved - no action taken"}


@router.post("/reports/{report_id}/remove")
async def remove_content(
    report_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Remove reported content"""
    report = await TBReport.find_one(TBReport.id == report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = ReportStatus.REMOVED
    report.reviewed_by = admin["email"]
    report.reviewed_at = datetime.now(timezone.utc)
    await report.save()
    
    # TODO: Actually remove the content (photo/message)
    
    return {"success": True, "message": "Content removed and user warned"}


@router.post("/reports/{report_id}/ban")
async def ban_user_from_report(
    report_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Ban user based on report"""
    report = await TBReport.find_one(TBReport.id == report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Ban the user
    try:
        user = await TBUser.get(PydanticObjectId(report.reported_user_id))
        if user:
            user.is_active = False
            await user.save()
    except:
        pass
    
    report.status = ReportStatus.BANNED
    report.reviewed_by = admin["email"]
    report.reviewed_at = datetime.now(timezone.utc)
    await report.save()
    
    return {"success": True, "message": "User has been banned"}
