import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.anyio
async def test_admin_login(client: AsyncClient):
    # Test successful login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": settings.default_admin_email, "password": settings.default_admin_password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test login failure
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": settings.default_admin_email, "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}

@pytest.mark.anyio
async def test_get_me(client: AsyncClient):
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": settings.default_admin_email, "password": settings.default_admin_password}
    )
    token = login_response.json()["access_token"]

    # Call /me with valid token
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == settings.default_admin_email
    assert me_data["role"] == "fleet_manager"
    assert me_data["is_active"] is True

    # Call /me with invalid token
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert me_response.status_code == 401
    assert me_response.json() == {"detail": "Could not validate credentials"}

    # Call /me without token
    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 401

@pytest.mark.anyio
async def test_create_user_and_rbac(client: AsyncClient):
    # 1. Login as Admin (fleet_manager)
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": settings.default_admin_email, "password": settings.default_admin_password}
    )
    admin_token = admin_login.json()["access_token"]

    # 2. Admin creates a dispatcher user
    dispatcher_email = "test.dispatcher@transitops.com"
    dispatcher_password = "DispatcherPassword123!"
    create_response = await client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "Test Dispatcher User",
            "email": dispatcher_email,
            "password": dispatcher_password,
            "role": "dispatcher"
        }
    )
    assert create_response.status_code == 201
    dispatcher_data = create_response.json()
    assert dispatcher_data["email"] == dispatcher_email
    assert dispatcher_data["role"] == "dispatcher"

    # 3. Try creating user with same email (should fail with 409 Conflict)
    duplicate_response = await client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "Duplicate User",
            "email": dispatcher_email,
            "password": "somepassword",
            "role": "dispatcher"
        }
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {"detail": "A user with this email already exists"}

    # 4. Login as the newly created dispatcher
    disp_login = await client.post(
        "/api/v1/auth/login",
        json={"email": dispatcher_email, "password": dispatcher_password}
    )
    assert disp_login.status_code == 200
    dispatcher_token = disp_login.json()["access_token"]

    # 5. Dispatcher tries to create a new user (should fail with 403 Forbidden)
    create_by_disp_response = await client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {dispatcher_token}"},
        json={
            "full_name": "Unauthorized User",
            "email": "unauth@transitops.com",
            "password": "somepassword",
            "role": "dispatcher"
        }
    )
    assert create_by_disp_response.status_code == 403
    assert create_by_disp_response.json() == {"detail": "You do not have permission to perform this action"}
