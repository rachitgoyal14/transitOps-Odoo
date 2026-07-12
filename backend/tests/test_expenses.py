import uuid
from datetime import date

from tests.conftest import auth_header


# ── POST /api/v1/expenses ──────────────────────────────────────────────

async def test_create_expense(client, fleet_manager, seed_vehicle):
    resp = await client.post(
        "/api/v1/expenses/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "category": "toll",
            "amount": 250,
            "description": "NH-8 toll",
            "expense_date": date.today().isoformat(),
        },
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "toll"
    assert data["amount"] == 250
    assert data["created_by"] == str(fleet_manager.id)


async def test_create_expense_by_dispatcher(client, dispatcher_user, seed_vehicle):
    resp = await client.post(
        "/api/v1/expenses/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "category": "parking",
            "amount": 50,
        },
        headers=auth_header(dispatcher_user),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "parking"
    assert data["created_by"] == str(dispatcher_user.id)


async def test_create_expense_unauthorized(client, safety_officer, seed_vehicle):
    resp = await client.post(
        "/api/v1/expenses/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "category": "other",
            "amount": 100,
        },
        headers=auth_header(safety_officer),
    )
    assert resp.status_code == 403


async def test_create_expense_no_auth(client, seed_vehicle):
    resp = await client.post(
        "/api/v1/expenses/",
        json={
            "vehicle_id": str(seed_vehicle.id),
            "category": "other",
            "amount": 100,
        },
    )
    assert resp.status_code == 401


# ── GET /api/v1/expenses ───────────────────────────────────────────────

async def test_list_expenses(client, fleet_manager, seed_expense):
    resp = await client.get(
        f"/api/v1/expenses/?vehicle_id={seed_expense.vehicle_id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["items"]]
    assert str(seed_expense.id) in ids


async def test_list_expenses_filter_category(
    client, fleet_manager, seed_expense
):
    resp = await client.get(
        f"/api/v1/expenses/?category=toll&vehicle_id={seed_expense.vehicle_id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["items"]]
    assert str(seed_expense.id) in ids

    resp2 = await client.get(
        f"/api/v1/expenses/?category=parking&vehicle_id={seed_expense.vehicle_id}",
        headers=auth_header(fleet_manager),
    )
    assert resp2.status_code == 200
    ids2 = [e["id"] for e in resp2.json()["items"]]
    assert str(seed_expense.id) not in ids2


async def test_list_expenses_filter_vehicle(
    client, fleet_manager, seed_expense, seed_vehicle
):
    resp = await client.get(
        f"/api/v1/expenses/?vehicle_id={seed_vehicle.id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["items"]]
    assert str(seed_expense.id) in ids


# ── GET /api/v1/expenses/{id} ──────────────────────────────────────────

async def test_get_expense(client, seed_expense):
    resp = await client.get(f"/api/v1/expenses/{seed_expense.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(seed_expense.id)


async def test_get_expense_not_found(client):
    resp = await client.get(f"/api/v1/expenses/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── DELETE /api/v1/expenses/{id} ───────────────────────────────────────

async def test_delete_expense(client, fleet_manager, seed_expense):
    resp = await client.delete(
        f"/api/v1/expenses/{seed_expense.id}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 204


async def test_delete_expense_unauthorized(client, dispatcher_user, seed_expense):
    resp = await client.delete(
        f"/api/v1/expenses/{seed_expense.id}",
        headers=auth_header(dispatcher_user),
    )
    assert resp.status_code == 403


async def test_delete_expense_not_found(client, fleet_manager):
    resp = await client.delete(
        f"/api/v1/expenses/{uuid.uuid4()}",
        headers=auth_header(fleet_manager),
    )
    assert resp.status_code == 404
