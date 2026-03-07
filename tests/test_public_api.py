import pytest
from unittest.mock import MagicMock
from visiondx.main import app

@pytest.mark.asyncio
class TestPublicAPI:
    """Tests for the v1 Public API (API Key protected)."""

    async def test_ping(self, client):
        """Test the public health check (no auth)."""
        response = await client.get("/api/v1/ping")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

    async def test_analyze_pdf_with_key(self, pub_client):
        """Test uploading report via public API with key."""
        from visiondx.api.middleware.api_auth import require_api_key
        
        # Mock API key validation dependency
        mock_dev = MagicMock()
        mock_dev.id = "dev-1"
        
        with pytest.MonkeyPatch.context() as mp:
            async def mock_require_key(*args, **kwargs): return mock_dev
            app.dependency_overrides[require_api_key] = mock_require_key
            
            files = {"file": ("outside_report.pdf", b"%PDF-1.4 content", "application/pdf")}
            response = await pub_client.post("/api/v1/analyze", files=files)
            
            assert response.status_code == 202
            assert "report_id" in response.json()
            
            app.dependency_overrides.clear()

    async def test_analyze_text_with_key(self, pub_client):
        """Test analyzing raw text via public API."""
        from visiondx.api.middleware.api_auth import require_api_key
        mock_dev = MagicMock()
        
        with pytest.MonkeyPatch.context() as mp:
            async def mock_require_key(*args, **kwargs): return mock_dev
            app.dependency_overrides[require_api_key] = mock_require_key

            payload = {
                "text": "Glucose: 150 mg/dL (70-100)",
                "patient_name": "External User"
            }
            response = await pub_client.post("/api/v1/analyze/text", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["patient_name"] == "External User"
            assert data["total_parameters"] > 0
            
            app.dependency_overrides.clear()

    async def test_unauthorized_public_access(self, client):
        """Test public API endpoint without X-API-Key."""
        response = await client.post("/api/v1/analyze")
        # Middleware should return 401/403
        assert response.status_code in [401, 403, 422] # 422 if header missing and not caught by custom logic
