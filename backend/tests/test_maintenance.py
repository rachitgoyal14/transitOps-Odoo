import uuid
from datetime import date
from decimal import Decimal

from tests.conftest import auth_header, _created_ids

from app.models import Vehicle, Driver, Role, User
from app.models.enums import VehicleStatus, DriverStatus
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


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
    seed_vehicle.status = VehicleStatus.retired
    await db.commit()

    await client.post(
        f"/api/v1/maintenance/{seed_maintenance.id}/close",
        json={"completed_date": date.today().isoformat()},
        headers=auth_header(fleet_manager),
    )
    await db.refresh(seed_vehicle)
    assert seed_vehicle.status.value == "retired"


# ── Flow / integration tests ────────────────────────────────────────────

async def _create_user_with_role(db: AsyncSession, client, role_name: str) -> dict:
    role_stmt = select(Role).where(Role.name == role_name)
    role_result = await db.execute(role_stmt)
    role = role_result.scalar_one()

    email = f"{role_name}-{uuid.uuid4().hex[:6]}@test.com"
    password = "TestPassword123!"
    user = User(
        full_name=f"Test {role_name}",
        email=email,
        hashed_password=hash_password(password),
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    await db.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_maintenance_flow_success(client, fleet_manager, db):
    headers = await _create_user_with_role(db, client, "fleet_manager")
    dispatcher_headers = await _create_user_with_role(db, client, "dispatcher")

    veh = Vehicle(
        registration_number=f"REG-{uuid.uuid4().hex[:10].upper()}",
        name="Maintenance Flow Vehicle",
        type="Van",
        max_load_kg=Decimal("800.00"),
        odometer_km=Decimal("12000.00"),
        acquisition_cost=Decimal("25000.00"),
        status=VehicleStatus.available,
        lat=Decimal("23.2156"),
        lng=Decimal("72.6369")
    )
    db.add(veh)
    await db.commit()
    await db.refresh(veh)
    _created_ids["vehicles"].append(veh.id)

    res = await client.get("/api/v1/vehicles/available", headers=dispatcher_headers)
    assert res.status_code == 200
    available_ids = [v["id"] for v in res.json()]
    assert str(veh.id) in available_ids

    payload = {
        "vehicle_id": str(veh.id),
        "type": "Oil Change",
        "description": "Scheduled maintenance",
        "cost": 150.0,
        "odometer_at_service": 12500.0,
        "scheduled_date": "2026-07-12"
    }
    res = await client.post("/api/v1/maintenance/", json=payload, headers=headers)
    assert res.status_code == 201
    log_data = res.json()
    log_id = log_data["id"]
    assert log_data["status"] == "open"

    await db.refresh(veh)
    assert veh.status == VehicleStatus.in_shop

    res = await client.get("/api/v1/vehicles/available", headers=dispatcher_headers)
    assert res.status_code == 200
    available_ids = [v["id"] for v in res.json()]
    assert str(veh.id) not in available_ids

    close_payload = {
        "completed_date": "2026-07-13",
        "final_cost": 175.0
    }
    res = await client.post(f"/api/v1/maintenance/{log_id}/close", json=close_payload, headers=headers)
    assert res.status_code == 200
    closed_log = res.json()
    assert closed_log["status"] == "closed"
    assert closed_log["cost"] == 175.0

    await db.refresh(veh)
    assert veh.status == VehicleStatus.available


async def test_maintenance_close_does_not_restore_retired(client, fleet_manager, db):
    headers = await _create_user_with_role(db, client, "fleet_manager")

    veh = Vehicle(
        registration_number=f"REG-{uuid.uuid4().hex[:10].upper()}",
        name="Maintenance Retired Vehicle",
        type="Van",
        max_load_kg=Decimal("800.00"),
        odometer_km=Decimal("12000.00"),
        acquisition_cost=Decimal("25000.00"),
        status=VehicleStatus.available,
        lat=Decimal("23.2156"),
        lng=Decimal("72.6369")
    )
    db.add(veh)
    await db.commit()
    await db.refresh(veh)
    _created_ids["vehicles"].append(veh.id)

    payload = {
        "vehicle_id": str(veh.id),
        "type": "Engine Repair",
        "description": "Major breakdown",
        "cost": 1500.0,
        "odometer_at_service": 12500.0,
        "scheduled_date": "2026-07-12"
    }
    res = await client.post("/api/v1/maintenance/", json=payload, headers=headers)
    assert res.status_code == 201
    log_id = res.json()["id"]

    veh.status = VehicleStatus.retired
    await db.commit()

    close_payload = {
        "completed_date": "2026-07-13",
        "final_cost": 1500.0
    }
    res = await client.post(f"/api/v1/maintenance/{log_id}/close", json=close_payload, headers=headers)
    assert res.status_code == 200

    await db.refresh(veh)
    assert veh.status == VehicleStatus.retired


async def test_maintenance_rbac_flow(client, fleet_manager, db):
    headers = await _create_user_with_role(db, client, "fleet_manager")
    dispatcher_headers = await _create_user_with_role(db, client, "dispatcher")
    financial_headers = await _create_user_with_role(db, client, "financial_analyst")
    safety_headers = await _create_user_with_role(db, client, "safety_officer")

    veh = Vehicle(
        registration_number=f"REG-{uuid.uuid4().hex[:10].upper()}",
        name="Maintenance RBAC Vehicle",
        type="Van",
        max_load_kg=Decimal("800.00"),
        odometer_km=Decimal("12000.00"),
        acquisition_cost=Decimal("25000.00"),
        status=VehicleStatus.available,
        lat=Decimal("23.2156"),
        lng=Decimal("72.6369")
    )
    db.add(veh)
    await db.commit()
    await db.refresh(veh)
    _created_ids["vehicles"].append(veh.id)

    payload = {
        "vehicle_id": str(veh.id),
        "type": "Tire Rotation",
        "description": "Routine check",
        "cost": 50.0,
        "odometer_at_service": 12500.0,
        "scheduled_date": "2026-07-12"
    }

    res = await client.post("/api/v1/maintenance/", json=payload, headers=dispatcher_headers)
    assert res.status_code == 403

    res = await client.post("/api/v1/maintenance/", json=payload, headers=financial_headers)
    assert res.status_code == 403

    res = await client.post("/api/v1/maintenance/", json=payload, headers=safety_headers)
    assert res.status_code == 201
    log_id = res.json()["id"]

    close_payload = {
        "completed_date": "2026-07-13",
        "final_cost": 50.0
    }
    res = await client.post(f"/api/v1/maintenance/{log_id}/close", json=close_payload, headers=dispatcher_headers)
    assert res.status_code == 403

    res = await client.post(f"/api/v1/maintenance/{log_id}/close", json=close_payload, headers=financial_headers)
    assert res.status_code == 403

    res = await client.post(f"/api/v1/maintenance/{log_id}/close", json=close_payload, headers=safety_headers)
    assert res.status_code == 200
