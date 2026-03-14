import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from backend.models.app_settings import AppSettings
from backend.routes.tb_admin_auth import get_current_admin, check_super_admin

logger = logging.getLogger("admin.settings")

router = APIRouter(prefix="/api/admin/settings", tags=["TrueBond Admin Settings"])


class PackageUpdate(BaseModel):
    id: str
    name: str
    coins: int
    price_inr: int
    discount: int = 0
    popular: bool = False


class SettingsUpdate(BaseModel):
    # Pricing
    message_cost: Optional[int] = None
    audio_call_cost_per_min: Optional[int] = None
    video_call_cost_per_min: Optional[int] = None
    signup_bonus: Optional[int] = None
    
    # Packages
    packages: Optional[List[PackageUpdate]] = None
    
    # Matching
    default_search_radius: Optional[int] = None
    max_search_radius: Optional[int] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    
    # Safety
    auto_moderation: Optional[bool] = None
    profanity_filter: Optional[bool] = None
    photo_verification: Optional[bool] = None
    
    # App status
    maintenance_mode: Optional[bool] = None


@router.get("")
async def get_settings(
    admin: dict = Depends(get_current_admin)
):
    """Get current app settings"""
    settings = await AppSettings.get_or_create()
    
    return {
        # General
        "appName": "TrueBond",
        "tagline": "Real connections, meaningful bonds",
        "maintenanceMode": settings.maintenance_mode,
        
        # Matching
        "defaultSearchRadius": settings.default_search_radius,
        "maxSearchRadius": settings.max_search_radius,
        "minAge": settings.min_age,
        "maxAge": settings.max_age,
        
        # Credits
        "signupBonus": settings.signup_bonus,
        "messageCost": settings.message_cost,
        "audioCallCost": settings.audio_call_cost_per_min,
        "videoCallCost": settings.video_call_cost_per_min,
        
        # Packages
        "packages": settings.packages,
        
        # Safety
        "autoModeration": settings.auto_moderation,
        "profanityFilter": settings.profanity_filter,
        "photoVerification": settings.photo_verification
    }


@router.put("")
async def update_settings(
    updates: SettingsUpdate,
    admin: dict = Depends(check_super_admin)
):
    """Update app settings"""
    
    settings = await AppSettings.get_or_create()
    
    # Update provided fields
    update_data = updates.model_dump(exclude_none=True)
    
    if "packages" in update_data:
        settings.packages = [p.model_dump() if hasattr(p, 'model_dump') else p for p in update_data["packages"]]
        del update_data["packages"]
    
    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    settings.updated_at = datetime.now(timezone.utc)
    settings.updated_by = admin["email"]
    await settings.save()
    
    return {"success": True, "message": "Settings updated successfully"}


@router.get("/pricing")
async def get_pricing():
    """Public endpoint to get pricing info (for frontend)"""
    settings = await AppSettings.get_or_create()
    
    return {
        "messageCost": settings.message_cost,
        "audioCallCostPerMin": settings.audio_call_cost_per_min,
        "videoCallCostPerMin": settings.video_call_cost_per_min,
        "signupBonus": settings.signup_bonus,
        "packages": settings.packages
    }


@router.get("/security-audit")
async def get_security_audit(
    admin: dict = Depends(check_super_admin)
):
    """
    Get security configuration audit report.
    Only super_admin can access this endpoint.
    """
    
    import os
    from backend.core.security_config import (
        security_config, 
        JWTSecretValidator,
        validate_security_config
    )
    from backend.core.env_validator import get_validation_report
    
    environment = os.getenv("ENVIRONMENT", "development")
    jwt_secret = os.getenv("JWT_SECRET", "")
    
    # Validate JWT without exposing the secret
    jwt_valid, jwt_errors, jwt_metrics = JWTSecretValidator.validate(jwt_secret, environment)
    rotation_info = JWTSecretValidator.get_rotation_info(jwt_secret)
    
    # Get overall security validation
    security_valid, security_errors = validate_security_config()
    
    # Get environment validation
    env_report = get_validation_report()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": environment,
        "overall_status": "secure" if (jwt_valid and security_valid) else "needs_attention",
        
        "cors": {
            "status": "configured",
            "allowed_origins": security_config.cors_origins,
            "allow_credentials": security_config.cors_allow_credentials,
            "allow_methods": security_config.cors_allow_methods,
            "max_age_seconds": security_config.cors_max_age,
            "wildcard_warning": "*" in security_config.cors_origins,
        },
        
        "security_headers": {
            "hsts_enabled": security_config.enable_hsts,
            "hsts_max_age": security_config.hsts_max_age if security_config.enable_hsts else None,
            "hsts_preload": security_config.hsts_preload if security_config.enable_hsts else None,
            "csp_configured": bool(security_config.content_security_policy),
            "permissions_policy_configured": bool(security_config.permissions_policy),
        },
        
        "jwt": {
            "status": "valid" if jwt_valid else "weak",
            "algorithm": security_config.jwt_algorithm,
            "access_token_expiry_minutes": security_config.jwt_access_token_expire_minutes,
            "refresh_token_expiry_days": security_config.jwt_refresh_token_expire_days,
            "metrics": {
                "length": jwt_metrics["length"],
                "entropy_bits": round(jwt_metrics["entropy_bits"], 1),
                "character_classes": jwt_metrics["character_classes"],
            },
            "issues": jwt_errors if not jwt_valid else [],
            "rotation": rotation_info,
        },
        
        "rate_limiting": {
            "enabled": security_config.rate_limit_enabled,
            "endpoints_protected": [
                "/api/auth/login",
                "/api/auth/signup", 
                "/api/auth/otp/send",
                "/api/auth/otp/verify",
                "/api/payments/order",
                "/api/messages/send",
            ],
        },
        
        "environment_validation": env_report,
        
        "recommendations": _get_security_recommendations(environment, jwt_valid, security_config),
    }


def _get_security_recommendations(environment: str, jwt_valid: bool, config) -> list:
    """Generate security recommendations based on current config"""
    recommendations = []
    
    if environment == "development":
        recommendations.append({
            "priority": "info",
            "message": "Running in development mode - some security features are relaxed"
        })
    
    if "*" in config.cors_origins:
        recommendations.append({
            "priority": "high" if environment == "production" else "medium",
            "message": "CORS wildcard (*) detected - restrict to specific origins in production"
        })
    
    if not jwt_valid:
        recommendations.append({
            "priority": "critical" if environment == "production" else "high",
            "message": "JWT secret does not meet security requirements"
        })
    
    if not config.enable_hsts and environment == "production":
        recommendations.append({
            "priority": "high",
            "message": "HSTS is disabled - enable for production HTTPS deployments"
        })
    
    if not config.content_security_policy and environment == "production":
        recommendations.append({
            "priority": "medium",
            "message": "Content Security Policy not configured"
        })
    
    if not recommendations:
        recommendations.append({
            "priority": "info",
            "message": "Security configuration looks good for current environment"
        })
    
    return recommendations


# ========== ADMIN NOTIFICATION BROADCAST ==========

class AdminNotificationRequest(BaseModel):
    title: str
    body: str
    type: str = "announcement"
    target_user_ids: Optional[List[str]] = None


@router.post("/send-notification", tags=["Admin Notifications"])
async def send_notification_broadcast(
    data: AdminNotificationRequest,
    admin: dict = Depends(get_current_admin)
):
    """
    Broadcast a notification to all users or a specific subset.
    - Stores notification in DB for offline users
    - Emits socket event to all connected online users
    """
    from backend.models.tb_user import TBUser
    from backend.routes.tb_notifications import TBNotification
    from backend.socket_server import sio, user_sockets

    created_count = 0
    emitted_count = 0

    try:
        if data.target_user_ids:
            from beanie import PydanticObjectId
            oids = [PydanticObjectId(uid) for uid in data.target_user_ids if uid]
            users = await TBUser.find({"_id": {"$in": oids}, "is_active": True}).to_list()
        else:
            users = await TBUser.find({"is_active": True}).to_list()

        for user in users:
            uid = str(user.id)
            notif = TBNotification(
                user_id=uid,
                title=data.title,
                body=data.body,
                notification_type=data.type
            )
            await notif.insert()
            created_count += 1

            if uid in user_sockets and user_sockets[uid]:
                await sio.emit("new_notification", {
                    "id": str(notif.id),
                    "title": data.title,
                    "body": data.body,
                    "type": data.type,
                    "created_at": notif.created_at.isoformat()
                }, room=f"user_{uid}")
                emitted_count += 1

        logger.info(
            f"Admin notification sent by {admin.get('sub', 'unknown')}: "
            f"title='{data.title}', created={created_count}, emitted={emitted_count}"
        )

        return {
            "success": True,
            "message": f"Notification sent to {created_count} users ({emitted_count} online)",
            "created": created_count,
            "emitted": emitted_count
        }
    except Exception as e:
        logger.error(f"Admin notification broadcast failed: {e}")
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")
