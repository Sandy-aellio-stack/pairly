import pytest
from backend.services.notification_service import notification_service

@pytest.mark.asyncio
async def test_send_and_list():
    n = await notification_service.send_in_app("u1","Hello","Welcome",{})
    assert n.user_id == "u1"
    unread = await notification_service.list_unread("u1")
    assert any(x.id == n.id for x in unread)
