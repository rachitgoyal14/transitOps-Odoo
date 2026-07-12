from app.api.v1 import autopilot as autopilot_module
from tests.conftest import auth_header


async def _reset_autopilot_state():
    autopilot_module._autopilot_enabled = False
    autopilot_module._autopilot_events.clear()


# ── POST /api/v1/trips/autopilot/toggle ────────────────────────────────

async def test_toggle_autopilot_enable(client, fleet_manager):
    await _reset_autopilot_state()
    resp = await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": True},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True
    assert "enabled" in data["message"].lower()


async def test_toggle_autopilot_disable(client, fleet_manager):
    await _reset_autopilot_state()
    resp = await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": False},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


async def test_toggle_autopilot_unauthorized(client, safety_officer):
    await _reset_autopilot_state()
    resp = await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": True},
        headers=auth_header(safety_officer),
    )
    assert resp.status_code == 403


async def test_toggle_autopilot_no_auth(client):
    await _reset_autopilot_state()
    resp = await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": True},
    )
    assert resp.status_code == 401


# ── GET /api/v1/trips/autopilot/feed ───────────────────────────────────

async def test_feed_returns_empty_when_disabled(client, fleet_manager):
    await _reset_autopilot_state()
    resp = await client.get(
        "/api/v1/trips/autopilot/feed",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["autopilot_enabled"] is False
    assert data["events"] == []
    assert data["total_dispatched"] == 0
    assert data["total_escalated"] == 0


async def test_feed_returns_empty_when_enabled_no_trips(client, fleet_manager):
    await _reset_autopilot_state()
    await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": True},
        headers=auth_header(fleet_manager),
    )
    resp = await client.get(
        "/api/v1/trips/autopilot/feed",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    assert resp.json()["autopilot_enabled"] is True


async def test_feed_requires_auth(client):
    resp = await client.get("/api/v1/trips/autopilot/feed")
    assert resp.status_code == 401


async def test_feed_requires_dispatcher_or_manager(client, safety_officer):
    resp = await client.get(
        "/api/v1/trips/autopilot/feed",
        headers=auth_header(safety_officer),
    )
    assert resp.status_code == 403


async def test_feed_by_dispatcher(client, dispatcher_user):
    await _reset_autopilot_state()
    resp = await client.get(
        "/api/v1/trips/autopilot/feed",
        headers=auth_header(dispatcher_user),
    )
    assert resp.status_code == 200
