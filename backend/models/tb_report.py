from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid


class ReportType(str, Enum):
    PHOTO = "photo"
    PROFILE = "profile"
    MESSAGE = "message"


class ReportStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"  # Content is OK, no action
    REMOVED = "removed"    # Content removed
    BANNED = "banned"      # User banned


class TBReport(Document):
    """Content moderation report"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    report_type: ReportType
    reported_user_id: str
    reported_by_user_id: str
    reason: str
    content: Optional[str] = None  # URL for photo, text for message/profile
    
    status: ReportStatus = ReportStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tb_reports"
