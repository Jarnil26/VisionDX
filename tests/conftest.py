"""
VisionDX — Comprehensive Test Configuration & Fixtures
"""
import asyncio
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from passlib.context import CryptContext
from unittest.mock import MagicMock, patch

from visiondx.main import app
from visiondx.database.connection import Base, get_db
from visiondx.database.models import AppUser, User, Lab, LabBooking
from visiondx.api.routes.users import _create_access_token
from visiondx.database.schemas import ParsedReport, ParsedParameter

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Database Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def override_db(test_db):
    async def _get_db_override():
        yield test_db
    app.dependency_overrides[get_db] = _get_db_override
    yield test_db
    app.dependency_overrides.clear()

# ── Mocking Service Fixtures ───────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_report_service():
    with patch("visiondx.services.report_service.process_report") as mock:
        mock.return_value = MagicMock(
            report_id="test-report-id",
            status="processed",
            predictions=[]
        )
        yield mock

@pytest.fixture(autouse=True)
def mock_chat_service():
    with patch("visiondx.services.chat_service.process_chat_message") as mock:
        mock.return_value = (
            "AI Reply", "session-123", ["suggestion"], False, []
        )
        yield mock

# ── User & Auth Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
async def test_app_user(override_db):
    user = AppUser(
        id="test-app-user",
        email="patient@example.com",
        phone="+1234567890",
        hashed_password=_pwd_ctx.hash("password123"),
        full_name="Test Patient",
        is_active=True,
    )
    override_db.add(user)
    await override_db.flush()
    return user

@pytest.fixture
async def test_staff_user(override_db):
    user = User(
        email="staff@visiondx.ai",
        hashed_password=_pwd_ctx.hash("password123"),
        full_name="Staff Member",
        role="lab_staff",
    )
    override_db.add(user)
    await override_db.flush()
    return user

@pytest.fixture
def app_user_token(test_app_user):
    return _create_access_token(test_app_user.id)

@pytest.fixture
def staff_token(test_staff_user):
    from visiondx.api.routes.auth import create_access_token
    return create_access_token({"sub": test_staff_user.email, "role": test_staff_user.role})

# ── Clients ────────────────────────────────────────────────────────────────────

@pytest.fixture
async def client(override_db):
    async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
        yield ac

@pytest.fixture
async def auth_client(client, app_user_token):
    client.headers.update({"Authorization": f"Bearer {app_user_token}"})
    return client

@pytest.fixture
async def staff_client(client, staff_token):
    client.headers.update({"Authorization": f"Bearer {staff_token}"})
    return client

@pytest.fixture
async def lab_client(client):
    client.headers.update({"X-Lab-API-Key": "test-lab-key"})
    return client

@pytest.fixture
async def pub_client(client):
    client.headers.update({"X-API-Key": "test-public-key"})
    return client

# ── Data Factories ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_pdf_content():
    return b"%PDF-1.4 test content"

@pytest.fixture
def mock_parsed_report():
    return ParsedReport(
        patient_name="John Doe",
        age="45",
        gender="Male",
        report_id="REP123",
        date="2023-10-27",
        parameters=[
            ParsedParameter(name="Glucose", value=110.0, unit="mg/dL", status="HIGH")
        ]
    )
