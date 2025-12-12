import pytest
from backend.services.analytics_service import analytics_service

@pytest.mark.asyncio
async def test_ingest_and_aggregate():
    await analytics_service.ingest("u1","page.view",{"path":"/home"})
    res = await analytics_service.aggregate_daily()
    assert isinstance(res, dict)
    assert res.get("page.view", 0) >= 1
