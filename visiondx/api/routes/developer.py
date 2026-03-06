"""
VisionDX — Developer API Routes
================================
POST /developer/signup          Register and get API key
POST /developer/login           Login and get account info
GET  /developer/me              Get account + key info
GET  /developer/keys            List all API keys
POST /developer/keys/new        Create new API key
DELETE /developer/keys/{id}     Revoke API key
GET  /developer/usage           Usage stats for today/month
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.database.api_key_models import (
    ApiDeveloper,
    ApiKey,
    PLAN_LIMITS,
    generate_api_key,
    hash_key,
    hash_password,
    verify_password,
)
from visiondx.database.connection import get_db

router = APIRouter(prefix="/developer", tags=["Developer API"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    full_name: str    = Field(..., min_length=2, max_length=100)
    email: str        = Field(..., description="Valid email address")
    password: str     = Field(..., min_length=8, max_length=100)
    org_name: str | None = Field(None, max_length=200)
    use_case: str | None = Field(None, max_length=500, description="Briefly describe your use case")

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupResponse(BaseModel):
    message: str
    developer_id: str
    email: str
    plan: str
    api_key: str          = Field(..., description="⚠️ Save this key — shown only once!")
    key_prefix: str
    daily_limit: int
    docs_url: str

class KeyInfo(BaseModel):
    id: str
    name: str
    prefix: str
    plan: str
    requests_today: int
    requests_total: int
    daily_limit: int
    is_active: bool
    created_at: str
    last_used_at: str | None

class DeveloperInfo(BaseModel):
    developer_id: str
    email: str
    full_name: str
    org_name: str | None
    plan: str
    created_at: str
    keys: list[KeyInfo]

class UsageResponse(BaseModel):
    plan: str
    daily_limit: int
    requests_today: int
    requests_total: int
    remaining_today: int

class NewKeyRequest(BaseModel):
    name: str = Field("Default Key", max_length=100)

class NewKeyResponse(BaseModel):
    message: str
    api_key: str = Field(..., description="⚠️ Save this key — shown only once!")
    key_prefix: str
    name: str


# ── Helper: get developer from Basic email:password header ────────────────────

async def _auth_developer(email: str, password: str, db: AsyncSession) -> ApiDeveloper:
    result = await db.execute(select(ApiDeveloper).where(ApiDeveloper.email == email))
    dev: ApiDeveloper | None = result.scalar_one_or_none()
    if not dev or not verify_password(password, dev.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not dev.is_active:
        raise HTTPException(status_code=403, detail="Account is suspended")
    return dev


async def _get_dev_by_token(
    x_developer_email: str = Header(..., alias="X-Developer-Email"),
    x_developer_password: str = Header(..., alias="X-Developer-Password"),
    db: AsyncSession = Depends(get_db),
) -> ApiDeveloper:
    return await _auth_developer(x_developer_email, x_developer_password, db)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new developer account and receive your first API key.
    **The API key is shown only once — save it immediately.**
    """
    # Check duplicate email
    existing = await db.execute(select(ApiDeveloper).where(ApiDeveloper.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create developer
    dev = ApiDeveloper(
        email=body.email,
        full_name=body.full_name,
        org_name=body.org_name,
        use_case=body.use_case,
        plan="free",
        hashed_password=hash_password(body.password),
    )
    db.add(dev)
    await db.flush()  # get dev.id

    # Create first API key
    raw_key, prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        developer_id=dev.id,
        prefix=prefix,
        key_hash=key_hash,
        name="Default Key",
        plan="free",
        requests_limit_daily=PLAN_LIMITS["free"],
    )
    db.add(api_key)
    await db.commit()

    return SignupResponse(
        message="Account created successfully! Save your API key — it won't be shown again.",
        developer_id=dev.id,
        email=dev.email,
        plan="free",
        api_key=raw_key,
        key_prefix=prefix,
        daily_limit=PLAN_LIMITS["free"],
        docs_url="/developer/docs",
    )


@router.get("/me", response_model=DeveloperInfo)
async def get_me(dev: ApiDeveloper = Depends(_get_dev_by_token), db: AsyncSession = Depends(get_db)):
    """Get your developer account details and all API keys."""
    keys_result = await db.execute(select(ApiKey).where(ApiKey.developer_id == dev.id))
    keys = keys_result.scalars().all()

    return DeveloperInfo(
        developer_id=dev.id,
        email=dev.email,
        full_name=dev.full_name,
        org_name=dev.org_name,
        plan=dev.plan,
        created_at=dev.created_at.isoformat(),
        keys=[
            KeyInfo(
                id=k.id, name=k.name, prefix=k.prefix,
                plan=k.plan, requests_today=k.requests_today,
                requests_total=k.requests_total, daily_limit=k.requests_limit_daily,
                is_active=k.is_active,
                created_at=k.created_at.isoformat(),
                last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            )
            for k in keys
        ],
    )


@router.post("/keys/new", response_model=NewKeyResponse, status_code=201)
async def create_key(
    body: NewKeyRequest,
    dev: ApiDeveloper = Depends(_get_dev_by_token),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for your account (max 5 keys per account)."""
    existing = await db.execute(select(ApiKey).where(ApiKey.developer_id == dev.id, ApiKey.is_active == True))
    count = len(existing.scalars().all())
    if count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 active keys per account")

    raw_key, prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        developer_id=dev.id,
        prefix=prefix,
        key_hash=key_hash,
        name=body.name,
        plan=dev.plan,
        requests_limit_daily=PLAN_LIMITS[dev.plan],
    )
    db.add(api_key)
    await db.commit()

    return NewKeyResponse(
        message="New API key created. Save it — shown only once.",
        api_key=raw_key,
        key_prefix=prefix,
        name=body.name,
    )


@router.delete("/keys/{key_id}", status_code=200)
async def revoke_key(
    key_id: str,
    dev: ApiDeveloper = Depends(_get_dev_by_token),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.developer_id == dev.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    await db.execute(update(ApiKey).where(ApiKey.id == key_id).values(is_active=False))
    await db.commit()
    return {"message": f"Key {key.prefix}… revoked successfully"}


@router.get("/usage", response_model=UsageResponse)
async def get_usage(dev: ApiDeveloper = Depends(_get_dev_by_token), db: AsyncSession = Depends(get_db)):
    """Get today's API usage statistics."""
    result = await db.execute(select(ApiKey).where(ApiKey.developer_id == dev.id, ApiKey.is_active == True))
    keys = result.scalars().all()
    today_total  = sum(k.requests_today for k in keys)
    total_all    = sum(k.requests_total for k in keys)
    daily_limit  = PLAN_LIMITS[dev.plan]
    return UsageResponse(
        plan=dev.plan,
        daily_limit=daily_limit,
        requests_today=today_total,
        requests_total=total_all,
        remaining_today=max(0, daily_limit - today_total),
    )
