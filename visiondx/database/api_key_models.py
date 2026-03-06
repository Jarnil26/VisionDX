"""
VisionDX — API Key System
=========================
Allows external developers to sign up, receive an API key,
and access the VisionDX AI analysis endpoints.

Tables added:
  - api_developers  (name, email, hashed_password, org, plan)
  - api_keys        (key_hash, prefix, developer_id, plan, usage stats)
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from visiondx.database.connection import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ApiDeveloper(Base):
    """External developer who signs up for API access."""
    __tablename__ = "api_developers"

    id: Mapped[str]          = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str]       = mapped_column(String(200), unique=True, nullable=False, index=True)
    full_name: Mapped[str]   = mapped_column(String(200), nullable=False)
    org_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    use_case: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[str]        = mapped_column(String(20), default="free")  # free | pro | enterprise
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool]  = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)  # auto-verify for now
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="developer", cascade="all, delete-orphan")


class ApiKey(Base):
    """API key issued to a developer."""
    __tablename__ = "api_keys"

    id: Mapped[str]           = mapped_column(String(36), primary_key=True, default=_uuid)
    developer_id: Mapped[str] = mapped_column(String(36), ForeignKey("api_developers.id"), nullable=False)
    # Show prefix to user for identification: "vdx_abc123..."
    prefix: Mapped[str]       = mapped_column(String(12), nullable=False)
    # Never store raw key — only sha256 hash
    key_hash: Mapped[str]     = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str]         = mapped_column(String(100), default="Default Key")
    plan: Mapped[str]         = mapped_column(String(20), default="free")
    # Rate limits
    requests_today: Mapped[int]  = mapped_column(Integer, default=0)
    requests_total: Mapped[int]  = mapped_column(Integer, default=0)
    requests_limit_daily: Mapped[int] = mapped_column(Integer, default=100)  # free: 100/day
    is_active: Mapped[bool]      = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    developer: Mapped["ApiDeveloper"] = relationship("ApiDeveloper", back_populates="keys")


# ── Helper utilities ──────────────────────────────────────────────────────────

PLAN_LIMITS = {
    "free":       100,
    "pro":        5_000,
    "enterprise": 100_000,
}


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    Returns (raw_key, prefix, key_hash).
    raw_key is shown to user ONCE — never stored.
    """
    raw = "vdx_" + secrets.token_urlsafe(32)
    prefix = raw[:12]
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefix, key_hash


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def hash_password(password: str) -> str:
    import hashlib, os
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False
