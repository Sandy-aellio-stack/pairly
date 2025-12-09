from beanie import Document
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import Field

class AdminAuditLog(Document):
    """Audit log for all admin actions"""
    
    admin_user_id: str
    admin_email: str
    admin_role: str
    action: str  # e.g., "user_banned", "payout_approved", "post_removed"
    target_type: str  # e.g., "user", "post", "payout", "system"
    target_id: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severity: str = "info"  # info, warning, critical
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "admin_audit_logs"
        indexes = [
            "admin_user_id",
            "action",
            "target_type",
            "created_at",
            [("admin_user_id", 1), ("created_at", -1)],
            [("action", 1), ("created_at", -1)]
        ]