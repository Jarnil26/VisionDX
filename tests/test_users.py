import pytest

@pytest.mark.asyncio
class TestUsersAPI:
    """Tests for patient user endpoints."""

    async def test_user_registration(self, client):
        """Test successful patient registration."""
        payload = {
            "email": "patient_new@example.com",
            "password": "password123",
            "full_name": "John Patient",
            "age": 25,
            "gender": "M"
        }
        response = await client.post("/users/register", json=payload)
        assert response.status_code == 201
        assert "access_token" in response.json()

    async def test_user_profile_update(self, auth_client, test_app_user):
        """Test updating patient profile."""
        payload = {
            "full_name": "Updated Name",
            "age": 35,
            "medical_history": "Previous allergies to penicillin"
        }
        response = await auth_client.patch("/users/me", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["age"] == 35
        assert data["medical_history"] == payload["medical_history"]

    async def test_user_reports_listing(self, auth_client):
        """Test listing reports for the authenticated user."""
        response = await auth_client.get("/users/me/reports")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_user_report_upload(self, auth_client):
        """Test uploading a report linked to the user."""
        files = {"file": ("my_report.pdf", b"%PDF-1.4 content", "application/pdf")}
        response = await auth_client.post("/users/me/reports/upload", files=files)
        assert response.status_code == 202
        assert "report_id" in response.json()

    async def test_user_unauthorized_access(self, client):
        """Test protected user endpoint without token."""
        response = await client.get("/users/me")
        assert response.status_code == 401
