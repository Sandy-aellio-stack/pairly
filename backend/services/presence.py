from datetime import datetime, timedelta, timezone
from backend.models.profile import Profile
from beanie import PydanticObjectId
from typing import Dict, Optional
from fastapi import HTTPException
import time
import asyncio

online_users: Dict[str, float] = {}
presence_lock = asyncio.Lock()


async def set_online(user_id: str):
    async with presence_lock:
        online_users[user_id] = time.time()
    
    from backend.utils.objectid_utils import validate_object_id
    try:
        user_oid = validate_object_id(user_id)
        profile = await Profile.find_one(Profile.user_id == user_oid)
        if profile:
            profile.is_online = True
            profile.last_seen = datetime.now(timezone.utc)
            await profile.save()
    except HTTPException:
        # Ignore invalid IDs in background presence updates to prevent noise
        pass


async def set_offline(user_id: str):
    async with presence_lock:
        if user_id in online_users:
            del online_users[user_id]
    
    from backend.utils.objectid_utils import validate_object_id
    try:
        user_oid = validate_object_id(user_id)
        profile = await Profile.find_one(Profile.user_id == user_oid)
        if profile:
            profile.is_online = False
            profile.last_seen = datetime.now(timezone.utc)
            await profile.save()
    except HTTPException:
        pass


async def heartbeat(user_id: str):
    async with presence_lock:
        online_users[user_id] = time.time()


def is_online(user_id: str) -> bool:
    if user_id not in online_users:
        return False
    return time.time() - online_users[user_id] < 45


def get_last_seen(user_id: str) -> Optional[float]:
    return online_users.get(user_id)


async def cleanup_stale_users():
    while True:
        await asyncio.sleep(15)
        
        now = time.time()
        stale_users = []
        
        async with presence_lock:
            for user_id, last_heartbeat in list(online_users.items()):
                if now - last_heartbeat > 45:
                    stale_users.append(user_id)
        
        for user_id in stale_users:
            await set_offline(user_id)


async def start_presence_monitor():
    asyncio.create_task(cleanup_stale_users())