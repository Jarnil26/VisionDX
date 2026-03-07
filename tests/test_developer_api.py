import pytest
from unittest.mock import MagicMock
from datetime import datetime

@pytest.mark.asyncio
class TestDeveloperAPI:
    """Tests for the Developer Portal API."""

    async def test_developer_signup(self, client):
        """Test registering as a new developer."""
        payload = {
            "full_name": "Dev User",
            "email": "dev@example.com",
            "password": "strongpassword123",
            "org_name": "DevCorp",
            "use_case": "Testing the API"
        }
        response = await client.post("/developer/signup", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "api_key" in data
        assert data["email"] == "dev@example.com"

    async def test_get_developer_info(self, client, override_db):
        """Test retrieving developer account info."""
        from visiondx.api.routes import developer
        
        mock_dev = MagicMock()
        mock_dev.id = "dev-123"
        mock_dev.email = "dev@example.com"
        mock_dev.full_name = "Dev User"
        mock_dev.org_name = "DevCorp"
        mock_dev.plan = "free"
        mock_dev.created_at = datetime.now()
        
        with pytest.MonkeyPatch.context() as mp:
            async def mock_auth(*args, **kwargs): return mock_dev
            mp.setattr(developer, "_get_dev_by_token", mock_auth)
            
            headers = {
                "X-Developer-Email": "dev@example.com",
                "X-Developer-Password": "password123"
            }
            response = await client.get("/developer/me", headers=headers)
            assert response.status_code == 200
            assert response.json()["email"] == "dev@example.com"

    async def test_create_new_api_key(self, client):
        """Test rotating or creating a new API key."""
        from visiondx.api.routes import developer
        mock_dev = MagicMock()
        mock_dev.id = "dev-123"
        mock_dev.plan = "free"

        with pytest.MonkeyPatch.context() as mp:
            async def mock_auth(*args, **kwargs): return mock_dev
            mp.setattr(developer, "_get_dev_by_token", mock_auth)

            payload = {"name": "Secondary Key"}
            response = await client.post("/developer/keys/new", json=payload)
            assert response.status_code == 201
            assert "api_key" in response.json()

    async def test_get_usage_stats(self, client):
        """Test retrieving API usage stats."""
        from visiondx.api.routes import developer
        mock_dev = MagicMock()
        mock_dev.id = "dev-123"
        mock_dev.plan = "free"

        with pytest.MonkeyPatch.context() as mp:
            async def mock_auth(*args, **kwargs): return mock_dev
            mp.setattr(developer, "_get_dev_by_token", mock_auth)

            response = await client.get("/developer/usage")
            assert response.status_code == 200
            data = response.json()
            assert "requests_today" in data
            assert "remaining_today" in data
