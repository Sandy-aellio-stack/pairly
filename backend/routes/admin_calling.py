from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime, timezone
from backend.models.call_session_v2 import CallSessionV2, CallStatus
from backend.services.admin_rbac import AdminRBACService
from backend.services.admin_logging import AdminLoggingService
from backend.models.user import User

logger = logging.getLogger('routes.admin_calling')

router = APIRouter(prefix="/api/admin/calls", tags=["Admin - Calling"])

class ModerateCallRequest(BaseModel):
    call_quality: Optional[str] = None
    notes: Optional[str] = None

@router.get("/search")
async def search_calls(
    user_id: Optional[str] = Query(None),
    status: Optional[CallStatus] = Query(None),
    limit: int = Query(50, le=200),
    skip: int = Query(0, ge=0),
    admin: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """
    Search and filter calls (admin only)
    Requires: analytics.view permission
    """
    query = {}
    
    if user_id:
        query["$or"] = [
            {"caller_id": user_id},
            {"receiver_id": user_id}
        ]
    
    if status:
        query["status"] = status
    
    calls = await CallSessionV2.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
    total = await CallSessionV2.find(query).count()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="search_calls",
        target_type="call",
        metadata={
            "filters": {"user_id": user_id, "status": status.value if status else None},
            "results": len(calls)
        }
    )
    
    return {
        "calls": [
            {
                "id": call.id,
                "caller_id": call.caller_id,
                "receiver_id": call.receiver_id,
                "status": call.status.value,
                "initiated_at": call.initiated_at.isoformat(),
                "duration_seconds": call.duration_seconds,
                "credits_spent": call.credits_spent
            }
            for call in calls
        ],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "limit": limit
    }

@router.get("/stats/overview")
async def get_calling_stats(
    admin: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """
    Get overall calling statistics (admin only)
    Requires: analytics.view permission
    """
    total_calls = await CallSessionV2.find().count()
    
    # Status breakdown
    initiated = await CallSessionV2.find(CallSessionV2.status == CallStatus.INITIATED).count()
    ringing = await CallSessionV2.find(CallSessionV2.status == CallStatus.RINGING).count()
    connected = await CallSessionV2.find(CallSessionV2.status == CallStatus.CONNECTED).count()
    ended = await CallSessionV2.find(CallSessionV2.status == CallStatus.ENDED).count()
    missed = await CallSessionV2.find(CallSessionV2.status == CallStatus.MISSED).count()
    rejected = await CallSessionV2.find(CallSessionV2.status == CallStatus.REJECTED).count()
    failed = await CallSessionV2.find(CallSessionV2.status == CallStatus.FAILED).count()
    
    # Calculate total revenue
    all_calls = await CallSessionV2.find().to_list()
    total_credits_revenue = sum(call.credits_spent for call in all_calls)
    total_minutes = sum(call.duration_seconds // 60 for call in all_calls if call.duration_seconds > 0)
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="view_calling_stats",
        target_type="analytics",
        metadata={"total_calls": total_calls}
    )
    
    return {
        "total_calls": total_calls,
        "status_breakdown": {
            "initiated": initiated,
            "ringing": ringing,
            "connected": connected,
            "ended": ended,
            "missed": missed,
            "rejected": rejected,
            "failed": failed
        },
        "total_credits_revenue": total_credits_revenue,
        "total_minutes": total_minutes
    }

@router.get("/user/{user_id}/history")
async def get_user_call_history(
    user_id: str,
    limit: int = Query(100, le=500),
    admin: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """
    Get call history for a specific user (admin only)
    Requires: analytics.view permission
    """
    calls = await CallSessionV2.find(
        {
            "$or": [
                {"caller_id": user_id},
                {"receiver_id": user_id}
            ]
        }
    ).sort("-created_at").limit(limit).to_list()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="view_user_call_history",
        target_type="call",
        target_id=user_id,
        metadata={"call_count": len(calls)}
    )
    
    return {
        "user_id": user_id,
        "calls": [
            {
                "id": call.id,
                "caller_id": call.caller_id,
                "receiver_id": call.receiver_id,
                "status": call.status.value,
                "initiated_at": call.initiated_at.isoformat(),
                "connected_at": call.connected_at.isoformat() if call.connected_at else None,
                "ended_at": call.ended_at.isoformat() if call.ended_at else None,
                "duration_seconds": call.duration_seconds,
                "credits_spent": call.credits_spent,
                "disconnect_reason": call.disconnect_reason
            }
            for call in calls
        ],
        "total": len(calls)
    }

@router.get("/export")
async def export_calls(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(1000, le=5000),
    admin: User = Depends(AdminRBACService.require_permission("analytics.export"))
):
    """
    Export call data for analysis (admin only)
    Requires: analytics.export permission
    """
    query = {}
    
    if start_date:
        if "initiated_at" not in query:
            query["initiated_at"] = {}
        query["initiated_at"]["$gte"] = datetime.fromisoformat(start_date)
    
    if end_date:
        if "initiated_at" not in query:
            query["initiated_at"] = {}
        query["initiated_at"]["$lte"] = datetime.fromisoformat(end_date)
    
    calls = await CallSessionV2.find(query).limit(limit).to_list()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="export_calls",
        target_type="call",
        metadata={
            "filters": {"start_date": start_date, "end_date": end_date},
            "exported_count": len(calls)
        },
        severity="warning"
    )
    
    return {
        "calls": [
            {
                "id": call.id,
                "caller_id": call.caller_id,
                "receiver_id": call.receiver_id,
                "status": call.status.value,
                "initiated_at": call.initiated_at.isoformat(),
                "connected_at": call.connected_at.isoformat() if call.connected_at else None,
                "ended_at": call.ended_at.isoformat() if call.ended_at else None,
                "duration_seconds": call.duration_seconds,
                "credits_spent": call.credits_spent,
                "credits_per_minute": call.credits_per_minute,
                "disconnect_reason": call.disconnect_reason,
                "call_quality": call.call_quality
            }
            for call in calls
        ],
        "total_exported": len(calls),
        "export_timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/{call_id}/moderate")
async def moderate_call(
    call_id: str,
    request: ModerateCallRequest,
    admin: User = Depends(AdminRBACService.require_permission("moderation.action"))
):
    """
    Add moderation notes to a call (admin only)
    Requires: moderation.action permission
    """
    call = await CallSessionV2.find_one(CallSessionV2.id == call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if request.call_quality:
        call.call_quality = request.call_quality
    
    if request.notes:
        if "admin_notes" not in call.metadata:
            call.metadata["admin_notes"] = []
        call.metadata["admin_notes"].append({
            "admin_id": str(admin.id),
            "note": request.notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    call.updated_at = datetime.now(timezone.utc)
    await call.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin.id),
        admin_email=admin.email,
        admin_role=admin.role,
        action="moderate_call",
        target_type="call",
        target_id=call_id,
        metadata={
            "call_quality": request.call_quality,
            "notes_added": bool(request.notes)
        },
        severity="info"
    )
    
    return {
        "success": True,
        "call_id": call_id,
        "message": "Call moderation updated"
    }
