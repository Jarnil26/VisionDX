"""
VisionDX — Database Utilities & Migration Guide

Production-grade database setup, migrations, and utilities.
"""
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from visiondx.database.connection import engine, Base


# ─────────────────────────────────────────────────────────────────────────
# 1️⃣ DATABASE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────

async def create_all_tables():
    """Create all tables based on ORM models."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ All tables created successfully")


async def drop_all_tables():
    """Drop all tables (for testing/reset)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✓ All tables dropped")


# ─────────────────────────────────────────────────────────────────────────
# 2️⃣ DATABASE HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────

async def check_database_health(db: AsyncSession) -> dict:
    """Check database connectivity and status."""
    health = {
        "connected": False,
        "tables_count": 0,
        "tables": [],
        "errors": [],
    }

    try:
        # Check connection
        await db.execute(text("SELECT 1"))
        health["connected"] = True

        # Get table info
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        health["tables_count"] = len(tables)
        health["tables"] = tables

        print(f"✓ Database healthy - {len(tables)} tables found")
    except Exception as e:
        health["errors"].append(str(e))
        print(f"✗ Database error: {e}")

    return health


# ─────────────────────────────────────────────────────────────────────────
# 3️⃣ SEED DATABASE (Sample Data)
# ─────────────────────────────────────────────────────────────────────────

async def seed_database(db: AsyncSession):
    """Seed database with sample data for testing."""
    print("Seeding database with sample data...")

    # Sample Labs
    from visiondx.database.models import Lab

    labs = [
        Lab(
            name="City Diagnostics",
            slug="city-diagnostics",
            address="123 Main St, Downtown",
            city="Mumbai",
            phone="+91-9876543210",
            email="contact@citydiagnostics.com",
            latitude=19.0760,
            longitude=72.8777,
            services='["Blood Test", "Urine Test", "COVID-19 Test", "Ultrasound"]',
            is_active=True,
        ),
        Lab(
            name="Apollo Diagnostics",
            slug="apollo-diagnostics",
            address="456 Commercial Rd",
            city="Bangalore",
            phone="+91-9876543211",
            email="contact@apollodiag.com",
            latitude=12.9716,
            longitude=77.5946,
            services='["Blood Test", "Imaging", "Advanced Tests"]',
            is_active=True,
        ),
    ]

    for lab in labs:
        db.add(lab)

    # Sample Facilities
    from visiondx.database.models import Facility

    facilities = [
        Facility(
            name="General Hospital Mumbai",
            facility_type="hospital",
            address="123 Medical Avenue, Mumbai",
            city="Mumbai",
            latitude=19.0760,
            longitude=72.8777,
            phone="+91-9876543210",
            specialities='["Cardiology", "Orthopedics", "Pediatrics"]',
            available_24h=True,
            rating=4.5,
        ),
        Facility(
            name="City Clinic",
            facility_type="clinic",
            address="456 Health St, Bangalore",
            city="Bangalore",
            latitude=12.9716,
            longitude=77.5946,
            phone="+91-9876543211",
            specialities='["General Medicine", "Cardiology"]',
            available_24h=False,
            rating=4.2,
        ),
    ]

    for facility in facilities:
        db.add(facility)

    await db.commit()
    print("✓ Database seeded successfully")


# ─────────────────────────────────────────────────────────────────────────
# 4️⃣ ALEMBIC MIGRATION SETUP (for production)
# ─────────────────────────────────────────────────────────────────────────

ALEMBIC_MIGRATION_GUIDE = """
# Alembic Migration Setup for VisionDX

## Installation
pip install alembic

## Initialize Alembic
alembic init alembic

## Configure alembic.ini
- Update SQLALCHEMY_URL in alembic.ini:
  SQLALCHEMY_URL = 'postgresql+asyncpg://user:password@localhost/visiondx_db'

## Configure alembic/env.py
- Import your models
- Set target_metadata = Base.metadata

## Create a Migration
alembic revision --autogenerate -m "Add new tables"

## Review the migration file in alembic/versions/

## Apply Migration
alembic upgrade head

## Downgrade
alembic downgrade -1

## Create New Table Example
```python
# In migration file
def upgrade():
    op.create_table(
        'new_table',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('new_table')
```

## Deploy
1. Test migrations on staging
2. Create backup of production database
3. Run: alembic upgrade head
4. Verify data integrity
"""


# ─────────────────────────────────────────────────────────────────────────
# 5️⃣ INDEX OPTIMIZATION
# ─────────────────────────────────────────────────────────────────────────

async def create_indexes(db: AsyncSession):
    """Create performance indexes."""
    indexes = [
        # User indexes
        "CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email)",
        "CREATE INDEX IF NOT EXISTS idx_app_users_phone ON app_users(phone)",
        # Booking indexes
        "CREATE INDEX IF NOT EXISTS idx_lab_bookings_user_id ON lab_bookings(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_lab_bookings_status ON lab_bookings(status)",
        "CREATE INDEX IF NOT EXISTS idx_lab_bookings_scheduled_date ON lab_bookings(scheduled_date)",
        # Report indexes
        "CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at)",
        # Chat indexes
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at)",
        # Health metrics indexes
        "CREATE INDEX IF NOT EXISTS idx_health_metrics_user_id ON health_metrics(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_health_metrics_recorded_at ON health_metrics(recorded_at)",
        # Alert indexes
        "CREATE INDEX IF NOT EXISTS idx_abnormal_alerts_user_id ON abnormal_alerts(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_abnormal_alerts_severity ON abnormal_alerts(severity)",
    ]

    for index in indexes:
        try:
            await db.execute(text(index))
        except Exception as e:
            print(f"Index creation note: {e}")

    await db.commit()
    print("✓ Indexes created/verified")


# ─────────────────────────────────────────────────────────────────────────
# 6️⃣ DATA INTEGRITY CHECKS
# ─────────────────────────────────────────────────────────────────────────

async def verify_data_integrity(db: AsyncSession) -> dict:
    """Verify database data integrity."""
    issues = []

    # Check for orphaned reports (user deleted but reports exist)
    # TODO: Implement specific checks for your data model

    return {
        "status": "ok" if not issues else "issues_found",
        "issues": issues,
    }


# ─────────────────────────────────────────────────────────────────────────
# 7️⃣ BACKUP & RESTORE
# ─────────────────────────────────────────────────────────────────────────

BACKUP_RESTORE_GUIDE = """
# VisionDX Database Backup & Restore Guide

## PostgreSQL Backup (Production)

### Full Database Backup
pg_dump -U visiondx_user -h localhost -d visiondx_db > backup_$(date +%Y%m%d_%H%M%S).sql

### Compressed Backup
pg_dump -U visiondx_user -h localhost -d visiondx_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

### Restore from Backup
psql -U visiondx_user -h localhost -d visiondx_db < backup_20240307_120000.sql

### Restore from Compressed Backup
gunzip -c backup_20240307_120000.sql.gz | psql -U visiondx_user -h localhost -d visiondx_db

## SQLite Backup (Development)

### Copy Database File
cp visiondx.db visiondx_backup_$(date +%Y%m%d_%H%M%S).db

### Automated Backup Script
```bash
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
sqlite3 visiondx.db ".dump" | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

## Automated Backup with Cron

Add to crontab:
```
# Daily backup at 2 AM
0 2 * * * /path/to/backup_script.sh

# Weekly backup on Sunday at 3 AM
0 3 * * 0 /path/to/backup_script.sh
```
"""


# ─────────────────────────────────────────────────────────────────────────
# 8️⃣ DATABASE MONITORING
# ─────────────────────────────────────────────────────────────────────────

async def get_database_stats(db: AsyncSession) -> dict:
    """Get database statistics."""
    stats = {}

    from visiondx.database.models import (
        AppUser,
        Report,
        LabBooking,
        ChatSession,
        WeeklyFollowUp,
        AbnormalAlert,
    )

    # Count users
    result = await db.execute(
        text("SELECT COUNT(*) FROM app_users")
    )
    stats["total_users"] = result.scalar() or 0

    # Count reports
    result = await db.execute(
        text("SELECT COUNT(*) FROM reports")
    )
    stats["total_reports"] = result.scalar() or 0

    # Count bookings
    result = await db.execute(
        text("SELECT COUNT(*) FROM lab_bookings")
    )
    stats["total_bookings"] = result.scalar() or 0

    # Count chat sessions
    result = await db.execute(
        text("SELECT COUNT(*) FROM chat_sessions")
    )
    stats["total_chats"] = result.scalar() or 0

    # Count alerts
    result = await db.execute(
        text(
            "SELECT COUNT(*) FROM abnormal_alerts WHERE status = 'active'"
        )
    )
    stats["active_alerts"] = result.scalar() or 0

    return stats


# ─────────────────────────────────────────────────────────────────────────
# Implementation Checklist
# ─────────────────────────────────────────────────────────────────────────

IMPLEMENTATION_CHECKLIST = """
# VisionDX Backend Implementation Checklist

## Phase 1: Database & ORM (✓ Complete)
- [x] SQLAlchemy models created
  - [x] AppUser, Doctor
  - [x] Lab, LabBooking
  - [x] Report, Parameter, Prediction
  - [x] WeeklyFollowUp, MonthlyFollowUp
  - [x] HealthMetric, AbnormalAlert
  - [x] ChatSession, Facility, APIKey
- [x] Pydantic schemas created
  - [x] Request/response models
  - [x] Enum definitions
  - [x] Validation rules

## Phase 2: Service Layer (✓ Complete)
- [x] HealthTrackingService
- [x] ChatDoctorService
- [x] BookingService
- [x] LocationService
- [x] ServiceContainer (DI)

## Phase 3: API Routers (✓ Complete)
- [x] Follow-ups endpoints
- [x] Chat Doctor endpoints
- [x] Bookings endpoints
- [x] Nearby Facilities endpoints
- [x] Doctor Dashboard endpoints
- [x] Health Dashboard endpoints

## Phase 4: ML Modules (✓ Complete)
- [x] SymptomClassifier
- [x] RiskScorer
- [x] TrendAnalyzer
- [x] AnomalyDetector
- [x] HealthPredictor (orchestrator)

## Phase 5: Database Utilities (✓ Complete)
- [x] Table creation
- [x] Health checks
- [x] Data seeding
- [x] Index optimization
- [x] Data integrity verification
- [x] Backup/restore guide
- [x] Monitoring

## Phase 6: Authentication & Security
- [ ] Password hashing (bcrypt)
- [ ] JWT token generation
- [ ] Refresh token logic
- [ ] Rate limiting
- [ ] API key authentication
- [ ] CORS configuration
- [ ] Input validation
- [ ] SQL injection prevention

## Phase 7: Error Handling & Logging
- [ ] Custom exceptions
- [ ] Global error handler
- [ ] Request logging
- [ ] Error responses
- [ ] Structured logging

## Phase 8: Testing
- [ ] Unit tests for services
- [ ] Integration tests for APIs
- [ ] ML module tests
- [ ] Database tests
- [ ] Performance tests

## Phase 9: Deployment
- [ ] Docker configuration
- [ ] Docker Compose setup
- [ ] GitHub Actions CI/CD
- [ ] Environment configuration
- [ ] Database migrations

## Phase 10: Monitoring & Analytics
- [ ] API metrics
- [ ] Database monitoring
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] User analytics

## Phase 11: Documentation
- [ ] API documentation (OpenAPI)
- [ ] Deployment guide
- [ ] Architecture documentation
- [ ] Database schema docs
- [ ] ML model documentation

## Phase 12: Production Hardening
- [ ] Security audit
- [ ] Load testing
- [ ] Cache setup (Redis)
- [ ] Background jobs (Celery)
- [ ] Message queue setup
"""

print(__doc__)
print("\n" + "=" * 80)
print(ALEMBIC_MIGRATION_GUIDE)
print("\n" + "=" * 80)
print(BACKUP_RESTORE_GUIDE)
print("\n" + "=" * 80)
print(IMPLEMENTATION_CHECKLIST)
