from fastapi import HTTPException
from backend.models.failed_login import FailedLogin
from backend.models.user import User
from backend.services.audit import log_event
from beanie import PydanticObjectId
from datetime import datetime, timedelta, timezone
from typing import Optional

LOCK_THRESHOLD = 3
LOCK_MINUTES = 30

async def check_login_lock(ip: str, email: str):
    user = await User.find_one(User.email == email)
    now = datetime.now(timezone.utc)

    ip_doc = await FailedLogin.find_one(FailedLogin.ip == ip)
    if ip_doc and ip_doc.locked_until and ip_doc.locked_until > now:
        raise HTTPException(403, "IP temporarily locked due to repeated failures")

    if user:
        udoc = await FailedLogin.find_one(FailedLogin.user_id == user.id)
        if udoc and udoc.locked_until and udoc.locked_until > now:
            raise HTTPException(403, "Account temporarily locked due to repeated failures")

async def register_failed_attempt(ip: str, user_id: Optional[PydanticObjectId]):
    now = datetime.now(timezone.utc)

    ip_doc = await FailedLogin.find_one(FailedLogin.ip == ip)
    if not ip_doc:
        ip_doc = FailedLogin(ip=ip, count=1, created_at=now)
    else:
        ip_doc.count += 1
    if ip_doc.count >= 150:
        ip_doc.locked_until = now + timedelta(hours=1)
        await log_event(
            actor_user_id=user_id,
            actor_ip=ip,
            action="ip_banned",
            details={"ip": ip, "count": ip_doc.count},
            severity="warning"
        )
    await ip_doc.save()

    if user_id:
        udoc = await FailedLogin.find_one(FailedLogin.user_id == user_id)
        if not udoc:
            udoc = FailedLogin(user_id=user_id, count=1, created_at=now)
        else:
            udoc.count += 1
        if udoc.count >= LOCK_THRESHOLD:
            udoc.locked_until = now + timedelta(minutes=LOCK_MINUTES)
            await log_event(
                actor_user_id=user_id,
                actor_ip=ip,
                action="account_locked",
                details={"user_id": str(user_id), "count": udoc.count},
                severity="warning"
            )
        await udoc.save()

async def clear_failed_attempts(user_id: PydanticObjectId):
    await FailedLogin.find_many(FailedLogin.user_id == user_id).delete()