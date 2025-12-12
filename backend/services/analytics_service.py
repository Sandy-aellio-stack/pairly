from datetime import datetime, timedelta, timezone
from collections import defaultdict
from backend.models.analytics_event import AnalyticsEvent
from beanie import PydanticObjectId

class AnalyticsService:
    async def ingest(self, user_id: str, event_type: str, payload: dict):
        ev = AnalyticsEvent(user_id=user_id, event_type=event_type, payload=payload)
        await ev.insert()
        return ev

    async def aggregate_daily(self, day: datetime = None):
        if not day:
            day = datetime.now(timezone.utc)
        start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        q = AnalyticsEvent.find({"created_at": {"$gte": start, "$lt": end}})
        counters = defaultdict(int)
        async for e in q:
            counters[e.event_type] += 1
        return dict(counters)

    async def get_user_events(self, user_id: str, limit: int = 50):
        q = AnalyticsEvent.find({"user_id": user_id}).sort("-created_at").limit(limit)
        out = []
        async for e in q:
            out.append({"event_type": e.event_type, "payload": e.payload, "created_at": e.created_at})
        return out

analytics_service = AnalyticsService()
