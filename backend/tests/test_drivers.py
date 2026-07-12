import uuid
from datetime import date, timedelta

from tests.conftest import auth_header


# ── POST /api/v1/drivers ───────────────────────────────────────────────

async def test_create_driver(client, fleet_manager):
    lic = f"DL-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/v1/drivers/",
        json={
            "full_name": "Jane Smith",
            "license_number": lic,
            "license_category": "LMV",
            "license_expiry": (date.today() + timedelta(days=400)).isoformat(),
            "contact_number": "+91-1234567890",
            "safety_score": 8.0,
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Jane Smith"
    assert data["license_number"] == lic


async def test_create_driver_duplicate_license(client, fleet_manager, seed_driver):
    resp = await client.post(
        "/api/v1/drivers/",
        json={
            "full_name": "Duplicate",
            "license_number": seed_driver.license_number,
            "license_category": "LMV",
            "license_expiry": (date.today() + timedelta(days=200)).isoformat(),
            "contact_number": "+91-0000000000",
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 409


async def test_create_driver_by_safety_officer(client, safety_officer):
    resp = await client.post(
        "/api/v1/drivers/",
        json={
            "full_name": "By Safety",
            "license_number": f"DL-{uuid.uuid4().hex[:8]}",
            "license_category": "HMV",
            "license_expiry": (date.today() + timedelta(days=300)).isoformat(),
            "contact_number": "+91-1111111111",
        },
        headers=auth_header(safety_officer),
    )
    assert resp.status_code == 201


async def test_create_driver_unauthorized(client, financial_analyst):
    resp = await client.post(
        "/api/v1/drivers/",
        json={
            "full_name": "No Perms",
            "license_number": f"DL-{uuid.uuid4().hex[:8]}",
            "license_category": "LMV",
            "license_expiry": (date.today() + timedelta(days=300)).isoformat(),
            "contact_number": "+91-2222222222",
        },
        headers=auth_header(financial_analyst),
    )
    assert resp.status_code == 403


# ── GET /api/v1/drivers ────────────────────────────────────────────────

async def test_list_drivers(client, seed_driver):
    resp = await client.get(f"/api/v1/drivers/?search={seed_driver.full_name.split()[0]}")
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["items"]]
    assert str(seed_driver.id) in ids


async def test_list_drivers_filter_status(client, seed_driver):
    resp = await client.get(f"/api/v1/drivers/?status=available&search={seed_driver.full_name.split()[0]}")
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["items"]]
    assert str(seed_driver.id) in ids


async def test_list_drivers_search(client, seed_driver):
    resp = await client.get(f"/api/v1/drivers/?search={seed_driver.full_name.split()[0]}")
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["items"]]
    assert str(seed_driver.id) in ids


# ── GET /api/v1/drivers/{id} ──────────────────────────────────────────

async def test_get_driver(client, seed_driver):
    resp = await client.get(f"/api/v1/drivers/{seed_driver.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(seed_driver.id)


async def test_get_driver_not_found(client):
    resp = await client.get(f"/api/v1/drivers/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /api/v1/drivers/{id} ─────────────────────────────────────────

async def test_update_driver(client, fleet_manager, seed_driver):
    resp = await client.patch(
        f"/api/v1/drivers/{seed_driver.id}",
        json={"full_name": "Alex Updated", "safety_score": 9.5},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Alex Updated"
    assert resp.json()["safety_score"] == 9.5


async def test_update_driver_not_found(client, fleet_manager):
    resp = await client.patch(
        f"/api/v1/drivers/{uuid.uuid4()}",
        json={"full_name": "Ghost"},
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 404


# ── DELETE /api/v1/drivers/{id}  (suspend) ─────────────────────────────

async def test_delete_driver_suspend(client, fleet_manager, seed_driver):
    resp = await client.delete(
        f"/api/v1/drivers/{seed_driver.id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "suspended"


async def test_delete_driver_not_found(client, fleet_manager):
    resp = await client.delete(
        f"/api/v1/drivers/{uuid.uuid4()}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 404


# ── GET /api/v1/drivers/available ───────────────────────────────────────

async def test_list_available_drivers(client, fleet_manager, seed_driver):
    resp = await client.get(
        "/api/v1/drivers/available",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert str(seed_driver.id) in ids


async def test_list_available_drivers_excludes_expired(
    client, fleet_manager, seed_driver_expired_license
):
    resp = await client.get(
        "/api/v1/drivers/available",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert str(seed_driver_expired_license.id) not in ids


# ── GET /api/v1/drivers/expiring-licenses ───────────────────────────────

async def test_expiring_licenses(client, fleet_manager, seed_driver_expired_license, db):
    from app.models.driver import Driver, DriverStatus

    drv = Driver(
        full_name=f"Expiring Soon {uuid.uuid4().hex[:6]}",
        license_number=f"DL-EXP-{uuid.uuid4().hex[:6]}",
        license_category="LMV",
        license_expiry=date.today() + timedelta(days=15),
        contact_number="+91-9999999999",
        safety_score=8.0,
        status=DriverStatus.available,
    )
    db.add(drv)
    await db.flush()
    await db.refresh(drv)
    await db.commit()

    from tests.conftest import _created_ids
    _created_ids["drivers"].append(drv.id)

    resp = await client.get(
        "/api/v1/drivers/expiring-licenses",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert str(drv.id) in ids


async def test_expiring_licenses_requires_role(client):
    resp = await client.get("/api/v1/drivers/expiring-licenses")
    assert resp.status_code == 401
