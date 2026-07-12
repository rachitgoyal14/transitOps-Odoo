from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.models.briefing_cache import BriefingCache
from tests.conftest import auth_header, _test_session_factory


async def _clear_briefing_cache():
    async with _test_session_factory() as session:
        await session.execute(delete(BriefingCache))
        await session.commit()


async def test_briefing_returns_content(client):
    await _clear_briefing_cache()
    resp = await client.post("/api/v1/dashboard/briefing")
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert isinstance(data["content"], str)
    assert data["cached"] is False
    assert "generated_at" in data


async def test_briefing_is_cached_on_second_call(client):
    await _clear_briefing_cache()
    resp1 = await client.post("/api/v1/dashboard/briefing")
    assert resp1.status_code == 200
    assert resp1.json()["cached"] is False

    resp2 = await client.post("/api/v1/dashboard/briefing")
    assert resp2.status_code == 200
    assert resp2.json()["cached"] is True
    assert resp2.json()["content"] == resp1.json()["content"]


async def test_briefing_cache_expires(client, db):
    await _clear_briefing_cache()

    cache = BriefingCache(
        content="Old cached briefing",
        generated_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db.add(cache)
    await db.commit()

    resp = await client.post("/api/v1/dashboard/briefing")
    assert resp.status_code == 200
    assert resp.json()["cached"] is False
    assert resp.json()["content"] != "Old cached briefing"
