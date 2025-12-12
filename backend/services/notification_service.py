from backend.models.notification import Notification
from typing import List

class NotificationService:
    async def send_in_app(self, user_id: str, title: str, body: str, meta: dict = {}):
        n = Notification(user_id=user_id, title=title, body=body, meta=meta)
        await n.insert()
        # also log to structured logger under notifications
        return n

    async def list_unread(self, user_id: str, limit: int = 50):
        q = Notification.find({"user_id": user_id, "read": False}).sort("-created_at").limit(limit)
        out = []
        async for n in q:
            out.append(n)
        return out

    async def mark_read(self, notification_id: str):
        n = await Notification.get(notification_id)
        if n:
            n.read = True
            await n.save()
        return n

notification_service = NotificationService()
