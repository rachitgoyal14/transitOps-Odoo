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


# ── Functional integration tests ────────────────────────────────────────

import uuid
import json
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch

from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Vehicle, Driver, Trip, Role, User
from app.models.enums import VehicleStatus, DriverStatus, TripStatus
from app.core.security import hash_password
from tests.conftest import _created_ids


async def _create_user_with_role(db: AsyncSession, client, role_name: str) -> dict:
    from sqlalchemy.future import select
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


async def test_autopilot_toggle_flow(client, fleet_manager, db):
    headers = await _create_user_with_role(db, client, "fleet_manager")

    res = await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": True},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["enabled"] is True

    res = await client.get("/api/v1/trips/autopilot/feed", headers=headers)
    assert res.status_code == 200
    assert res.json()["autopilot_enabled"] is True

    res = await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": False},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["enabled"] is False

    res = await client.get("/api/v1/trips/autopilot/feed", headers=headers)
    assert res.status_code == 200
    assert res.json()["autopilot_enabled"] is False


async def test_autopilot_single_unambiguous_candidate(client, fleet_manager, db):
    headers = await _create_user_with_role(db, client, "fleet_manager")

    veh = Vehicle(
        registration_number=f"REG-{uuid.uuid4().hex[:10].upper()}",
        name="Autopilot Test Vehicle",
        type="Van",
        max_load_kg=Decimal("1000.00"),
        odometer_km=Decimal("5000.00"),
        acquisition_cost=Decimal("20000.00"),
        status=VehicleStatus.available,
        lat=Decimal("23.2156"),
        lng=Decimal("72.6369")
    )
    db.add(veh)
    await db.commit()
    await db.refresh(veh)
    _created_ids["vehicles"].append(veh.id)

    d = Driver(
        full_name="Autopilot Driver",
        license_number=f"DL-{uuid.uuid4().hex[:10].upper()}",
        license_category="LMV",
        license_expiry=date.today() + timedelta(days=50),
        contact_number="+91-1234567890",
        safety_score=Decimal("9.5"),
        status=DriverStatus.available
    )
    db.add(d)
    await db.commit()
    await db.refresh(d)
    _created_ids["drivers"].append(d.id)

    await db.execute(
        update(Vehicle).where(Vehicle.id != veh.id).values(status=VehicleStatus.retired)
    )
    await db.execute(
        update(Driver).where(Driver.id != d.id).values(status=DriverStatus.suspended)
    )
    await db.execute(
        delete(Trip).where(Trip.status == TripStatus.draft)
    )
    await db.commit()

    trip = Trip(
        vehicle_id=veh.id,
        driver_id=d.id,
        source="Gandhinagar Depot",
        destination="Ahmedabad Hub",
        planned_distance_km=Decimal("35.00"),
        cargo_weight_kg=Decimal("500.00"),
        status=TripStatus.draft
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)
    _created_ids["trips"].append(trip.id)

    await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": True},
        headers=headers
    )

    res = await client.get("/api/v1/trips/autopilot/feed", headers=headers)
    assert res.status_code == 200
    data = res.json()

    event = next((e for e in data["events"] if e.get("trip_id") == str(trip.id)), None)
    assert event is not None
    assert event["event_type"] == "auto_dispatched"
    assert event["status"] == "dispatched"
    assert "Single unambiguous candidate" in event["reason"]

    await db.refresh(trip)
    assert trip.status == TripStatus.dispatched
    assert trip.vehicle_id == veh.id
    assert trip.driver_id == d.id

    await db.refresh(veh)
    assert veh.status == VehicleStatus.on_trip
    await db.refresh(d)
    assert d.status == DriverStatus.on_trip

    await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": False},
        headers=headers
    )


async def test_autopilot_conflict_escalation(client, fleet_manager, db):
    headers = await _create_user_with_role(db, client, "fleet_manager")

    veh = Vehicle(
        registration_number=f"REG-{uuid.uuid4().hex[:10].upper()}",
        name="Autopilot Escalation Vehicle",
        type="Van",
        max_load_kg=Decimal("1000.00"),
        odometer_km=Decimal("5000.00"),
        acquisition_cost=Decimal("20000.00"),
        status=VehicleStatus.available,
        lat=Decimal("23.2156"),
        lng=Decimal("72.6369")
    )
    db.add(veh)
    await db.commit()
    await db.refresh(veh)
    _created_ids["vehicles"].append(veh.id)

    d = Driver(
        full_name="Autopilot Escalation Driver",
        license_number=f"DL-{uuid.uuid4().hex[:10].upper()}",
        license_category="LMV",
        license_expiry=date.today() + timedelta(days=50),
        contact_number="+91-1234567890",
        safety_score=Decimal("9.5"),
        status=DriverStatus.available
    )
    db.add(d)
    await db.commit()
    await db.refresh(d)
    _created_ids["drivers"].append(d.id)

    await db.execute(
        update(Vehicle).where(Vehicle.id != veh.id).values(status=VehicleStatus.retired)
    )
    await db.execute(
        update(Driver).where(Driver.id != d.id).values(status=DriverStatus.suspended)
    )
    await db.execute(
        delete(Trip).where(Trip.status == TripStatus.draft)
    )
    await db.commit()

    trip = Trip(
        vehicle_id=veh.id,
        driver_id=d.id,
        source="Gandhinagar Depot",
        destination="Ahmedabad Hub",
        planned_distance_km=Decimal("35.00"),
        cargo_weight_kg=Decimal("5000.00"),
        status=TripStatus.draft
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)
    _created_ids["trips"].append(trip.id)

    await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": True},
        headers=headers
    )

    res = await client.get("/api/v1/trips/autopilot/feed", headers=headers)
    assert res.status_code == 200
    data = res.json()

    event = next((e for e in data["events"] if e.get("trip_id") == str(trip.id)), None)
    assert event is not None
    assert event["event_type"] == "no_candidates"
    assert event["status"] == "rejected"

    await db.refresh(trip)
    assert trip.status == TripStatus.draft

    await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": False},
        headers=headers
    )


async def test_autopilot_multiple_candidates_mocked_llm(client, fleet_manager, db):
    headers = await _create_user_with_role(db, client, "fleet_manager")

    veh = Vehicle(
        registration_number=f"REG-{uuid.uuid4().hex[:10].upper()}",
        name="Autopilot Vehicle 1",
        type="Van",
        max_load_kg=Decimal("1000.00"),
        odometer_km=Decimal("5000.00"),
        acquisition_cost=Decimal("20000.00"),
        status=VehicleStatus.available,
        lat=Decimal("23.2156"),
        lng=Decimal("72.6369")
    )
    d = Driver(
        full_name="Autopilot Driver 1",
        license_number=f"DL-{uuid.uuid4().hex[:10].upper()}",
        license_category="LMV",
        license_expiry=date.today() + timedelta(days=50),
        contact_number="+91-1234567890",
        safety_score=Decimal("9.5"),
        status=DriverStatus.available
    )
    db.add_all([veh, d])
    await db.commit()
    await db.refresh(veh)
    await db.refresh(d)
    _created_ids["vehicles"].append(veh.id)
    _created_ids["drivers"].append(d.id)

    vehicle2 = Vehicle(
        registration_number=f"REG-{uuid.uuid4().hex[:10].upper()}",
        name="Autopilot Vehicle 2",
        type="Van",
        max_load_kg=Decimal("1200.00"),
        odometer_km=Decimal("5000.00"),
        acquisition_cost=Decimal("20000.00"),
        status=VehicleStatus.available,
        lat=Decimal("23.2156"),
        lng=Decimal("72.6369")
    )
    driver2 = Driver(
        full_name="Autopilot Driver 2",
        license_number=f"DL-{uuid.uuid4().hex[:10].upper()}",
        license_category="LMV",
        license_expiry=date.today() + timedelta(days=50),
        contact_number="+91-0987654321",
        safety_score=Decimal("9.0"),
        status=DriverStatus.available
    )
    db.add_all([vehicle2, driver2])
    await db.commit()
    await db.refresh(vehicle2)
    await db.refresh(driver2)
    _created_ids["vehicles"].append(vehicle2.id)
    _created_ids["drivers"].append(driver2.id)

    await db.execute(
        update(Vehicle).where(Vehicle.id != veh.id, Vehicle.id != vehicle2.id).values(status=VehicleStatus.retired)
    )
    await db.execute(
        update(Driver).where(Driver.id != d.id, Driver.id != driver2.id).values(status=DriverStatus.suspended)
    )
    await db.execute(
        delete(Trip).where(Trip.status == TripStatus.draft)
    )
    await db.commit()

    trip = Trip(
        vehicle_id=veh.id,
        driver_id=d.id,
        source="Gandhinagar Depot",
        destination="Ahmedabad Hub",
        planned_distance_km=Decimal("35.00"),
        cargo_weight_kg=Decimal("500.00"),
        status=TripStatus.draft
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)
    _created_ids["trips"].append(trip.id)

    await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": True},
        headers=headers
    )

    with patch("app.services.llm_service.call_llm") as mock_call:
        mock_response = {
            "action": "dispatch",
            "vehicle_id": str(vehicle2.id),
            "driver_id": str(driver2.id),
            "reason": "AI recommendation for Vehicle 2"
        }
        mock_call.return_value = json.dumps(mock_response)

        res = await client.get("/api/v1/trips/autopilot/feed", headers=headers)
        assert res.status_code == 200
        data = res.json()

        event = next((e for e in data["events"] if e.get("trip_id") == str(trip.id)), None)
        assert event is not None
        assert event["event_type"] == "auto_dispatched"
        assert event["status"] == "dispatched"
        assert event["vehicle_id"] == str(vehicle2.id)
        assert event["driver_id"] == str(driver2.id)

        await db.refresh(trip)
        assert trip.status == TripStatus.dispatched
        assert trip.vehicle_id == vehicle2.id
        assert trip.driver_id == driver2.id

    trip2 = Trip(
        vehicle_id=veh.id,
        driver_id=d.id,
        source="Gandhinagar Depot",
        destination="Ahmedabad Hub",
        planned_distance_km=Decimal("35.00"),
        cargo_weight_kg=Decimal("400.00"),
        status=TripStatus.draft
    )
    db.add(trip2)
    await db.commit()
    await db.refresh(trip2)
    _created_ids["trips"].append(trip2.id)

    vehicle2.status = VehicleStatus.available
    driver2.status = DriverStatus.available
    await db.commit()

    with patch("app.services.llm_service.call_llm") as mock_call:
        mock_response = {
            "action": "escalate",
            "vehicle_id": None,
            "driver_id": None,
            "reason": "Ambiguous choices, please review"
        }
        mock_call.return_value = json.dumps(mock_response)

        res = await client.get("/api/v1/trips/autopilot/feed", headers=headers)
        assert res.status_code == 200
        data = res.json()

        event2 = next((e for e in data["events"] if e.get("trip_id") == str(trip2.id)), None)
        assert event2 is not None
        assert event2["event_type"] == "escalated"
        assert event2["status"] == "pending"

        await db.refresh(trip2)
        assert trip2.status == TripStatus.draft

    await client.post(
        "/api/v1/trips/autopilot/toggle",
        json={"enabled": False},
        headers=headers
    )
