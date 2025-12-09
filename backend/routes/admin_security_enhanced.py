from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, List
import logging
from datetime import datetime, timezone, timedelta
from backend.models.user import User
from backend.models.failed_login import FailedLogin
from backend.models.device_fingerprint import DeviceFingerprint
from backend.models.fraud_alert import FraudAlert
from backend.services.admin_rbac import get_admin_user, AdminRBACService
from backend.services.admin_logging import AdminLoggingService
from backend.middleware.rate_limiter import get_banned_ips, unban_ip
from beanie import PydanticObjectId

logger = logging.getLogger('routes.admin_security_enhanced')
router = APIRouter(prefix="/api/admin/security", tags=["admin-security"])

@router.get("/dashboard")
async def get_security_dashboard(
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("security.view"))
):
    """Get security dashboard overview"""
    try:
        # Failed login metrics (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        failed_logins = await FailedLogin.find(
            FailedLogin.created_at >= yesterday
        ).to_list()
        
        # Active fraud alerts
        fraud_alerts = await FraudAlert.find(
            FraudAlert.status == "open"
        ).to_list()
        
        # High-risk device fingerprints
        high_risk_devices = await DeviceFingerprint.find(
            DeviceFingerprint.risk_score >= 70
        ).limit(50).to_list()
        
        # Banned IPs
        banned_ips = await get_banned_ips()
        
        # Locked accounts
        locked_accounts = await User.find(
            {"$or": [{"is_suspended": True}, {"account_locked": True}]}
        ).count()
        
        dashboard_data = {
            "failed_logins_24h": len(failed_logins),
            "active_fraud_alerts": len(fraud_alerts),
            "high_risk_devices": len(high_risk_devices),
            "banned_ips_count": len(banned_ips),
            "locked_accounts": locked_accounts,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await AdminLoggingService.log_action(
            admin_user_id=str(admin_user.id),
            admin_email=admin_user.email,
            admin_role=admin_user.role,
            action="security_dashboard_viewed",
            target_type="system",
            ip_address=request.client.host if request.client else None
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error fetching security dashboard: {e}", exc_info=True)
        return {"error": str(e)}

@router.get("/failed-logins")
async def get_failed_logins(
    request: Request,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    admin_user: User = Depends(AdminRBACService.require_permission("security.view"))
):
    """Get failed login attempts"""
    start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    failed_logins = await FailedLogin.find(
        FailedLogin.created_at >= start_time
    ).sort("-created_at").limit(limit).to_list()
    
    return {
        "failed_logins": [
            {
                "email": fl.email,
                "ip_address": fl.ip_address,
                "count": fl.count,
                "locked_until": fl.locked_until.isoformat() if fl.locked_until else None,
                "created_at": fl.created_at.isoformat()
            }
            for fl in failed_logins
        ],
        "total": len(failed_logins),
        "timeframe_hours": hours
    }

@router.get("/suspicious-ips")
async def get_suspicious_ips(
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("security.view"))
):
    """Get list of suspicious IP addresses"""
    # Get IPs with multiple failed logins
    failed_logins = await FailedLogin.find(
        FailedLogin.count >= 3
    ).sort("-count").limit(100).to_list()
    
    # Get banned IPs
    banned_ips = await get_banned_ips()
    
    return {
        "suspicious_ips": [
            {
                "ip_address": fl.ip_address,
                "failed_attempts": fl.count,
                "email_attempted": fl.email,
                "locked_until": fl.locked_until.isoformat() if fl.locked_until else None,
                "status": "locked" if fl.locked_until and fl.locked_until > datetime.now(timezone.utc) else "active"
            }
            for fl in failed_logins
        ],
        "banned_ips": banned_ips,
        "total_suspicious": len(failed_logins),
        "total_banned": len(banned_ips)
    }

@router.get("/device-fingerprints")
async def get_device_fingerprints(
    request: Request,
    min_risk_score: int = Query(50, ge=0, le=100),
    limit: int = Query(100, ge=1, le=500),
    admin_user: User = Depends(AdminRBACService.require_permission("security.view"))
):
    """Get device fingerprints with risk scores"""
    devices = await DeviceFingerprint.find(
        DeviceFingerprint.risk_score >= min_risk_score
    ).sort("-risk_score").limit(limit).to_list()
    
    return {
        "devices": [
            {
                "fingerprint_hash": d.fingerprint_hash,
                "user_id": str(d.user_id) if d.user_id else None,
                "ip_address": d.ip_address,
                "risk_score": d.risk_score,
                "trusted": d.trusted,
                "created_at": d.created_at.isoformat(),
                "risk_history": d.risk_history[-5:] if d.risk_history else []
            }
            for d in devices
        ],
        "total": len(devices),
        "min_risk_score": min_risk_score
    }

@router.get("/fraud-alerts")
async def get_fraud_alerts(
    request: Request,
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    admin_user: User = Depends(AdminRBACService.require_permission("security.view"))
):
    """Get fraud detection alerts"""
    query = {}
    if status:
        query["status"] = status
    
    alerts = await FraudAlert.find(query).sort("-created_at").limit(limit).to_list()
    
    return {
        "fraud_alerts": [
            {
                "id": str(a.id),
                "user_id": str(a.user_id) if a.user_id else None,
                "risk_score": a.risk_score,
                "rule_triggered": a.rule_triggered,
                "status": a.status,
                "metadata": a.metadata,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ],
        "total": len(alerts)
    }

@router.post("/fraud-alerts/{alert_id}/resolve")
async def resolve_fraud_alert(
    alert_id: str,
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("security.action"))
):
    """Resolve a fraud alert"""
    alert = await FraudAlert.get(PydanticObjectId(alert_id))
    if not alert:
        return {"error": "Fraud alert not found"}
    
    old_status = alert.status
    alert.status = "resolved"
    await alert.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="fraud_alert_resolved",
        target_type="fraud_alert",
        target_id=alert_id,
        before_state={"status": old_status},
        after_state={"status": "resolved"},
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True, "alert_id": alert_id, "new_status": "resolved"}

@router.post("/users/{user_id}/lock")
async def lock_user_account(
    user_id: str,
    request: Request,
    reason: str = Query(...),
    admin_user: User = Depends(AdminRBACService.require_permission("security.action"))
):
    """Lock a user account"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"error": "User not found"}
    
    # Store old state
    old_state = {"account_locked": getattr(user, "account_locked", False)}
    
    # Lock account
    user.account_locked = True
    await user.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="user_account_locked",
        target_type="user",
        target_id=user_id,
        before_state=old_state,
        after_state={"account_locked": True},
        reason=reason,
        ip_address=request.client.host if request.client else None,
        severity="warning"
    )
    
    return {"success": True, "user_id": user_id, "locked": True}

@router.post("/users/{user_id}/unlock")
async def unlock_user_account(
    user_id: str,
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("security.action"))
):
    """Unlock a user account"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"error": "User not found"}
    
    old_state = {"account_locked": getattr(user, "account_locked", False)}
    
    user.account_locked = False
    await user.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="user_account_unlocked",
        target_type="user",
        target_id=user_id,
        before_state=old_state,
        after_state={"account_locked": False},
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True, "user_id": user_id, "locked": False}

@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: str,
    request: Request,
    reason: str = Query(...),
    admin_user: User = Depends(AdminRBACService.require_permission("security.action"))
):
    """Ban a user permanently"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"error": "User not found"}
    
    old_state = {"is_suspended": user.is_suspended}
    
    user.is_suspended = True
    await user.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="user_banned",
        target_type="user",
        target_id=user_id,
        before_state=old_state,
        after_state={"is_suspended": True},
        reason=reason,
        ip_address=request.client.host if request.client else None,
        severity="critical"
    )
    
    return {"success": True, "user_id": user_id, "banned": True}

@router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: str,
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("security.action"))
):
    """Unban a user"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"error": "User not found"}
    
    old_state = {"is_suspended": user.is_suspended}
    
    user.is_suspended = False
    await user.save()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="user_unbanned",
        target_type="user",
        target_id=user_id,
        before_state=old_state,
        after_state={"is_suspended": False},
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True, "user_id": user_id, "banned": False}

@router.post("/ip/{ip_address}/unban")
async def unban_ip_address(
    ip_address: str,
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("security.action"))
):
    """Unban an IP address"""
    success = await unban_ip(ip_address)
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="ip_unbanned",
        target_type="ip_address",
        target_id=ip_address,
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": success, "ip_address": ip_address}

@router.get("/audit-logs")
async def get_security_audit_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    action: Optional[str] = None,
    admin_user: User = Depends(AdminRBACService.require_permission("security.view"))
):
    """Get security-related audit logs"""
    from backend.services.admin_logging import AdminLoggingService
    
    logs, total = await AdminLoggingService.get_audit_logs(
        action=action,
        limit=limit,
        skip=skip
    )
    
    return {
        "logs": [
            {
                "id": str(log.id),
                "admin_email": log.admin_email,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "reason": log.reason,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "total": total,
        "limit": limit,
        "skip": skip
    }