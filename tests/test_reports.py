import pytest
from io import BytesIO
from unittest.mock import MagicMock

@pytest.mark.asyncio
class TestReportsAPI:
    """Tests for report management and analysis endpoints."""

    async def test_upload_valid_pdf(self, client):
        """Test uploading a valid PDF report."""
        files = {"file": ("report.pdf", b"%PDF-1.4 test content", "application/pdf")}
        response = await client.post("/upload-report", files=files)
        assert response.status_code == 202
        data = response.json()
        assert "report_id" in data
        assert data["message"] == "Report processed successfully"

    async def test_upload_invalid_file_type(self, client):
        """Test uploading a non-PDF file."""
        files = {"file": ("report.txt", b"not a pdf", "text/plain")}
        response = await client.post("/upload-report", files=files)
        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]

    async def test_get_report_not_found(self, client):
        """Test retrieving a non-existent report."""
        response = await client.get("/report/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    async def test_report_analysis_endpoint(self, client, mock_report_service):
        """Test the analysis summary endpoint."""
        # Mock what build_report_analysis would return
        with pytest.MonkeyPatch.context() as mp:
            from visiondx.services import report_service
            async def mock_build(*args, **kwargs):
                return {
                    "report_id": "REP123",
                    "total_parameters": 10,
                    "abnormal_count": 2,
                    "normal_count": 8,
                    "parameters": [],
                    "summary": "Everything looks okay mostly."
                }
            mp.setattr(report_service, "build_report_analysis", mock_build)
            mp.setattr(report_service, "get_report_by_id", lambda *a: MagicMock())

            response = await client.get("/report/REP123/analysis")
            assert response.status_code == 200
            data = response.json()
            assert data["report_id"] == "REP123"
            assert "summary" in data

    async def test_disease_prediction_format(self, client):
        """Test disease prediction response structure."""
        from unittest.mock import MagicMock
        from visiondx.services import report_service
        
        with pytest.MonkeyPatch.context() as mp:
            mock_report = MagicMock()
            mock_report.report_id = "REP123"
            mock_report.predictions = [MagicMock(disease="Anemia", confidence=0.85)]
            
            async def mock_get(*args, **kwargs): return mock_report
            mp.setattr(report_service, "get_report_by_id", mock_get)

            response = await client.get("/report/REP123/prediction")
            assert response.status_code == 200
            data = response.json()
            assert data["report_id"] == "REP123"
            assert len(data["possible_conditions"]) > 0
            assert data["possible_conditions"][0]["disease"] == "Anemia"
