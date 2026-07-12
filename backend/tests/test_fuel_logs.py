import uuid
from datetime import date

from tests.conftest import auth_header


# ── POST /api/v1/fuel-logs ─────────────────────────────────────────────

async def test_create_fuel_log(client, fleet_manager, seed_vehicle):
    resp = await client.post(
        "/api/v1/fuel-logs/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "liters": 45.5,
            "cost_per_liter": 106.72,
            "odometer_at_fill": 15000,
            "filled_at": date.today().isoformat(),
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["liters"] == 45.5
    assert data["cost_per_liter"] == 106.72


async def test_create_fuel_log_by_dispatcher(client, dispatcher_user, seed_vehicle):
    resp = await client.post(
        "/api/v1/fuel-logs/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "liters": 30,
            "cost_per_liter": 105,
        },
        headers=auth_header(dispatcher_user),
    )
    assert resp.status_code == 201


async def test_create_fuel_log_unauthorized(client, financial_analyst, seed_vehicle):
    resp = await client.post(
        "/api/v1/fuel-logs/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "liters": 30,
            "cost_per_liter": 105,
        },
        headers=auth_header(financial_analyst),
    )
    assert resp.status_code == 403


# ── GET /api/v1/fuel-logs ──────────────────────────────────────────────

async def test_list_fuel_logs(client, fleet_manager, seed_fuel_log):
    resp = await client.get(
        f"/api/v1/fuel-logs/?vehicle_id={seed_fuel_log.vehicle_id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [fl["id"] for fl in resp.json()["items"]]
    assert str(seed_fuel_log.id) in ids


async def test_list_fuel_logs_filter_vehicle(
    client, fleet_manager, seed_fuel_log, seed_vehicle
):
    resp = await client.get(
        f"/api/v1/fuel-logs/?vehicle_id={seed_vehicle.id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [fl["id"] for fl in resp.json()["items"]]
    assert str(seed_fuel_log.id) in ids


# ── GET /api/v1/fuel-logs/{id} ─────────────────────────────────────────

async def test_get_fuel_log(client, seed_fuel_log):
    resp = await client.get(f"/api/v1/fuel-logs/{seed_fuel_log.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(seed_fuel_log.id)


async def test_get_fuel_log_not_found(client):
    resp = await client.get(f"/api/v1/fuel-logs/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── DELETE /api/v1/fuel-logs/{id} ──────────────────────────────────────

async def test_delete_fuel_log(client, fleet_manager, seed_fuel_log):
    resp = await client.delete(
        f"/api/v1/fuel-logs/{seed_fuel_log.id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 204


async def test_delete_fuel_log_unauthorized(client, dispatcher_user, seed_fuel_log):
    resp = await client.delete(
        f"/api/v1/fuel-logs/{seed_fuel_log.id}",
        headers=auth_header(dispatcher_user),
    )
    assert resp.status_code == 403


async def test_delete_fuel_log_not_found(client, fleet_manager):
    resp = await client.delete(
        f"/api/v1/fuel-logs/{uuid.uuid4()}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 404
import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models import Vehicle
from app.models.enums import VehicleStatus

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def admin_headers(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": settings.default_admin_email, "password": settings.default_admin_password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def vehicle(db: AsyncSession) -> Vehicle:
    veh = Vehicle(
        registration_number=f"REG-{uuid.uuid4().hex[:10].upper()}",
        name="Test Fuel Truck",
        type="Heavy Truck",
        max_load_kg=Decimal("1500.00"),
        odometer_km=Decimal("100.00"),
        acquisition_cost=Decimal("50000.00"),
        status=VehicleStatus.available
    )
    db.add(veh)
    await db.commit()
    await db.refresh(veh)
    return veh

@pytest.mark.anyio
async def test_create_fuel_log_success(client: AsyncClient, admin_headers: dict, vehicle: Vehicle):
    payload = {
        "vehicle_id": str(vehicle.id),
        "liters": 50.0,
        "cost_per_liter": 2.50,
        "odometer_at_fill": 150.0,
        "filled_at": "2026-07-12"
    }
    response = await client.post(
        "/api/v1/fuel-logs/",
        json=payload,
        headers=admin_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["liters"] == 50.0
    assert data["cost_per_liter"] == 2.50
    assert data["total_cost"] == 125.0
