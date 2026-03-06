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


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    report_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
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
