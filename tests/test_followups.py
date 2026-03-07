import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
class TestFollowUpsAPI:
    """Tests for weekly and monthly follow-up tracking."""

    async def test_create_weekly_followup(self, auth_client):
        """Test submitting a weekly summary."""
        payload = {
            "week_start_date": datetime.now().isoformat(),
            "mood_score": 8,
            "weight_kg": 72.5,
            "mental_state": "calm, happy",
            "notes": "Feeling good this week."
        }
        response = await auth_client.post("/follow-ups/weekly", json=payload)
        assert response.status_code == 201
        assert response.json()["mood_score"] == 8

    async def test_get_weekly_history(self, auth_client):
        """Test retrieving weekly follow-up history."""
        response = await auth_client.get("/follow-ups/weekly")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_create_monthly_followup(self, auth_client):
        """Test submitting a monthly evaluation."""
        payload = {
            "month_start": datetime.now().isoformat(),
            "summary": "Stable health month.",
            "health_trends": "Improving sleep patterns.",
            "recommendations": "Keep exercising."
        }
        response = await auth_client.post("/follow-ups/monthly", json=payload)
        assert response.status_code == 201
        assert response.json()["summary"] == "Stable health month."

    async def test_get_monthly_history(self, auth_client):
        """Test retrieving monthly history."""
        response = await auth_client.get("/follow-ups/monthly")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
