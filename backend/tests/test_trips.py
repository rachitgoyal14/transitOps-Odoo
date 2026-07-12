import uuid

from tests.conftest import auth_header


# ── POST /api/v1/trips ─────────────────────────────────────────────────

async def test_create_trip(client, fleet_manager, seed_vehicle, seed_driver):
    resp = await client.post(
        "/api/v1/trips/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "driver_id": str(seed_driver.id),
            "source": f"TestSrc-{uuid.uuid4().hex[:6]}",
            "destination": f"TestDst-{uuid.uuid4().hex[:6]}",
            "planned_distance_km": 150,
            "cargo_weight_kg": 300,
            "revenue": 5000,
            "notes": "Fragile",
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert data["created_by"] == str(fleet_manager.id)


async def test_create_trip_by_dispatcher(client, dispatcher_user, seed_vehicle, seed_driver):
    resp = await client.post(
        "/api/v1/trips/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "driver_id": str(seed_driver.id),
            "source": f"Src-{uuid.uuid4().hex[:6]}",
            "destination": f"Dst-{uuid.uuid4().hex[:6]}",
            "planned_distance_km": 10,
            "cargo_weight_kg": 10,
        },
        headers=auth_header(dispatcher_user),
    )
    assert resp.status_code == 201


# ── BR-02: vehicle must be available ────────────────────────────────────

async def test_create_trip_vehicle_not_available(
    client, fleet_manager, seed_vehicle_unavailable, seed_driver
):
    resp = await client.post(
        "/api/v1/trips/",
        json={
            "vehicle_id": str(seed_vehicle_unavailable.id),
            "driver_id": str(seed_driver.id),
            "source": "A",
            "destination": "B",
            "planned_distance_km": 10,
            "cargo_weight_kg": 10,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 400
    assert "not available" in resp.json()["detail"].lower()


# ── BR-03: driver must be available ────────────────────────────────────

async def test_create_trip_driver_not_available(
    client, fleet_manager, seed_vehicle, seed_driver_unavailable
):
    resp = await client.post(
        "/api/v1/trips/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "driver_id": str(seed_driver_unavailable.id),
            "source": "A",
            "destination": "B",
            "planned_distance_km": 10,
            "cargo_weight_kg": 10,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 400
    assert "cannot be assigned" in resp.json()["detail"].lower()


# ── BR-04: driver license must not be expired ───────────────────────────

async def test_create_trip_expired_license(
    client, fleet_manager, seed_vehicle, seed_driver_expired_license
):
    resp = await client.post(
        "/api/v1/trips/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "driver_id": str(seed_driver_expired_license.id),
            "source": "A",
            "destination": "B",
            "planned_distance_km": 10,
            "cargo_weight_kg": 10,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


# ── BR-05: cargo weight <= vehicle max load ─────────────────────────────

async def test_create_trip_cargo_exceeds_capacity(
    client, fleet_manager, seed_vehicle, seed_driver
):
    resp = await client.post(
        "/api/v1/trips/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "driver_id": str(seed_driver.id),
            "source": "A",
            "destination": "B",
            "planned_distance_km": 10,
            "cargo_weight_kg": 9999,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 400
    assert "exceeds" in resp.json()["detail"].lower()


async def test_create_trip_not_found_vehicle(client, fleet_manager, seed_driver):
    resp = await client.post(
        "/api/v1/trips/",
        json={
            "vehicle_id": str(uuid.uuid4()),
            "driver_id": str(seed_driver.id),
            "source": "A",
            "destination": "B",
            "planned_distance_km": 10,
            "cargo_weight_kg": 10,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 404


# ── GET /api/v1/trips ──────────────────────────────────────────────────

async def test_list_trips(client, seed_trip):
    resp = await client.get(f"/api/v1/trips/?vehicle_id={seed_trip.vehicle_id}")
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()["items"]]
    assert str(seed_trip.id) in ids


async def test_list_trips_filter_status(client, seed_trip):
    resp = await client.get(f"/api/v1/trips/?status=draft&vehicle_id={seed_trip.vehicle_id}")
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()["items"]]
    assert str(seed_trip.id) in ids


# ── GET /api/v1/trips/{id} ────────────────────────────────────────────

async def test_get_trip(client, seed_trip):
    resp = await client.get(f"/api/v1/trips/{seed_trip.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(seed_trip.id)


async def test_get_trip_not_found(client):
    resp = await client.get(f"/api/v1/trips/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /api/v1/trips/{id} ──────────────────────────────────────────

async def test_update_trip_draft(client, fleet_manager, seed_trip):
    resp = await client.patch(
        f"/api/v1/trips/{seed_trip.id}",
        json={"notes": "Updated notes", "revenue": 7500},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Updated notes"
    assert resp.json()["revenue"] == 7500


async def test_update_trip_not_draft(client, fleet_manager, seed_trip, db):
    from app.models.trip import TripStatus

    seed_trip.status = TripStatus.dispatched
    await db.commit()

    resp = await client.patch(
        f"/api/v1/trips/{seed_trip.id}",
        json={"notes": "Cannot update"},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 400
    assert "draft" in resp.json()["detail"].lower()


# ── Stubs (501) ────────────────────────────────────────────────────────

async def test_dispatch_stub(client, seed_trip):
    resp = await client.post(f"/api/v1/trips/{seed_trip.id}/dispatch")
    assert resp.status_code == 501


async def test_complete_stub(client, seed_trip):
    resp = await client.post(f"/api/v1/trips/{seed_trip.id}/complete")
    assert resp.status_code == 501


async def test_cancel_stub(client, seed_trip):
    resp = await client.post(f"/api/v1/trips/{seed_trip.id}/cancel")
    assert resp.status_code == 501


# ── POST /api/v1/trips/suggest ─────────────────────────────────────────

async def test_suggest_dispatch(client, fleet_manager, seed_vehicle, seed_driver):
    resp = await client.post(
        "/api/v1/trips/suggest",
        json={
            "source": "Mumbai",
            "destination": "Pune",
            "cargo_weight_kg": 100,
            "planned_distance_km": 150,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data


async def test_suggest_dispatch_no_candidates(
    client, fleet_manager, seed_vehicle_small, seed_driver
):
    resp = await client.post(
        "/api/v1/trips/suggest",
        json={
            "source": "A",
            "destination": "B",
            "cargo_weight_kg": 9999,
            "planned_distance_km": 10,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    assert resp.json()["suggestions"] == []


async def test_suggest_dispatch_requires_auth(client):
    resp = await client.post(
        "/api/v1/trips/suggest",
        json={
            "source": "A",
            "destination": "B",
            "cargo_weight_kg": 100,
            "planned_distance_km": 50,
        },
    )
    assert resp.status_code == 401
