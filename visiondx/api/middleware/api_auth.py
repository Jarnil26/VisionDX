"""
VisionDX — API Key Middleware
==============================
FastAPI dependency that validates `X-API-Key` header,
looks up the developer, checks daily rate limit,
and increments usage counter.

Usage in routes:
    from visiondx.api.middleware.api_auth import require_api_key

    @router.get("/analyze")
    async def analyze(dev: ApiDeveloper = Depends(require_api_key)):
        ...
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.database.api_key_models import ApiDeveloper, ApiKey, hash_key
from visiondx.database.connection import get_db


async def require_api_key(
    x_api_key: str = Header(..., alias="X-API-Key", description="Your VisionDX API key"),
    db: AsyncSession = Depends(get_db),
) -> ApiDeveloper:
    """
    FastAPI dependency — validates API key and returns the developer.
    Raises 401 if missing/invalid, 429 if rate limit exceeded.
    """
    if not x_api_key or not x_api_key.startswith("vdx_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. Keys must start with 'vdx_'.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_hash = hash_key(x_api_key)

    # Look up key
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )
    api_key: ApiKey | None = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key not found or revoked.",
        )

    # Check developer
    dev_result = await db.execute(
        select(ApiDeveloper).where(ApiDeveloper.id == api_key.developer_id, ApiDeveloper.is_active == True)
    )
    developer: ApiDeveloper | None = dev_result.scalar_one_or_none()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Developer account is inactive.",
        )

    # Rate limit check
    if api_key.requests_today >= api_key.requests_limit_daily:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily rate limit of {api_key.requests_limit_daily} requests reached. "
                   f"Upgrade your plan at https://visiondx.app/developer",
            headers={"Retry-After": "86400"},
        )

    # Increment usage
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key.id)
        .values(
            requests_today=ApiKey.requests_today + 1,
            requests_total=ApiKey.requests_total + 1,
            last_used_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()

    return developer


async def optional_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> ApiDeveloper | None:
    """Optional API key — for endpoints accessible both with and without key."""
    if not x_api_key:
        return None
    try:
        return await require_api_key(x_api_key, db)
    except HTTPException:
        return None
