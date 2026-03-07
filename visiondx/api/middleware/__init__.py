"""VisionDX API Middleware"""

from .authentication import (
    create_access_token,
    get_current_user,
    get_authenticated_user,
    get_doctor_user,
    get_admin_user,
    get_lab_user,
    verify_api_key,
    CurrentUser,
    TokenData,
)

from .error_handler import (
    VisionDXException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError_,
    DatabaseError,
    ExternalServiceError,
    register_error_handlers,
)

from .logging_config import setup_logging

__all__ = [
    # Authentication
    "create_access_token",
    "get_current_user",
    "get_authenticated_user",
    "get_doctor_user",
    "get_admin_user",
    "get_lab_user",
    "verify_api_key",
    "CurrentUser",
    "TokenData",
    # Error Handling
    "VisionDXException",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "ValidationError_",
    "DatabaseError",
    "ExternalServiceError",
    "register_error_handlers",
    # Logging
    "setup_logging",
]
