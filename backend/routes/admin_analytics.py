from fastapi import APIRouter, HTTPException, Depends, Query
from backend.models.user import User, Role
from backend.models.session import Session
from backend.models.fraud_alert import FraudAlert
from backend.models.device_fingerprint import DeviceFingerprint
from backend.models.audit_log import AuditLog
from backend.models.failed_login import FailedLogin
from datetime import datetime, timedelta, timezone
from typing import Optional
from beanie import PydanticObjectId

router = APIRouter(prefix="/api/admin/security-analytics", tags=["Admin Security Analytics"])


async def require_admin(user: User = Depends(lambda: None)):
    if not user or user.role != Role.ADMIN:
        raise HTTPException(403, "Admin only")
    return user


@router.get("/analytics")
async def get_security_analytics(admin: User = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    one_day_ago = now - timedelta(days=1)
    
    total_users = await User.find({}).count()
    
    active_sessions = await Session.find(
        Session.revoked == False,
        Session.last_active_at >= one_day_ago
    ).count()
    
    failed_logins_24h = await FailedLogin.find(
        FailedLogin.created_at >= one_day_ago
    ).count()
    
    fraud_alerts_7d = await FraudAlert.find(
        FraudAlert.created_at >= seven_days_ago
    ).sort("-score").limit(50).to_list()
    
    fraud_summary = [
        {
            "id": str(alert.id),
            "user_id": str(alert.user_id) if alert.user_id else None,
            "score": alert.score,
            "rule_triggered": alert.rule_triggered,
            "ip": alert.ip,
            "status": alert.status,
            "created_at": alert.created_at.isoformat()
        }
        for alert in fraud_alerts_7d
    ]
    
    return {
        "user_metrics": {
            "total_users": total_users,
            "active_sessions": active_sessions
        },
        "security_metrics": {
            "failed_logins_24h": failed_logins_24h,
            "fraud_alerts_7d_count": len(fraud_summary),
            "fraud_alerts_7d": fraud_summary
        }
    }


@router.get("/fraud-alerts")
async def list_fraud_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    admin: User = Depends(require_admin)
):
    filters = {}
    if status:
        filters["status"] = status
    
    alerts = await FraudAlert.find(filters).sort("-created_at").skip(offset).limit(limit).to_list()
    
    return {
        "alerts": [
            {
                "id": str(alert.id),
                "user_id": str(alert.user_id) if alert.user_id else None,
                "ip": alert.ip,
                "fingerprint_hash": alert.fingerprint_hash,
                "score": alert.score,
                "rule_triggered": alert.rule_triggered,
                "status": alert.status,
                "metadata": alert.metadata,
                "created_at": alert.created_at.isoformat()
            }
            for alert in alerts
        ]
    }


@router.get("/fingerprint/{fingerprint_hash}")
async def get_fingerprint_details(
    fingerprint_hash: str,
    admin: User = Depends(require_admin)
):
    fingerprint = await DeviceFingerprint.find_one(
        DeviceFingerprint.fingerprint_hash == fingerprint_hash
    )
    
    if not fingerprint:
        raise HTTPException(404, "Fingerprint not found")
    
    return {
        "fingerprint_hash": fingerprint.fingerprint_hash,
        "user_id": str(fingerprint.user_id) if fingerprint.user_id else None,
        "ip": fingerprint.ip,
        "user_agent": fingerprint.user_agent,
        "device_info": fingerprint.device_info,
        "usage_count": fingerprint.usage_count,
        "created_at": fingerprint.created_at.isoformat(),
        "last_seen": fingerprint.last_seen.isoformat(),
        "risk_history": fingerprint.risk_history
    }


@router.post("/fraud/resolve")
async def resolve_fraud_alert(
    alert_id: str,
    action: str,
    admin: User = Depends(require_admin)
):
    if action not in ["clear", "review", "ban_ip"]:
        raise HTTPException(400, "Invalid action")
    
    alert = await FraudAlert.get(PydanticObjectId(alert_id))
    if not alert:
        raise HTTPException(404, "Alert not found")
    
    if action == "clear":
        alert.status = "cleared"
    elif action == "review":
        alert.status = "under_review"
    elif action == "ban_ip":
        alert.status = "banned"
    
    alert.resolved_by = admin.id
    alert.updated_at = datetime.now(timezone.utc)
    await alert.save()
    
    return {"status": "resolved", "action": action}


@router.get("/device-metrics")
async def get_device_metrics(admin: User = Depends(require_admin)):
    top_fingerprints = await DeviceFingerprint.find({}).sort("-usage_count").limit(20).to_list()
    
    return {
        "top_devices": [
            {
                "fingerprint_hash": fp.fingerprint_hash,
                "usage_count": fp.usage_count,
                "user_id": str(fp.user_id) if fp.user_id else None,
                "device_info": fp.device_info,
                "ip": fp.ip,
                "last_seen": fp.last_seen.isoformat()
            }
            for fp in top_fingerprints
        ]
    }