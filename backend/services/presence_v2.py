import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from backend.models.presence_v2 import PresenceV2, PresenceStatus

logger = logging.getLogger('service.presence_v2')

class PresenceServiceV2:
    def __init__(self):
        self.away_threshold_minutes = 5
        self.offline_threshold_minutes = 30
    
    async def heartbeat(self, user_id: str, device_info: Optional[Dict[str, Any]] = None) -> PresenceV2:
        """Update user presence with heartbeat"""
        presence = await PresenceV2.find_one(PresenceV2.user_id == user_id)
        
        if not presence:
            presence = PresenceV2(
                user_id=user_id,
                status=PresenceStatus.ONLINE,
                device_info=device_info or {}
            )
        else:
            presence.status = PresenceStatus.ONLINE
            presence.last_activity = datetime.now(timezone.utc)
            presence.updated_at = datetime.now(timezone.utc)
            if device_info:
                presence.device_info = device_info
        
        presence.last_seen = datetime.now(timezone.utc)
        await presence.save()
        
        logger.debug(f"Heartbeat received from user {user_id}")
        return presence
    
    async def get_status(self, user_id: str) -> Optional[PresenceStatus]:
        """Get current presence status for a user"""
        presence = await PresenceV2.find_one(PresenceV2.user_id == user_id)
        if presence:
            # Auto-update status based on last activity
            await self._update_stale_status(presence)
            return presence.status
        return PresenceStatus.OFFLINE
    
    async def bulk_status_lookup(self, user_ids: List[str]) -> Dict[str, str]:
        """Get presence status for multiple users"""
        presences = await PresenceV2.find({"user_id": {"$in": user_ids}}).to_list()
        
        result = {}
        for presence in presences:
            await self._update_stale_status(presence)
            result[presence.user_id] = presence.status.value
        
        # Set offline for users not found
        for user_id in user_ids:
            if user_id not in result:
                result[user_id] = PresenceStatus.OFFLINE.value
        
        return result
    
    async def set_offline(self, user_id: str):
        """Explicitly set user as offline"""
        presence = await PresenceV2.find_one(PresenceV2.user_id == user_id)
        if presence:
            presence.status = PresenceStatus.OFFLINE
            presence.updated_at = datetime.now(timezone.utc)
            await presence.save()
            logger.info(f"User {user_id} set to offline")
    
    async def update_stale_presences(self) -> int:
        """Update all stale presences (background task)"""
        now = datetime.now(timezone.utc)
        away_threshold = now - timedelta(minutes=self.away_threshold_minutes)
        offline_threshold = now - timedelta(minutes=self.offline_threshold_minutes)
        
        # Mark as away
        away_updated = await PresenceV2.find(
            PresenceV2.status == PresenceStatus.ONLINE,
            PresenceV2.last_activity < away_threshold
        ).to_list()
        
        for presence in away_updated:
            presence.status = PresenceStatus.AWAY
            presence.updated_at = now
            await presence.save()
        
        # Mark as offline
        offline_updated = await PresenceV2.find(
            PresenceV2.status.is_in([PresenceStatus.ONLINE, PresenceStatus.AWAY]),
            PresenceV2.last_activity < offline_threshold
        ).to_list()
        
        for presence in offline_updated:
            presence.status = PresenceStatus.OFFLINE
            presence.updated_at = now
            await presence.save()
        
        total_updated = len(away_updated) + len(offline_updated)
        if total_updated > 0:
            logger.info(f"Updated {total_updated} stale presences ({len(away_updated)} away, {len(offline_updated)} offline)")
        
        return total_updated
    
    async def _update_stale_status(self, presence: PresenceV2):
        """Internal method to update stale status"""
        now = datetime.now(timezone.utc)
        away_threshold = now - timedelta(minutes=self.away_threshold_minutes)
        offline_threshold = now - timedelta(minutes=self.offline_threshold_minutes)
        
        if presence.last_activity < offline_threshold and presence.status != PresenceStatus.OFFLINE:
            presence.status = PresenceStatus.OFFLINE
            presence.updated_at = now
            await presence.save()
        elif presence.last_activity < away_threshold and presence.status == PresenceStatus.ONLINE:
            presence.status = PresenceStatus.AWAY
            presence.updated_at = now
            await presence.save()
    
    async def get_online_users_count(self) -> int:
        """Get count of online users"""
        return await PresenceV2.find(PresenceV2.status == PresenceStatus.ONLINE).count()
    
    async def get_all_online_users(self, limit: int = 100) -> List[str]:
        """Get list of all online users"""
        presences = await PresenceV2.find(PresenceV2.status == PresenceStatus.ONLINE).limit(limit).to_list()
        return [p.user_id for p in presences]

_presence_service_v2 = None

def get_presence_service_v2():
    global _presence_service_v2
    if _presence_service_v2 is None:
        _presence_service_v2 = PresenceServiceV2()
    return _presence_service_v2
