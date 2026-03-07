"""
VisionDX — App User (Patient) Routes

POST /users/register        — Register with email or mobile + profile
POST /users/login           — Login with email or phone, get JWT
GET  /users/me              — Current app user profile
PATCH /users/me             — Update profile (age, gender, medical history)
GET  /users/me/reports      — List my reports
POST /users/me/reports/upload — Upload report PDF (linked to user)
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from loguru import logger
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.config import settings
from visiondx.database.connection import get_db
from visiondx.database.models import AppUser, Report
from visiondx.database.schemas import (
    AppUserLoginRequest,
    AppUserOut,
    AppUserProfileUpdate,
    AppUserRegisterRequest,
    ReportOut,
    TokenResponse,
    UploadResponse,
)
from visiondx.services import report_service

router = APIRouter(prefix="/users", tags=["App Users (Patients)"])
_http_bearer = HTTPBearer(auto_error=False)
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def _create_access_token(app_user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": app_user_id, "type": "app_user", "role": "user", "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def get_current_app_user(
    credentials: HTTPAuthorizationCredentials = Depends(_http_bearer),
    db: AsyncSession = Depends(get_db),
) -> AppUser:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        # Fallback to 'sub' as primary ID
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Try lookup by UUID first (tokens from /users/login)
    result = await db.execute(select(AppUser).where(AppUser.id == user_id))
    user = result.scalar_one_or_none()
    
    # If not found, try lookup by email (tokens from /auth/login store email in sub)
    if user is None and "@" in user_id:
        result = await db.execute(select(AppUser).where(AppUser.email == user_id))
        user = result.scalar_one_or_none()
        
        # If still no AppUser but the email exists as a User (doctor/lab), auto-create an AppUser
        if user is None:
            from visiondx.database.models import User as StaffUser
            staff_result = await db.execute(select(StaffUser).where(StaffUser.email == user_id))
            staff_user = staff_result.scalar_one_or_none()
            if staff_user:
                user = AppUser(
                    email=staff_user.email,
                    hashed_password=staff_user.hashed_password,
                    full_name=staff_user.full_name,
                    is_active=staff_user.is_active,
                )
                db.add(user)
                await db.flush()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: AppUserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new app user (patient) with email or mobile and profile."""
    if body.email:
        r = await db.execute(select(AppUser).where(AppUser.email == body.email))
        if r.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )
    if body.phone:
        r = await db.execute(select(AppUser).where(AppUser.phone == body.phone))
        if r.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Phone number already registered",
            )
    user = AppUser(
        email=body.email,
        phone=body.phone,
        hashed_password=_hash_password(body.password),
        full_name=body.full_name,
        age=body.age,
        gender=body.gender,
        medical_history=body.medical_history,
    )
    db.add(user)
    await db.flush()
    token = _create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: AppUserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email or phone and password."""
    if body.email:
        result = await db.execute(select(AppUser).where(AppUser.email == body.email))
    else:
        result = await db.execute(select(AppUser).where(AppUser.phone == body.phone))
    user = result.scalar_one_or_none()
    if not user or not _verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    token = _create_access_token(user.id)
    return TokenResponse(access_token=token)


from visiondx.database.schemas import RefreshTokenRequest

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh an expired AppUser token without requiring a new login."""
    try:
        payload = jwt.decode(
            body.token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False}
        )
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Try by ID first, then by email
        result = await db.execute(select(AppUser).where(AppUser.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None and "@" in user_id:
            result = await db.execute(select(AppUser).where(AppUser.email == user_id))
            user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
            
        token = _create_access_token(user.id)
        return TokenResponse(access_token=token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/me", response_model=AppUserOut)
async def get_me(current_user: AppUser = Depends(get_current_app_user)):
    """Return current app user profile."""
    return AppUserOut.model_validate(current_user)


@router.patch("/me", response_model=AppUserOut)
async def update_me(
    body: AppUserProfileUpdate,
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile (full_name, age, gender, medical_history)."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.age is not None:
        current_user.age = body.age
    if body.gender is not None:
        current_user.gender = body.gender
    if body.medical_history is not None:
        current_user.medical_history = body.medical_history
    await db.flush()
    return AppUserOut.model_validate(current_user)


@router.get("/me/reports", response_model=list[ReportOut])
async def list_my_reports(
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
):
    """List all reports uploaded by the current user."""
    reports = await report_service.list_reports_by_app_user(current_user.id, db)
    return [ReportOut.model_validate(r) for r in reports]


@router.post("/me/reports/upload", response_model=UploadResponse, status_code=202)
async def upload_my_report(
    file: UploadFile = File(..., description="Blood test report PDF"),
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a report PDF; it will be linked to the current user and processed."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )
    pdf_path = await report_service.save_upload(content, file.filename or "report.pdf")
    try:
        report = await report_service.process_report(
            pdf_path, db, app_user_id=current_user.id
        )
    except Exception as e:
        logger.error(f"Report processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report processing failed: {str(e)}",
        )
    return UploadResponse(
        report_id=report.report_id,
        message="Report processed successfully",
        status=report.status,
    )
