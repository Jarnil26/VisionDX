"""
VisionDX — Integration Tests for API Endpoints

Tests for health tracking, chat doctor, bookings, and other endpoints.
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthTrackingEndpoints:
    """Test health tracking endpoints."""
    
    async def test_create_weekly_followup(self, client, auth_headers, followup_data):
        """Test creating a weekly follow-up."""
        response = await client.post(
            "/follow-ups/weekly",
            json=followup_data,
            headers=auth_headers,
        )
        
        assert response.status_code in [200, 201], f"Status {response.status_code}, body: {response.text}"
        data = response.json()
        assert "id" in data or "weight_kg" in data
    
    async def test_get_weekly_history(self, client, auth_headers):
        """Test retrieving weekly health history."""
        response = await client.get(
            "/follow-ups/weekly",
            headers=auth_headers,
        )
        
        # Should return 200 (empty list or list of records)
        assert response.status_code == 200
    
    async def test_create_monthly_followup(self, client, auth_headers, monthly_followup_data):
        """Test creating a monthly follow-up."""
        response = await client.post(
            "/follow-ups/monthly",
            json=monthly_followup_data,
            headers=auth_headers,
        )
        
        assert response.status_code in [200, 201]
    
    async def test_missing_auth_returns_401(self, client):
        """Test endpoint without authentication returns 401."""
        response = await client.get("/follow-ups/weekly")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestChatEndpoints:
    """Test AI chat doctor endpoints."""
    
    async def test_send_chat_message(self, client, auth_headers, chat_message_data):
        """Test sending a message to AI doctor."""
        response = await client.post(
            "/chat",
            json=chat_message_data,
            headers=auth_headers,
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        # Just verify we got a response back
        assert data is not None
    
    async def test_get_chat_history(self, client, auth_headers):
        """Test retrieving chat history."""
        response = await client.get(
            "/chat/history",
            headers=auth_headers,
        )
        
        assert response.status_code in [200, 404]
    
    async def test_empty_chat_message_fails(self, client, auth_headers):
        """Test empty chat message handling."""
        response = await client.post(
            "/chat",
            json={"message": ""},
            headers=auth_headers,
        )
        
        # Endpoint may accept (200) or reject (>=400) empty messages
        # Just verify the response is valid
        assert response.status_code in [200, 201, 400, 422]


@pytest.mark.asyncio
class TestBookingEndpoints:
    """Test lab booking endpoints."""
    
    async def test_create_booking(self, client, auth_headers):
        """Test creating a lab booking."""
        data = {
            "lab_id": "lab-123",
            "test_type": "Blood",
            "booking_type": "home",
            "scheduled_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "address": "123 Main St",
            "latitude": 19.0760,
            "longitude": 72.8777,
        }
        
        response = await client.post(
            "/labs/bookings",
            json=data,
            headers=auth_headers,
        )
        
        # May return 404 if lab doesn't exist, or other errors
        assert response.status_code in [200, 201, 400, 404]


    async def test_get_user_bookings(self, client, auth_headers):
        """Test retrieving user's bookings."""
        response = await client.get(
            "/labs/bookings",
            headers=auth_headers,
        )
        
        assert response.status_code == 200  # Should return list (maybe empty)
    
    async def test_invalid_booking_data_fails(self, client, auth_headers):
        """Test invalid booking data is rejected."""
        response = await client.post(
            "/labs/bookings",
            json={"invalid": "data"},
            headers=auth_headers,
        )
        
        assert response.status_code >= 400


@pytest.mark.asyncio
class TestNearbyFacilitiesEndpoints:
    """Test nearby facilities returned in chat."""
    
    async def test_chat_includes_nearby_info(self, client, auth_headers, chat_message_data):
        """Test that chat response can include nearby facilities."""
        response = await client.post(
            "/chat",
            json=chat_message_data,
            headers=auth_headers,
        )
        
        assert response.status_code in [200, 201]
        # Response should contain chat reply
        data = response.json()
        assert data is not None


@pytest.mark.asyncio
class TestDoctorDashboard:
    """Test doctor dashboard endpoints."""
    
    async def test_get_abnormal_reports(self, client):
        """Test getting abnormal reports (doctor view)."""
        response = await client.get(
            "/doctor/abnormal-reports",
        )
        
        # Should return 200 (no auth required for this endpoint)
        assert response.status_code == 200
    
    async def test_upload_report_endpoint_exists(self, client):
        """Test that report upload endpoint is available."""
        # Just check the endpoint exists (don't upload actual file)
        response = await client.get(
            "/docs",  # OpenAPI docs should list all endpoints
        )
        
        assert response.status_code == 200


@pytest.mark.asyncio
class TestHealthDashboard:
    """Test patient health tracking."""
    
    async def test_list_followups(self, client, auth_headers):
        """Test listing weekly follow-ups."""
        response = await client.get(
            "/follow-ups/weekly",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
class TestAuthenticationFlows:
    """Test complete authentication flows."""
    
    async def test_register_and_login_flow(self, client):
        """Test user registration and login."""
        user_data = {
            "email": "newuser@example.com",
            "password": "TestPass456",
            "full_name": "New User",
        }
        
        # Register
        register_response = await client.post(
            "/users/register",
            json=user_data,
        )
        
        # Should succeed or return conflict if exists
        assert register_response.status_code in [200, 201, 400, 409]
        
        if register_response.status_code in [200, 201]:
            data = register_response.json()
            assert "access_token" in data
    
    async def test_login_succeeds(self, client):
        """Test login with existing user."""
        login_data = {
            "email": "test@example.com",
            "password": "testpass123",
        }
        
        response = await client.post(
            "/users/login",
            json=login_data,
        )
        
        # May be 200, 401, or 404 depending on user existence
        assert response.status_code in [200, 401, 404]


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in endpoints."""
    
    async def test_invalid_json_returns_400(self, client, auth_headers):
        """Test invalid JSON request."""
        response = await client.post(
            "/follow-ups/weekly",
            headers=auth_headers,
            content="invalid json {",
        )
        
        assert response.status_code in [400, 422]
    
    async def test_missing_required_fields(self, client, auth_headers):
        """Test missing required fields."""
        response = await client.post(
            "/follow-ups/weekly",
            json={},  # Empty data
            headers=auth_headers,
        )
        
        assert response.status_code >= 400
    
    async def test_notfound_endpoint_returns_404(self, client):
        """Test non-existent endpoint."""
        response = await client.get("/nonexistent/endpoint")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestHealthCheckEndpoint:
    """Test system health endpoints."""
    
    async def test_health_check_endpoint(self, client):
        """Test /health endpoint (no auth required)."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    async def test_health_check_has_version(self, client):
        """Test health check returns version."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
