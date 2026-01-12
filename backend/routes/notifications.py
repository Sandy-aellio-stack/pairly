from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.services.notification_service import notification_service
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/api/legacy/notifications", tags=["Legacy Notifications"])

class SendIn(BaseModel):
    user_id: str
    title: str
    body: str
    meta: dict = {}

@router.post("/send")
async def send(payload: SendIn):
    n = await notification_service.send_in_app(payload.user_id, payload.title, payload.body, payload.meta)
    return {"id": str(n.id), "status":"queued"}

@router.get("/unread")
async def unread(user=Depends(get_current_user)):
    items = await notification_service.list_unread(str(user.id))
    return [{"id": str(i.id), "title": i.title, "body": i.body, "created_at": i.created_at} for i in items]

@router.post("/{notif_id}/read")
async def mark_read(notif_id: str):
    n = await notification_service.mark_read(notif_id)
    return {"status":"ok" if n else "not_found"}
