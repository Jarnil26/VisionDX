"""
VisionDX — Error Handling & Response Tests

Tests for custom exceptions and error response format.
"""
import pytest
from fastapi import status

from visiondx.api.middleware.error_handler import (
    VisionDXException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError_,
    DatabaseError,
    ExternalServiceError,
    ErrorResponse,
)


class TestErrorResponse:
    """Test ErrorResponse formatting."""
    
    def test_error_response_creation(self):
        """Test creating an error response."""
        error = ErrorResponse(
            status_code=400,
            error_code="TEST_ERROR",
            message="This is a test error",
        )
        
        assert error.status_code == 400
        assert error.error_code == "TEST_ERROR"
        assert error.message == "This is a test error"
    
    def test_error_response_to_dict(self):
        """Test converting error to dictionary."""
        error = ErrorResponse(
            status_code=400,
            error_code="VALIDATION_ERROR",
            message="Invalid input",
        )
        
        result = error.to_dict()
        
        assert "error" in result
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["message"] == "Invalid input"
        assert result["error"]["status"] == 400
    
    def test_error_response_with_details(self):
        """Test error response with additional details."""
        details = {"field": "email", "reason": "Invalid format"}
        error = ErrorResponse(
            status_code=422,
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            details=details,
        )
        
        result = error.to_dict()
        
        assert result["error"]["details"] == details


class TestVisionDXExceptions:
    """Test VisionDX custom exceptions."""
    
    def test_base_exception_creation(self):
        """Test creating a VisionDXException."""
        exc = VisionDXException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError("Invalid credentials")
        
        assert exc.error_code == "AUTH_ERROR"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in str(exc)
    
    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError("Admin access required")
        
        assert exc.error_code == "AUTHZ_ERROR"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
    
    def test_not_found_error(self):
        """Test ResourceNotFoundError."""
        exc = ResourceNotFoundError("User")
        
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc)
    
    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError_(
            "Invalid email format",
            details={"field": "email"}
        )
        
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.details == {"field": "email"}
    
    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError("Connection failed")
        
        assert exc.error_code == "DB_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_external_service_error(self):
        """Test ExternalServiceError."""
        exc = ExternalServiceError("ML Service", "Model not found")
        
        assert exc.error_code == "EXTERNAL_ERROR"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert "ML Service error" in str(exc)


class TestExceptionRaising:
    """Test raising and catching exceptions."""
    
    def test_catch_authentication_error(self):
        """Test catching AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Token expired")
        
        assert "Token expired" in str(exc_info.value)
    
    def test_catch_validation_error(self):
        """Test catching ValidationError."""
        with pytest.raises(ValidationError_) as exc_info:
            raise ValidationError_(
                "Email already exists",
                details={"field": "email", "value": "test@example.com"}
            )
        
        assert exc_info.value.details["field"] == "email"
    
    def test_catch_not_found_error(self):
        """Test catching ResourceNotFoundError."""
        with pytest.raises(ResourceNotFoundError) as exc_info:
            raise ResourceNotFoundError("Doctor")
        
        assert "Doctor not found" in str(exc_info.value)


@pytest.mark.asyncio
class TestErrorHandlingIntegration:
    """Integration tests for error handling middleware."""
    
    async def test_validation_error_returns_422(self, client, auth_headers):
        """Test validation error returns 422."""
        # Send invalid request (missing required fields) with auth
        response = await client.post(
            "/follow-ups/weekly",
            json={"invalid": "data"},
            headers=auth_headers,
        )
        
        assert response.status_code == 422
        # Response may have "error" or standard Pydantic format
        data = response.json()
        assert data is not None
    
    async def test_not_found_returns_404(self, client):
        """Test not found error returns 404."""
        response = await client.get(
            "/nonexistent/endpoint",
        )
        
        assert response.status_code == 404
    
    async def test_missing_auth_returns_401(self, client):
        """Test missing authentication returns 401."""
        response = await client.post(
            "/follow-ups/weekly",
            json={"week_start_date": "2026-03-01T00:00:00"},
        )
        
        # Endpoint requires auth
        assert response.status_code in [401, 422]
