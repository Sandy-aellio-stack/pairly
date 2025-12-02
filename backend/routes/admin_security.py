from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.models.user import User, Role
from backend.routes.auth import get_current_user
from backend.middleware.rate_limiter import get_banned_ips, unban_ip
from backend.services.ws_rate_limiter import mute_user, unmute_user, list_muted
from backend.services.audit import log_event

router = APIRouter(prefix="/api/admin/security")


class UnbanRequest(BaseModel):
    ip: str


class MuteRequest(BaseModel):
    user_id: str
    seconds: int = 3600


class UnmuteRequest(BaseModel):
    user_id: str


async def require_admin(user: User = Depends(get_current_user)):
    if user.role != Role.ADMIN:
        raise HTTPException(403, "Admin only")
    return user


@router.get("/banned-ips")
async def list_banned_ips(admin: User = Depends(require_admin)):
    banned = await get_banned_ips()
    return {"banned_ips": banned}


@router.post("/unban")
async def unban_ip_endpoint(req: UnbanRequest, admin: User = Depends(require_admin)):
    await unban_ip(req.ip)
    await log_event(
        actor_user_id=admin.id,
        actor_ip=None,
        action="ip_unbanned",
        details={"ip": req.ip, "admin_id": str(admin.id)},
        severity="info"
    )
    return {"status": "unbanned", "ip": req.ip}


@router.post("/mute")
async def mute_user_endpoint(req: MuteRequest, admin: User = Depends(require_admin)):
    await mute_user(req.user_id, req.seconds)
    await log_event(
        actor_user_id=admin.id,
        actor_ip=None,
        action="admin_mute",
        details={"muted_user_id": req.user_id, "seconds": req.seconds, "admin_id": str(admin.id)},
        severity="info"
    )
    return {"status": "muted", "user_id": req.user_id, "seconds": req.seconds}


@router.post("/unmute")
async def unmute_user_endpoint(req: UnmuteRequest, admin: User = Depends(require_admin)):
    await unmute_user(req.user_id)
    await log_event(
        actor_user_id=admin.id,
        actor_ip=None,
        action="admin_unmute",
        details={"unmuted_user_id": req.user_id, "admin_id": str(admin.id)},
        severity="info"
    )
    return {"status": "unmuted", "user_id": req.user_id}


@router.get("/muted")
async def list_muted_users(admin: User = Depends(require_admin)):
    muted = await list_muted()
    return {"muted_users": muted}