"""
VisionDX — JWT Authentication Middleware

Validates JWT tokens in Authorization headers.
Supports Bearer token and X-API-Key patterns.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header
from pydantic import BaseModel

from visiondx.config import settings


# ── JWT Schemas ────────────────────────────────────────────────────────────────

class TokenData(BaseModel):
    """JWT token data structure."""
    user_id: str
    email: str
    role: str  # user, doctor, lab, admin
    exp: Optional[datetime] = None


class CurrentUser(BaseModel):
    """Current authenticated user context."""
    user_id: str
    email: str
    role: str
    is_authenticated: bool = True


# ── Token Generation ───────────────────────────────────────────────────────────

def create_access_token(
    user_id: str,
    email: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    
    return encoded_jwt


# ── Token Validation ───────────────────────────────────────────────────────────

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Extract and validate JWT token from Bearer token.
    Returns current user or raises 401.
    """
    token = auth.credentials
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role", "user")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return CurrentUser(
            user_id=user_id,
            email=email,
            role=role,
        )
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Role-Based Access Control (RBAC) ──────────────────────────────────────────

def get_admin_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Verify user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user


def get_doctor_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Verify user is a doctor."""
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor role required",
        )
    return current_user


def get_lab_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Verify user is a lab staff."""
    if current_user.role not in ("lab", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lab staff role required",
        )
    return current_user


def get_authenticated_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Verify user is authenticated (any role)."""
    return current_user


# ── API Key Validation ─────────────────────────────────────────────────────────

async def verify_api_key(x_api_key: str = None) -> str:
    """
    Validate X-API-Key header for external API access.
    In production, check this against database.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )
    
    # TODO: Verify against database
    # from visiondx.database.models import APIKey
    # key = await db.get(APIKey, x_api_key)
    # if not key or not key.is_active:
    #     raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return x_api_key
