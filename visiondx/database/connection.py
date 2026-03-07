"""
VisionDX — Async SQLAlchemy Database Connection
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from visiondx.config import settings

# SQLite doesn't support pool_size / max_overflow
_is_sqlite = settings.database_url.startswith("sqlite")
_engine_kwargs = {} if _is_sqlite else {"pool_size": 10, "max_overflow": 20}

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    **_engine_kwargs,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables on startup (dev mode). Use Alembic for production."""
    async with engine.begin() as conn:
        from visiondx.database import models  # noqa: F401
        from visiondx.database import api_key_models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
