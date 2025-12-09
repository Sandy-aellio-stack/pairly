import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.models.admin_audit_log import AdminAuditLog
from beanie import PydanticObjectId

logger = logging.getLogger('service.admin_logging')

class AdminLoggingService:
    """Service for logging all admin actions"""
    
    @staticmethod
    async def log_action(
        admin_user_id: str,
        admin_email: str,
        admin_role: str,
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info"
    ) -> AdminAuditLog:
        """Log an admin action"""
        try:
            audit_log = AdminAuditLog(
                admin_user_id=admin_user_id,
                admin_email=admin_email,
                admin_role=admin_role,
                action=action,
                target_type=target_type,
                target_id=target_id,
                before_state=before_state,
                after_state=after_state,
                reason=reason,
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity
            )
            
            await audit_log.insert()
            
            logger.info(
                f"Admin action logged: {action}",
                extra={
                    "event": "admin_action",
                    "admin_user_id": admin_user_id,
                    "action": action,
                    "target_type": target_type,
                    "target_id": target_id,
                    "severity": severity
                }
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def get_audit_logs(
        admin_user_id: Optional[str] = None,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ):
        """Retrieve audit logs with filtering"""
        query = {}
        
        if admin_user_id:
            query["admin_user_id"] = admin_user_id
        if action:
            query["action"] = action
        if target_type:
            query["target_type"] = target_type
        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date
        
        logs = await AdminAuditLog.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
        total = await AdminAuditLog.find(query).count()
        
        return logs, total