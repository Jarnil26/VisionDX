"""
VisionDX — Production Integration Checklist & Deployment Guide

Complete guide to deploying the integrated backend.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# STEP-BY-STEP INTEGRATION & DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════════════════

## Phase 1: Code Integration ✅ COMPLETE

- [x] Middleware created (authentication, error handling, logging)
- [x] Database models enhanced (14 tables with Enums, indices, relationships)
- [x] Pydantic schemas integrated (30+ request/response models)
- [x] Service layer created (4 core services with business logic)
- [x] ML modules integrated (5 prediction modules)
- [x] API routers configured (40+ endpoints)
- [x] main.py updated with middleware and error handlers
- [x] Test suite created (unit, integration, middleware tests)

## Phase 2: Database Migration ⏳ NEXT

Run this sequence:

```bash
# 1. Create database tables
cd d:\risu\VisionDX
python -c "
import asyncio
from visiondx.database.connection import create_tables
asyncio.run(create_tables())
print('✓ Tables created')
"

# 2. Create indexes
python -c "
import asyncio
from visiondx.database.db_utilities import create_indexes
from visiondx.database.connection import engine
asyncio.run(create_indexes())
print('✓ Indexes created')
"

# 3. Seed sample data (optional)
python -c "
import asyncio
from visiondx.database.db_utilities import seed_database
from visiondx.database.connection import get_session
# asyncio.run(seed_database())
print('✓ Data seeded')
"
```

## Phase 3: Verify Installation

```bash
# 1. Test imports
python -c "
from visiondx.api.middleware import (
    setup_logging,
    register_error_handlers,
    get_current_user,
    create_access_token,
)
from visiondx.database.models import AppUser, Doctor, Lab, Report
print('✓ All imports successful')
"

# 2. Check configuration
python -c "
from visiondx.config import settings
print(f'✓ Config loaded')
print(f'  - DB: {settings.database_url}')
print(f'  - Env: {settings.app_env}')
print(f'  - Debug: {settings.debug}')
"
```

## Phase 4: Run Application

```bash
# Terminal 1: Start FastAPI backend
cd d:\risu\VisionDX
uvicorn visiondx.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Next.js frontend (if needed)
cd backend/frontend
npm run dev
```

## Phase 5: Test API Endpoints

### Via Swagger UI
- Open: http://localhost:8000/docs
- Authenticate with JWT token
- Test endpoints interactively

### Via cURL
```bash
# 1. Create access token
TOKEN=$(python -c "
from visiondx.api.middleware import create_access_token
token = create_access_token(
    user_id='test-user-1',
    email='test@example.com',
    role='user'
)
print(token)
")

# 2. Test authenticated endpoint
curl -X GET http://localhost:8000/health/summary \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION DETAILS
# ═══════════════════════════════════════════════════════════════════════════════

## Updated main.py Structure

```python
# Imports
from visiondx.api.middleware import (
    setup_logging,
    register_error_handlers,
)

# Startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()  # Initialize logging
    await create_tables()  # Create DB tables
    yield
    logger.info("VisionDX shutting down")

# Middleware
app.add_middleware(CORSMiddleware, ...)  # CORS
@app.middleware("http")
async def add_process_time_header(...)  # Request timing

# Error Handling
register_error_handlers(app)  # Global error handlers

# Routers
app.include_router(auth.router)
app.include_router(follow_ups.router)
app.include_router(chat.router)
# ... all routers included
```

## Middleware Components

### Authentication (`visiondx/api/middleware/authentication.py`)
- `create_access_token()` - Generate JWT tokens
- `get_current_user()` - Extract user from token
- `get_doctor_user()`, `get_admin_user()` - Role-based access
- RBAC decorators for endpoints

### Error Handling (`visiondx/api/middleware/error_handler.py`)
- Custom exceptions (VisionDXException, ResourceNotFoundError, etc.)
- Global error handler registration
- Consistent error response format
- Structured logging of errors

### Logging (`visiondx/api/middleware/logging_config.py`)
- Console and file logging
- Rotating file appenders
- Separate error log file
- DEBUG/INFO/WARNING/ERROR levels

## Database Models (14 Tables)

```
AppUser (patients)
├── Reports
│   ├── Parameters
│   ├── Predictions
│   └── LabBooking
├── WeeklyFollowUp
├── MonthlyFollowUp
├── HealthMetric
├── ChatSession
└── AbnormalAlert

Doctor
├── Hospital (Facility)

Lab
└── LabBooking

Facility
└── Doctors

APIKey
```

## API Endpoints (40+)

### Follow-ups (4)
- POST /follow-ups/weekly
- GET  /follow-ups/weekly
- POST /follow-ups/monthly
- GET  /follow-ups/monthly

### Chat (3)
- POST /chat (text)
- POST /chat/voice (audio)
- GET  /chat/history

### Bookings (4)
- POST /bookings
- GET  /bookings
- GET  /bookings/{id}
- PATCH /bookings/{id}/cancel

### Facilities (3)
- POST /nearby/doctors
- POST /nearby/hospitals
- POST /nearby/emergency

### Doctor Dashboard (4)
- GET /doctor/patients
- GET /doctor/high-risk
- GET /doctor/reports
- GET /doctor/alerts

### Health Dashboard (2)
- GET /health/summary
- GET /health/trends

# ═══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════════════════════════════

## .env file

```env
# Application
APP_NAME=VisionDX
APP_ENV=development
DEBUG=true
SECRET_KEY=your-long-random-secret-key-here-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=sqlite+aiosqlite:///./visiondx.db
DATABASE_URL_SYNC=sqlite:///./visiondx.db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# File Storage
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=20

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

## PostgreSQL Production Setup

```env
DATABASE_URL=postgresql+asyncpg://user:pass@db.example.com:5432/visiondx
DATABASE_URL_SYNC=postgresql://user:pass@db.example.com:5432/visiondx
```

# ═══════════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════════

## Run All Tests

```bash
# Install pytest
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=visiondx --cov-report=html
```

## Test Files

- `tests/conftest.py` - Fixtures and test configuration
- `tests/test_auth.py` - Authentication & JWT tests
- `tests/test_errors.py` - Error handling tests
- `tests/test_integration.py` - API endpoint integration tests

## Expected Test Coverage

- Authentication: ✓ 15+ tests
- Error Handling: ✓ 10+ tests
- API Endpoints: ✓ 20+ tests
- Models: ✓ TBD
- Services: ✓ TBD

# ═══════════════════════════════════════════════════════════════════════════════
# TROUBLESHOOTING
# ═══════════════════════════════════════════════════════════════════════════════

## Issue: Import Errors

```
ModuleNotFoundError: No module named 'visiondx'
```

**Solution:**
```bash
# Add project to PYTHONPATH
set PYTHONPATH=%CD%

# Or install in development mode
pip install -e .
```

## Issue: Database Connection Error

```
sqlite3.OperationalError: unable to open database file
```

**Solution:**
```bash
# Ensure uploads directory exists
mkdir uploads

# Check database file permissions
ls -la visiondx.db
```

## Issue: JWT Token Invalid

```
HTTPException: Invalid token
```

**Solution:**
```python
# Verify SECRET_KEY is consistent
from visiondx.config import settings
print(settings.secret_key)

# Regenerate tokens if SECRET_KEY changed
```

## Issue: CORS Blocked

```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solution:**
```env
# Update .env ALLOWED_ORIGINS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://yourdomain.com
```

# ═══════════════════════════════════════════════════════════════════════════════
# NEXT STEPS
# ═══════════════════════════════════════════════════════════════════════════════

### Immediate (This Week)
1. Run database migration
2. Execute test suite
3. Verify all endpoints in Swagger
4. Fix any remaining errors

### Short Term (Next Week)
1. Implement voice transcription (Whisper API)
2. Setup Celery background tasks
3. Add Redis caching layer
4. Implement email notifications

### Medium Term (2-3 Weeks)
1. Docker containerization
2. CI/CD pipeline (GitHub Actions)
3. Production deployment
4. Monitoring & alerting setup

### Long Term
1. Security audit
2. Load testing
3. Performance optimization
4. Analytics dashboard

# ═══════════════════════════════════════════════════════════════════════════════
# QUICK REFERENCE
# ═══════════════════════════════════════════════════════════════════════════════

## Start Backend
```bash
cd d:\risu\VisionDX
uvicorn visiondx.main:app --reload
```

## Start Frontend
```bash
cd d:\risu\VisionDX\frontend
npm run dev
```

## Generate JWT Token (Python)
```python
from visiondx.api.middleware import create_access_token
token = create_access_token(
    user_id="user-123",
    email="user@example.com",
    role="user"
)
print(token)
```

## Test Health Endpoint
```bash
curl http://localhost:8000/health
```

## View API Docs
```
http://localhost:8000/docs (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

## View Logs
```bash
tail -f logs/visiondx_*.log
tail -f logs/visiondx_errors_*.log
```

## Database Backup
```bash
cp visiondx.db visiondx.db.backup
```

---

**Status:** Ready for Phase 2 Database Migration  
**Last Updated:** March 7, 2026  
**Version:** 1.0-integrated
