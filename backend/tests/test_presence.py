import pytest
import asyncio
from backend.services.presence_service import presence_service
from backend.models.presence import Presence
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_heartbeat_and_get(monkeypatch):
    user_id = "u-test-1"
    await presence_service.heartbeat(user_id, {"ip":"1.1.1.1"})
    res = await presence_service.get(user_id)
    assert res["status"] == "online"
    await presence_service.mark_offline(user_id)
    res2 = await presence_service.get(user_id)
    assert res2["status"] == "offline"
