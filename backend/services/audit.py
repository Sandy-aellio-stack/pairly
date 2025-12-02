from backend.models.audit_log import AuditLog
from beanie import PydanticObjectId
from datetime import datetime
from typing import Optional

async def log_event(
    actor_user_id: Optional[PydanticObjectId] = None,
    actor_ip: Optional[str] = None,
    action: str = "",
    details: dict = {},
    severity: str = "info"
):
    log = AuditLog(
        actor_user_id=actor_user_id,
        actor_ip=actor_ip,
        action=action,
        details=details,
        severity=severity,
        created_at=datetime.utcnow()
    )
    await log.insert()