import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestAuthAPI:
    """Tests for staff/doctor authentication endpoints."""
    
    async def test_register_success(self, client):
        """Test successful registration."""
        payload = {
            "email": "new_staff@example.com",
            "password": "strongpassword123",
            "full_name": "New Staff",
            "role": "lab_staff"
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client, test_staff_user):
        """Test registration with existing email."""
        payload = {
            "email": test_staff_user.email,
            "password": "password123",
            "full_name": "Duplicate User",
            "role": "lab_staff"
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_login_success(self, client, test_staff_user):
        """Test successful login."""
        payload = {
            "email": test_staff_user.email,
            "password": "password123"
        }
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_login_invalid_credentials(self, client, test_staff_user):
        """Test login with wrong password."""
        payload = {
            "email": test_staff_user.email,
            "password": "wrongpassword"
        }
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    async def test_get_me_success(self, staff_client, test_staff_user):
        """Test /auth/me with valid token."""
        response = await staff_client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_staff_user.email
        assert data["full_name"] == test_staff_user.full_name

    async def test_get_me_unauthorized(self, client):
        """Test /auth/me without token."""
        response = await client.get("/auth/me")
        assert response.status_code == 401
