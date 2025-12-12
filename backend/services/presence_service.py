import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from backend.models.presence import Presence

# simple redis wrapper if available
try:
    import aioredis
    _redis = None
except Exception:
    aioredis = None
    _redis = None

HEARTBEAT_TTL_SECONDS = int(os.getenv("PRESENCE_TTL", "120"))
AWAY_THRESHOLD_SECONDS = int(os.getenv("PRESENCE_AWAY", "300"))

class PresenceService:
    def __init__(self):
        self._local_cache: Dict[str, dict] = {}

    async def heartbeat(self, user_id: str, client_info: dict = None):
        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(seconds=HEARTBEAT_TTL_SECONDS)
        # update DB
        obj = await Presence.find_one(Presence.user_id == user_id)
        if not obj:
            obj = Presence(user_id=user_id, status="online", last_seen=now, client_info=client_info, ttl_expires_at=expire_at)
        else:
            obj.status = "online"
            obj.last_seen = now
            obj.client_info = client_info
            obj.ttl_expires_at = expire_at
        await obj.save()
        # update in-memory
        self._local_cache[user_id] = {"status":"online","last_seen":now.isoformat(),"expires_at":expire_at.isoformat()}

    async def mark_offline(self, user_id: str):
        obj = await Presence.find_one(Presence.user_id == user_id)
        if obj:
            obj.status = "offline"
            obj.last_seen = datetime.now(timezone.utc)
            obj.ttl_expires_at = None
            await obj.save()
        self._local_cache.pop(user_id, None)

    async def get(self, user_id: str):
        obj = await Presence.find_one(Presence.user_id == user_id)
        if not obj:
            return {"user_id": user_id, "status":"offline"}
        return {"user_id": obj.user_id, "status": obj.status, "last_seen": obj.last_seen, "client_info": obj.client_info}

    async def bulk_get(self, user_ids: list):
        q = Presence.find({"user_id": {"$in": user_ids}})
        res = []
        async for p in q:
            res.append({"user_id": p.user_id, "status": p.status, "last_seen": p.last_seen})
        # add missing users as offline
        found = {r["user_id"] for r in res}
        for uid in user_ids:
            if uid not in found:
                res.append({"user_id": uid, "status": "offline"})
        return res

    async def monitor_expirations(self, interval_seconds: int=30):
        # background task to mark offline if ttl passed
        while True:
            now = datetime.now(timezone.utc)
            q = Presence.find({"ttl_expires_at": {"$lte": now}})
            async for p in q:
                p.status = "offline"
                p.ttl_expires_at = None
                await p.save()
                self._local_cache.pop(p.user_id, None)
            await asyncio.sleep(interval_seconds)

presence_service = PresenceService()
