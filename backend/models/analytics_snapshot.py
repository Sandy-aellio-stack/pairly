from beanie import Document
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional
from pydantic import Field

class AnalyticsSnapshot(Document):
    """Daily analytics snapshot for admin dashboard"""
    
    snapshot_date: date
    snapshot_type: str  # "daily", "weekly", "monthly"
    
    # User metrics
    total_users: int = 0
    active_users_today: int = 0
    new_signups_today: int = 0
    dau: int = 0
    wau: int = 0
    mau: int = 0
    
    # Engagement metrics
    total_swipes: int = 0
    total_matches: int = 0
    total_messages: int = 0
    total_calls: int = 0
    
    # Financial metrics
    revenue_credits: float = 0.0
    revenue_subscriptions: float = 0.0
    revenue_calls: float = 0.0
    total_revenue: float = 0.0
    
    # Creator metrics
    total_creators: int = 0
    active_creators: int = 0
    creator_earnings: float = 0.0
    
    # Retention metrics
    retention_d1: Optional[float] = None
    retention_d7: Optional[float] = None
    retention_d30: Optional[float] = None
    
    # Churn metrics
    churn_rate: Optional[float] = None
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "analytics_snapshots"
        indexes = [
            "snapshot_date",
            "snapshot_type",
            [("snapshot_date", -1), ("snapshot_type", 1)]
        ]