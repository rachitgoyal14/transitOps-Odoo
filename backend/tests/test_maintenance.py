import uuid
from datetime import date

from tests.conftest import auth_header


# ── POST /api/v1/maintenance ───────────────────────────────────────────

async def test_create_maintenance(client, fleet_manager, seed_vehicle):
    resp = await client.post(
        "/api/v1/maintenance/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "type": f"Service-{uuid.uuid4().hex[:6]}",
            "description": "Routine 10k service",
            "cost": 2500,
            "scheduled_date": date.today().isoformat(),
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "open"


async def test_create_maintenance_sets_vehicle_in_shop(
    client, fleet_manager, seed_vehicle, db
):
    """BR-09: creating maintenance auto-sets vehicle to in_shop."""
    resp = await client.post(
        "/api/v1/maintenance/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "type": f"Tyre-{uuid.uuid4().hex[:6]}",
            "cost": 8000,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 201

    await db.refresh(seed_vehicle)
    assert seed_vehicle.status.value == "in_shop"


async def test_create_maintenance_by_safety_officer(client, safety_officer, seed_vehicle):
    resp = await client.post(
        "/api/v1/maintenance/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "type": f"Brake-{uuid.uuid4().hex[:6]}",
            "cost": 1200,
        },
        headers=auth_header(safety_officer),
    )
    assert resp.status_code == 201


async def test_create_maintenance_unauthorized(client, dispatcher_user, seed_vehicle):
    resp = await client.post(
        "/api/v1/maintenance/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "type": f"Oil-{uuid.uuid4().hex[:6]}",
            "cost": 100,
        },
        headers=auth_header(dispatcher_user),
    )
    assert resp.status_code == 403


async def test_create_maintenance_vehicle_not_found(client, fleet_manager):
    resp = await client.post(
        "/api/v1/maintenance/",
        json={
            "vehicle_id": str(uuid.uuid4()),
            "type": "Oil Change",
            "cost": 100,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 404


# ── GET /api/v1/maintenance ────────────────────────────────────────────

async def test_list_maintenance(client, seed_maintenance):
    resp = await client.get(f"/api/v1/maintenance/?vehicle_id={seed_maintenance.vehicle_id}")
    assert resp.status_code == 200
    ids = [m["id"] for m in resp.json()["items"]]
    assert str(seed_maintenance.id) in ids


async def test_list_maintenance_filter_status(client, seed_maintenance):
    resp = await client.get(
        f"/api/v1/maintenance/?status=open&vehicle_id={seed_maintenance.vehicle_id}"
    )
    assert resp.status_code == 200
    ids = [m["id"] for m in resp.json()["items"]]
    assert str(seed_maintenance.id) in ids


# ── GET /api/v1/maintenance/{id} ──────────────────────────────────────

async def test_get_maintenance(client, seed_maintenance):
    resp = await client.get(f"/api/v1/maintenance/{seed_maintenance.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(seed_maintenance.id)


async def test_get_maintenance_not_found(client):
    resp = await client.get(f"/api/v1/maintenance/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /api/v1/maintenance/{id} ────────────────────────────────────

async def test_update_maintenance_open(client, fleet_manager, seed_maintenance):
    resp = await client.patch(
        f"/api/v1/maintenance/{seed_maintenance.id}",
        json={"cost": 3000, "description": "Updated desc"},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    assert resp.json()["cost"] == 3000
    assert resp.json()["description"] == "Updated desc"


async def test_update_maintenance_closed_rejected(
    client, fleet_manager, seed_maintenance, db
):
    from app.models.maintenance_log import MaintenanceStatus

    seed_maintenance.status = MaintenanceStatus.closed
    await db.commit()

    resp = await client.patch(
        f"/api/v1/maintenance/{seed_maintenance.id}",
        json={"cost": 9999},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 400
    assert "closed" in resp.json()["detail"].lower()


# ── POST /api/v1/maintenance/{id}/close ────────────────────────────────

async def test_close_maintenance(client, fleet_manager, seed_maintenance):
    resp = await client.post(
        f"/api/v1/maintenance/{seed_maintenance.id}/close",
        json={
            "completed_date": date.today().isoformat(),
            "final_cost": 2800,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "closed"


async def test_close_maintenance_restores_vehicle(
    client, fleet_manager, seed_maintenance, seed_vehicle, db
):
    """BR-10: closing maintenance restores vehicle to available."""
    await client.post(
        f"/api/v1/maintenance/{seed_maintenance.id}/close",
        json={
            "completed_date": date.today().isoformat(),
            "final_cost": 2800,
        },
        headers=auth_header(fleet_manager),
    )
    await db.refresh(seed_vehicle)
    assert seed_vehicle.status.value == "available"


async def test_close_maintenance_already_closed(
    client, fleet_manager, seed_maintenance, db
):
    from app.models.maintenance_log import MaintenanceStatus

    seed_maintenance.status = MaintenanceStatus.closed
    await db.commit()

    resp = await client.post(
        f"/api/v1/maintenance/{seed_maintenance.id}/close",
        json={"completed_date": date.today().isoformat()},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 400
    assert "already closed" in resp.json()["detail"].lower()


async def test_close_maintenance_retired_vehicle_not_restored(
    client, fleet_manager, seed_maintenance, seed_vehicle, db
):
    """BR-11: retired vehicle stays retired even after maintenance close."""
    from app.models.vehicle import VehicleStatus

    seed_vehicle.status = VehicleStatus.retired
    await db.commit()

    await client.post(
        f"/api/v1/maintenance/{seed_maintenance.id}/close",
        json={"completed_date": date.today().isoformat()},
        headers=auth_header(fleet_manager),
    )
    await db.refresh(seed_vehicle)
    assert seed_vehicle.status.value == "retired"
