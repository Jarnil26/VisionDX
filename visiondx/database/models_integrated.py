"""
VisionDX — Complete SQLAlchemy ORM Models

Production-grade models with relationships, indexing, and constraints.
"""
from datetime import datetime
from enum import Enum
import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from visiondx.database.connection import Base


def _uuid() -> str:
    """Generate UUID string."""
    return str(uuid.uuid4())


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    """User roles for RBAC."""
    PATIENT = "patient"
    DOCTOR = "doctor"
    LAB_STAFF = "lab_staff"
    ADMIN = "admin"


class BookingStatus(str, Enum):
    """Booking lifecycle states."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SAMPLE_COLLECTED = "sample_collected"
    PROCESSING = "processing"
    REPORT_READY = "report_ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReportStatus(str, Enum):
    """Report processing states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ParameterStatus(str, Enum):
    """Lab parameter value status."""
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"


class RiskLevel(str, Enum):
    """Health risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ─── Core User Models ────────────────────────────────────────────────────────

class AppUser(Base):
    """Patient/user account."""
    __tablename__ = "app_users"
    __table_args__ = (
        Index("idx_email", "email"),
        Index("idx_phone", "phone"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(300))
    full_name: Mapped[str | None] = mapped_column(String(200))
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(20))  # M, F, Other
    medical_history: Mapped[str | None] = mapped_column(Text)  # Previous conditions, allergies
    language_preference: Mapped[str] = mapped_column(String(10), default="en")  # en, hi, gu, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="app_user", cascade="all, delete-orphan")
    weekly_follow_ups: Mapped[list["WeeklyFollowUp"]] = relationship("WeeklyFollowUp", back_populates="app_user", cascade="all, delete-orphan")
    monthly_follow_ups: Mapped[list["MonthlyFollowUp"]] = relationship("MonthlyFollowUp", back_populates="app_user", cascade="all, delete-orphan")
    bookings: Mapped[list["LabBooking"]] = relationship("LabBooking", back_populates="app_user")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="app_user", cascade="all, delete-orphan")
    health_metrics: Mapped[list["HealthMetric"]] = relationship("HealthMetric", back_populates="app_user", cascade="all, delete-orphan")
    alerts: Mapped[list["AbnormalAlert"]] = relationship("AbnormalAlert", back_populates="app_user", cascade="all, delete-orphan")


class Doctor(Base):
    """Doctor account for accessing patient data."""
    __tablename__ = "doctors"
    __table_args__ = (
        Index("idx_email", "email"),
        Index("idx_speciality", "speciality"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(300))
    full_name: Mapped[str] = mapped_column(String(200))
    speciality: Mapped[str | None] = mapped_column(String(100))  # Cardiology, Pediatrics, etc.
    license_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    hospital_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("facilities.id"))
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hospital: Mapped["Facility | None"] = relationship("Facility", back_populates="doctors")


# ─── Lab System ──────────────────────────────────────────────────────────────

class Lab(Base):
    """Partner medical lab."""
    __tablename__ = "labs"
    __table_args__ = (
        Index("idx_slug", "slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    api_key_hash: Mapped[str | None] = mapped_column(String(255))  # For Lab API auth
    address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(200))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    services: Mapped[str] = mapped_column(Text)  # JSON array of services
    operating_hours: Mapped[str | None] = mapped_column(Text)  # JSON
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bookings: Mapped[list["LabBooking"]] = relationship("LabBooking", back_populates="lab")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="lab")


class LabBooking(Base):
    """Blood test booking with home sample or lab visit."""
    __tablename__ = "lab_bookings"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_lab_id", "lab_id"),
        Index("idx_status", "status"),
        Index("idx_scheduled_date", "scheduled_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id"))
    lab_id: Mapped[str] = mapped_column(String(36), ForeignKey("labs.id"))
    test_type: Mapped[str] = mapped_column(String(100))  # Blood, Urine, COVID, etc.
    booking_type: Mapped[str] = mapped_column(String(20))  # home | lab_visit
    address: Mapped[str | None] = mapped_column(String(500))  # For home sample
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="bookings")
    lab: Mapped["Lab"] = relationship("Lab", back_populates="bookings")
    report: Mapped["Report | None"] = relationship("Report", back_populates="booking", foreign_keys="Report.booking_id")


# ─── Report System ───────────────────────────────────────────────────────────

class Report(Base):
    """Lab report uploaded or received from partner lab."""
    __tablename__ = "reports"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_lab_id", "lab_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id"))
    lab_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("labs.id"), nullable=True)
    booking_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("lab_bookings.id"), nullable=True)
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pdf_url: Mapped[str | None] = mapped_column(String(500))  # S3 or local path
    raw_text: Mapped[str | None] = mapped_column(Text)  # Extracted text from OCR
    status: Mapped[str] = mapped_column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="reports")
    lab: Mapped["Lab | None"] = relationship("Lab", back_populates="reports")
    booking: Mapped["LabBooking | None"] = relationship("LabBooking", back_populates="report", foreign_keys="Report.booking_id")
    parameters: Mapped[list["Parameter"]] = relationship("Parameter", back_populates="report", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="report", cascade="all, delete-orphan")


class Parameter(Base):
    """Medical parameter extracted from report."""
    __tablename__ = "parameters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id"))
    name: Mapped[str] = mapped_column(String(200))  # Normalized: Hemoglobin, WBC, etc.
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(50))
    reference_range: Mapped[str | None] = mapped_column(String(100))  # e.g., "13-17"
    status: Mapped[str] = mapped_column(SQLEnum(ParameterStatus), default=ParameterStatus.NORMAL)

    report: Mapped["Report"] = relationship("Report", back_populates="parameters")


class Prediction(Base):
    """ML prediction of possible condition from report."""
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id"))
    condition: Mapped[str] = mapped_column(String(200))  # Possible condition
    confidence: Mapped[float] = mapped_column(Float)  # 0-1
    severity: Mapped[str] = mapped_column(SQLEnum(AlertSeverity))
    details: Mapped[str | None] = mapped_column(Text)  # Additional info
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    report: Mapped["Report"] = relationship("Report", back_populates="predictions")


# ─── Health Tracking ────────────────────────────────────────────────────────

class WeeklyFollowUp(Base):
    """Weekly health check-in."""
    __tablename__ = "weekly_follow_ups"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_week_start", "week_start"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id"))
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # Monday of that week
    weight: Mapped[float | None] = mapped_column(Float)  # kg
    mood: Mapped[str | None] = mapped_column(String(50))  # happy, sad, stressed, anxious
    stress_level: Mapped[int | None] = mapped_column(Integer)  # 0-10
    pain_level: Mapped[int | None] = mapped_column(Integer)  # 0-10
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    exercise: Mapped[str | None] = mapped_column(String(200))  # "30min jogging", etc.
    diet_quality: Mapped[str | None] = mapped_column(String(50))  # poor, fair, good, excellent
    symptoms: Mapped[str | None] = mapped_column(Text)  # Array of symptoms: ["headache", "fatigue"]
    notes: Mapped[str | None] = mapped_column(Text)  # User notes
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="weekly_follow_ups")


class MonthlyFollowUp(Base):
    """Detailed monthly health report."""
    __tablename__ = "monthly_follow_ups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id"))
    month: Mapped[str] = mapped_column(String(7))  # YYYY-MM
    weight: Mapped[float | None] = mapped_column(Float)
    blood_pressure: Mapped[str | None] = mapped_column(String(20))  # "120/80"
    sugar_level: Mapped[float | None] = mapped_column(Float)  # mg/dL
    cholesterol: Mapped[float | None] = mapped_column(Float)  # mg/dL
    lifestyle_notes: Mapped[str | None] = mapped_column(Text)  # Overall lifestyle summary
    mental_health_status: Mapped[str | None] = mapped_column(String(100))  # Good, Fair, Poor
    doctor_notes: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="monthly_follow_ups")


# ─── Health Metrics ─────────────────────────────────────────────────────────

class HealthMetric(Base):
    """Individual health metric tracking."""
    __tablename__ = "health_metrics"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_metric_name", "metric_name"),
        Index("idx_recorded_at", "recorded_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id"))
    metric_name: Mapped[str] = mapped_column(String(100))  # weight, bp, glucose, heart_rate, etc.
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))  # kg, mmHg, mg/dL, bpm
    notes: Mapped[str | None] = mapped_column(String(300))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="health_metrics")


# ─── AI Chat System ─────────────────────────────────────────────────────────

class ChatSession(Base):
    """Chat with AI doctor conversation history."""
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id"))
    message_text: Mapped[str] = mapped_column(Text)  # User's message
    message_type: Mapped[str] = mapped_column(String(20))  # text | voice
    transcription: Mapped[str | None] = mapped_column(Text)  # If voice input
    response_text: Mapped[str] = mapped_column(Text)  # AI response
    predicted_conditions: Mapped[str] = mapped_column(Text)  # JSON array
    risk_level: Mapped[str] = mapped_column(SQLEnum(RiskLevel))
    confidence_score: Mapped[float | None] = mapped_column(Float)  # 0-1
    recommended_action: Mapped[str | None] = mapped_column(Text)
    nearby_doctors_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="chat_sessions")


# ─── Alerts & Monitoring ───────────────────────────────────────────────────

class AbnormalAlert(Base):
    """Alert for abnormal health patterns."""
    __tablename__ = "abnormal_alerts"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_severity", "severity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id"))
    alert_type: Mapped[str] = mapped_column(String(50))  # weight_drop, sugar_rise, stress_high, etc.
    severity: Mapped[str] = mapped_column(SQLEnum(AlertSeverity))
    description: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | acknowledged | resolved
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="alerts")


# ─── Nearby Facilities ──────────────────────────────────────────────────────

class Facility(Base):
    """Hospital, clinic, or medical facility."""
    __tablename__ = "facilities"
    __table_args__ = (
        Index("idx_name", "name"),
        Index("idx_type", "facility_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    facility_type: Mapped[str] = mapped_column(String(50))  # hospital | clinic | emergency
    address: Mapped[str] = mapped_column(String(500))
    city: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(200))
    specialities: Mapped[str] = mapped_column(Text)  # JSON array
    available_24h: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[float | None] = mapped_column(Float)  # 0-5
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    doctors: Mapped[list["Doctor"]] = relationship("Doctor", back_populates="hospital")


# ─── API & Developer Management ─────────────────────────────────────────────

class APIKey(Base):
    """Developer API key for accessing public API."""
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_key_hash", "key_hash", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id"))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True)  # SHA256 of actual key
    name: Mapped[str] = mapped_column(String(200))  # "Production API Key"
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000)  # Requests per hour
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # Optional expiration

    app_user: Mapped["AppUser"] = relationship("AppUser")
