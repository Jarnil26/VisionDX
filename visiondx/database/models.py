"""
VisionDX — SQLAlchemy ORM Models

Tables:
  - patients
  - reports
  - parameters
  - predictions
  - users  (lab staff / doctors)
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from visiondx.database.connection import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="patient", cascade="all, delete-orphan"
    )


class AppUser(Base):
    """App patient/user — sign up with email or mobile, profile (age, gender, medical history)."""
    __tablename__ = "app_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(300), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    medical_history: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON or free text
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="app_user"
    )
    weekly_follow_ups: Mapped[list["WeeklyFollowUp"]] = relationship(
        "WeeklyFollowUp", back_populates="app_user", cascade="all, delete-orphan"
    )
    monthly_follow_ups: Mapped[list["MonthlyFollowUp"]] = relationship(
        "MonthlyFollowUp", back_populates="app_user", cascade="all, delete-orphan"
    )
    lab_bookings: Mapped[list["LabBooking"]] = relationship(
        "LabBooking", back_populates="app_user"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="app_user", cascade="all, delete-orphan"
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    report_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    app_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("app_users.id"), nullable=True, index=True
    )
    patient_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=True
    )
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False
    )  # pending | processing | done | error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    lab_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    app_user: Mapped["AppUser | None"] = relationship(
        "AppUser", back_populates="reports"
    )
    patient: Mapped["Patient | None"] = relationship(
        "Patient", back_populates="reports"
    )
    parameters: Mapped[list["Parameter"]] = relationship(
        "Parameter", back_populates="report", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="report", cascade="all, delete-orphan"
    )


class Parameter(Base):
    __tablename__ = "parameters"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    report_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("reports.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    raw_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(10), default="NORMAL", nullable=False
    )  # NORMAL | LOW | HIGH

    report: Mapped["Report"] = relationship("Report", back_populates="parameters")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    report_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("reports.id"), nullable=False
    )
    disease: Mapped[str] = mapped_column(String(200), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    report: Mapped["Report"] = relationship("Report", back_populates="predictions")


class User(Base):
    """Lab staff & doctors who access the system."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(300), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default="lab_staff")  # lab_staff | doctor | admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ─── Lab collaboration ───────────────────────────────────────────────────────

class Lab(Base):
    """Partner lab — certified medical lab for home sample / lab visit."""
    __tablename__ = "labs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    api_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # for Lab API auth
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    supports_home_collection: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    bookings: Mapped[list["LabBooking"]] = relationship(
        "LabBooking", back_populates="lab"
    )


class LabBooking(Base):
    """User's lab test booking — home sample or lab visit."""
    __tablename__ = "lab_bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    app_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_users.id"), nullable=False, index=True
    )
    lab_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("labs.id"), nullable=False, index=True
    )
    collection_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # home | lab_visit
    test_type: Mapped[str | None] = mapped_column(String(200), nullable=True)  # e.g. "CBC", "Blood Sugar"
    status: Mapped[str] = mapped_column(
        String(30), default="scheduled", nullable=False
    )  # scheduled | sample_collected | processing | report_ready | cancelled
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    report_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )  # link to Report.report_id when report is uploaded
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="lab_bookings")
    lab: Mapped["Lab"] = relationship("Lab", back_populates="bookings")


# ─── Weekly & monthly follow-up ───────────────────────────────────────────────

class WeeklyFollowUp(Base):
    """Weekly health summary — mood, symptoms, diet & lifestyle."""
    __tablename__ = "weekly_follow_ups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    app_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_users.id"), nullable=False, index=True
    )
    week_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # Monday of the week
    mood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–5 or 1–10
    mental_state: Mapped[str | None] = mapped_column(Text, nullable=True)  # sad, anxious, depressed, stressed, calm, happy (comma-sep or JSON)
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0–10 scale
    pain_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # location/details
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: ["fatigue", "headache"]
    diet_lifestyle: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON or text
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    app_user: Mapped["AppUser"] = relationship(
        "AppUser", back_populates="weekly_follow_ups"
    )


class MonthlyFollowUp(Base):
    """Monthly comprehensive health evaluation — trends, recommendations."""
    __tablename__ = "monthly_follow_ups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    app_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_users.id"), nullable=False, index=True
    )
    month_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # First day of month
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    health_trends: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_alerts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    app_user: Mapped["AppUser"] = relationship(
        "AppUser", back_populates="monthly_follow_ups"
    )


# ─── AI Chat Doctor ───────────────────────────────────────────────────────────

class ChatSession(Base):
    """Chat session for AI doctor — one per user conversation thread."""
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    app_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    app_user: Mapped["AppUser"] = relationship(
        "AppUser", back_populates="chat_sessions"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    """Single message in a chat session."""
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    emergency_alert: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="messages"
    )
