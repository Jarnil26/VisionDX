import pytest

@pytest.mark.asyncio
class TestSystemAPI:
    """Tests for system health and core utility endpoints."""

    async def test_server_health(self, client):
        """Test the main /health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "model_loaded" in data

    async def test_root_docs_availability(self, client):
        """Test that Swagger documentation is accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200

    async def test_openapi_json(self, client):
        """Test that OpenAPI schema is generated."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()
