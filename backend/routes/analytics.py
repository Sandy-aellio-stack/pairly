from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.services.analytics_service import analytics_service
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

class IngestIn(BaseModel):
    event_type: str
    payload: dict = {}
    user_id: Optional[str] = None

@router.post("/ingest")
async def ingest(payload: IngestIn, user=Depends(get_current_user)):
    uid = payload.user_id or str(user.id)
    await analytics_service.ingest(uid, payload.event_type, payload.payload)
    return {"status":"ok"}

@router.get("/daily")
async def daily(day: Optional[str] = None):
    # optional day ISO YYYY-MM-DD
    d = datetime.strptime(day, "%Y-%m-%d") if day else None
    res = await analytics_service.aggregate_daily(d)
    return res

@router.get("/user/{user_id}")
async def user_events(user_id: str):
    return await analytics_service.get_user_events(user_id)
