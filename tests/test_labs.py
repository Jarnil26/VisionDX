import pytest
from unittest.mock import MagicMock
from visiondx.main import app

@pytest.mark.asyncio
class TestLabsAPI:
    """Tests for lab collaboration and Lab API."""

    async def test_list_labs(self, client):
        """Test listing partner labs."""
        response = await client.get("/labs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_create_booking(self, auth_client, override_db):
        """Test creating a lab booking."""
        from visiondx.database.models import Lab
        lab = Lab(id="lab-1", name="Test Lab", slug="test-lab", is_active=True)
        override_db.add(lab)
        await override_db.flush()

        payload = {
            "lab_id": "lab-1",
            "collection_type": "home",
            "test_type": "Blood Test",
            "scheduled_at": "2023-12-01T10:00:00"
        }
        response = await auth_client.post("/labs/bookings", json=payload)
        assert response.status_code == 201
        assert response.json()["lab_id"] == "lab-1"

    async def test_lab_api_update_status(self, lab_client, override_db):
        """Test updating booking status via Lab API."""
        from visiondx.api.routes import labs
        
        mock_lab = MagicMock()
        mock_lab.id = "lab-1"
        
        async def mock_auth(*args, **kwargs): return mock_lab
        app.dependency_overrides[labs.get_lab_by_api_key] = mock_auth
        
        try:
            from visiondx.database.models import LabBooking
            booking = LabBooking(id="book-1", lab_id="lab-1", app_user_id="user-1", status="scheduled")
            override_db.add(booking)
            await override_db.flush()

            payload = {"status": "sample_collected"}
            response = await lab_client.put("/lab-api/bookings/book-1/status", json=payload)
            assert response.status_code == 200
            assert response.json()["status"] == "sample_collected"
        finally:
            app.dependency_overrides.clear()

    async def test_lab_api_submit_report(self, lab_client):
        """Test submitting report via Lab API."""
        from visiondx.api.routes import labs
        mock_lab = MagicMock()
        mock_lab.id = "lab-1"

        async def mock_auth(*args, **kwargs): return mock_lab
        app.dependency_overrides[labs.get_lab_by_api_key] = mock_auth

        try:
            files = {"file": ("lab_report.pdf", b"%PDF-1.4 content", "application/pdf")}
            data = {"booking_id": "book-1"}
            response = await lab_client.post("/lab-api/reports", files=files, data=data)
            assert response.status_code == 202
            assert "report_id" in response.json()
        finally:
            app.dependency_overrides.clear()
