from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List
from backend.services.presence_service import presence_service
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/api/presence", tags=["presence"])

class HeartbeatIn(BaseModel):
    client_info: dict = {}

@router.post("/heartbeat")
async def heartbeat(payload: HeartbeatIn, user=Depends(get_current_user)):
    await presence_service.heartbeat(str(user.id), client_info=payload.client_info)
    return {"status":"ok"}

@router.post("/set-offline")
async def set_offline(user=Depends(get_current_user)):
    await presence_service.mark_offline(str(user.id))
    return {"status":"ok"}

class BulkGetIn(BaseModel):
    user_ids: List[str]

@router.post("/bulk")
async def bulk_get(payload: BulkGetIn):
    res = await presence_service.bulk_get(payload.user_ids)
    return {"items": res}

@router.get("/{user_id}")
async def get_presence(user_id: str):
    res = await presence_service.get(user_id)
    return res

# background monitor endpoint (only admin call)
@router.post("/start-monitor")
async def start_monitor(background_tasks: BackgroundTasks):
    background_tasks.add_task(presence_service.monitor_expirations)
    return {"status":"monitor_started"}
