import uuid

from tests.conftest import auth_header


# ── POST /api/v1/vehicles ──────────────────────────────────────────────

async def test_create_vehicle(client, fleet_manager):
    reg = f"TEST-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/v1/vehicles/",
        json={
            "registration_number": reg,
            "name": "Test Van",
            "type": "Van",
            "max_load_kg": 600,
            "odometer_km": 500,
            "acquisition_cost": 700000,
            "region": "Mumbai",
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["registration_number"] == reg
    assert data["name"] == "Test Van"
    assert data["status"] == "available"


async def test_create_vehicle_duplicate_registration(client, fleet_manager, seed_vehicle):
    resp = await client.post(
        "/api/v1/vehicles/",
        json={
            "registration_number": seed_vehicle.registration_number,
            "name": "Duplicate",
            "type": "Van",
            "max_load_kg": 500,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


async def test_create_vehicle_unauthorized(client, dispatcher_user):
    resp = await client.post(
        "/api/v1/vehicles/",
        json={
            "registration_number": f"TEST-{uuid.uuid4().hex[:8]}",
            "name": "Unauthorized",
            "type": "Van",
            "max_load_kg": 500,
        },
        headers=auth_header(dispatcher_user),
    )
    assert resp.status_code == 403


async def test_create_vehicle_no_auth(client):
    resp = await client.post(
        "/api/v1/vehicles/",
        json={
            "registration_number": f"TEST-{uuid.uuid4().hex[:8]}",
            "name": "No Auth",
            "type": "Van",
            "max_load_kg": 500,
        },
    )
    assert resp.status_code == 401


# ── GET /api/v1/vehicles ───────────────────────────────────────────────

async def test_list_vehicles(client, seed_vehicle):
    resp = await client.get(f"/api/v1/vehicles/?search={seed_vehicle.registration_number}")
    assert resp.status_code == 200
    body = resp.json()
    ids = [v["id"] for v in body["items"]]
    assert str(seed_vehicle.id) in ids


async def test_list_vehicles_filter_status(client, seed_vehicle):
    resp = await client.get(f"/api/v1/vehicles/?status=available&search={seed_vehicle.registration_number}")
    assert resp.status_code == 200
    ids = [v["id"] for v in resp.json()["items"]]
    assert str(seed_vehicle.id) in ids


async def test_list_vehicles_filter_type(client, seed_vehicle):
    resp = await client.get(f"/api/v1/vehicles/?type=Van&search={seed_vehicle.registration_number}")
    assert resp.status_code == 200
    ids = [v["id"] for v in resp.json()["items"]]
    assert str(seed_vehicle.id) in ids


async def test_list_vehicles_search(client, seed_vehicle):
    resp = await client.get(f"/api/v1/vehicles/?search={seed_vehicle.registration_number}")
    assert resp.status_code == 200
    ids = [v["id"] for v in resp.json()["items"]]
    assert str(seed_vehicle.id) in ids


async def test_list_vehicles_pagination(client, seed_vehicle):
    resp = await client.get(f"/api/v1/vehicles/?page=1&page_size=100")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 100
    assert body["total"] >= 1


# ── GET /api/v1/vehicles/{id} ──────────────────────────────────────────

async def test_get_vehicle(client, seed_vehicle):
    resp = await client.get(f"/api/v1/vehicles/{seed_vehicle.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(seed_vehicle.id)


async def test_get_vehicle_not_found(client):
    resp = await client.get(f"/api/v1/vehicles/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /api/v1/vehicles/{id} ────────────────────────────────────────

async def test_update_vehicle(client, fleet_manager, seed_vehicle):
    resp = await client.patch(
        f"/api/v1/vehicles/{seed_vehicle.id}",
        json={"name": "Updated Van", "region": "Delhi"},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Van"
    assert data["region"] == "Delhi"


async def test_update_vehicle_not_found(client, fleet_manager):
    resp = await client.patch(
        f"/api/v1/vehicles/{uuid.uuid4()}",
        json={"name": "Ghost"},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 404


# ── DELETE /api/v1/vehicles/{id}  (soft-delete → retired) ──────────────

async def test_delete_vehicle_soft(client, fleet_manager, seed_vehicle):
    resp = await client.delete(
        f"/api/v1/vehicles/{seed_vehicle.id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "retired"


async def test_delete_vehicle_not_found(client, fleet_manager):
    resp = await client.delete(
        f"/api/v1/vehicles/{uuid.uuid4()}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 404


# ── GET /api/v1/vehicles/available ──────────────────────────────────────

async def test_list_available_vehicles(client, fleet_manager, seed_vehicle):
    resp = await client.get(
        "/api/v1/vehicles/available",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [v["id"] for v in resp.json()]
    assert str(seed_vehicle.id) in ids


async def test_list_available_vehicles_requires_role(client, seed_vehicle):
    resp = await client.get("/api/v1/vehicles/available")
    assert resp.status_code == 401
