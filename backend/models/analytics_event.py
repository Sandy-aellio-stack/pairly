from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timezone

class AnalyticsEvent(Document):
    user_id: str = Indexed()
    event_type: str
    payload: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = Field(default=False)

    class Settings:
        name = "analytics_events"
