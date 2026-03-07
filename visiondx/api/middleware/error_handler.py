"""
VisionDX — Error Handling Middleware

Global exception handlers for API errors.
Returns consistent error response format.
"""
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from loguru import logger

import json


# ── Error Response Schema ──────────────────────────────────────────────────────

class ErrorResponse:
    """Standard error response format."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status": self.status_code,
                **({"details": self.details} if self.details else {}),
            }
        }


# ── Custom Exceptions ──────────────────────────────────────────────────────────

class VisionDXException(Exception):
    """Base exception for VisionDX."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class AuthenticationError(VisionDXException):
    """Authentication failed."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(VisionDXException):
    """User not authorized for resource."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHZ_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ResourceNotFoundError(VisionDXException):
    """Resource not found."""
    
    def __init__(self, resource: str):
        super().__init__(
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationError_(VisionDXException):
    """Invalid input data."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class DatabaseError(VisionDXException):
    """Database operation failed."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="DB_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ExternalServiceError(VisionDXException):
    """External service (API, ML, etc.) failed."""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            error_code="EXTERNAL_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


# ── Exception Handlers ─────────────────────────────────────────────────────────

async def visiondx_exception_handler(
    request: Request,
    exc: VisionDXException,
) -> JSONResponse:
    """Handle VisionDX custom exceptions."""
    logger.error(
        f"{exc.error_code}: {exc.message}",
        error_code=exc.error_code,
        path=request.url.path,
        details=exc.details,
    )
    
    error_response = ErrorResponse(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        "Validation error",
        path=request.url.path,
        errors=errors,
    )
    
    error_response = ErrorResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"validation_errors": errors},
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.to_dict(),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.exception(
        "Unhandled exception",
        path=request.url.path,
        exception=str(exc),
    )
    
    # Don't expose internal error details in production
    message = "Internal server error. Please try again later."
    if str(exc):
        message = str(exc)
    
    error_response = ErrorResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
        message=message,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict(),
    )


# ── Handler Registration ───────────────────────────────────────────────────────

def register_error_handlers(app: FastAPI):
    """Register all error handlers with the FastAPI app."""
    app.add_exception_handler(
        VisionDXException,
        visiondx_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        generic_exception_handler,
    )
