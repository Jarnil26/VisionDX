"""
VisionDX — Pydantic v2 Schemas (Request / Response)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, EmailStr, model_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    role: str = "lab_staff"


# ── Parameters ────────────────────────────────────────────────────────────────

class ParameterOut(BaseModel):
    name: str
    raw_name: str | None = None
    value: float | None = None
    raw_value: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: str  # NORMAL | LOW | HIGH

    model_config = {"from_attributes": True}


# ── Patient ───────────────────────────────────────────────────────────────────

class PatientOut(BaseModel):
    id: str
    name: str
    age: int | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None

    model_config = {"from_attributes": True}


# ── Prediction ────────────────────────────────────────────────────────────────

class PredictionOut(BaseModel):
    disease: str
    confidence: float

    model_config = {"from_attributes": True}


class PredictionResponse(BaseModel):
    report_id: str
    possible_conditions: list[PredictionOut]


# ── Report ────────────────────────────────────────────────────────────────────

class ReportOut(BaseModel):
    report_id: str
    status: str
    report_date: str | None = None
    lab_name: str | None = None
    created_at: datetime
    processed_at: datetime | None = None
    patient: PatientOut | None = None
    parameters: list[ParameterOut] = []

    model_config = {"from_attributes": True}


class ReportAnalysisResponse(BaseModel):
    report_id: str
    total_parameters: int
    abnormal_count: int
    normal_count: int
    parameters: list[ParameterOut]
    summary: str


class FullReportResponse(BaseModel):
    """Doctor-facing full report view."""
    report_id: str
    status: str
    patient: PatientOut | None = None
    parameters: list[ParameterOut] = []
    predictions: list[PredictionOut] = []
    summary: str
    pdf_url: str | None = None


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    report_id: str
    message: str
    status: str


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


# ── Parsed Report (internal pipeline result) ──────────────────────────────────

class ParsedParameter(BaseModel):
    name: str
    raw_name: str | None = None
    value: float | None = None
    raw_value: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: str = "NORMAL"


class ParsedReport(BaseModel):
    patient_name: str = "Unknown"
    age: str | None = None
    gender: str | None = None
    report_id: str = ""
    date: str | None = None
    lab_name: str | None = None
    parameters: list[ParsedParameter] = []
    raw_text: str = ""


# ─── App User (Patient) ──────────────────────────────────────────────────────

class AppUserRegisterRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str = Field(min_length=8)
    full_name: str | None = None
    age: int | None = None
    gender: str | None = None
    medical_history: str | None = None

    @model_validator(mode="after")
    def require_email_or_phone(self) -> "AppUserRegisterRequest":
        if not self.email and not self.phone:
            raise ValueError("Either email or phone is required")
        return self


class AppUserLoginRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str

    @model_validator(mode="after")
    def require_email_or_phone(self) -> "AppUserLoginRequest":
        if not self.email and not self.phone:
            raise ValueError("Either email or phone is required")
        return self


class AppUserProfileUpdate(BaseModel):
    full_name: str | None = None
    age: int | None = None
    gender: str | None = None
    medical_history: str | None = None


class AppUserOut(BaseModel):
    id: str
    email: str | None = None
    phone: str | None = None
    full_name: str | None = None
    age: int | None = None
    gender: str | None = None
    medical_history: str | None = None

    model_config = {"from_attributes": True}


# ─── Lab & Booking ───────────────────────────────────────────────────────────

class LabOut(BaseModel):
    id: str
    name: str
    slug: str
    address: str | None = None
    phone: str | None = None
    supports_home_collection: bool = True

    model_config = {"from_attributes": True}


class LabBookingCreate(BaseModel):
    lab_id: str
    collection_type: str = "home"  # home | lab_visit
    test_type: str | None = None
    scheduled_at: datetime | None = None


class LabBookingOut(BaseModel):
    id: str
    lab_id: str
    collection_type: str
    test_type: str | None = None
    status: str
    scheduled_at: datetime | None = None
    report_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Weekly / Monthly Follow-Up ──────────────────────────────────────────────

class WeeklyFollowUpCreate(BaseModel):
    week_start_date: datetime
    mood_score: int | None = None  # 1–10
    mental_state: str | None = None  # e.g. "sad", "anxious", "depressed", "stressed", "calm", "happy" (comma-sep)
    pain_level: int | None = None  # 0–10
    pain_notes: str | None = None  # e.g. "back", "head"
    symptoms: str | None = None  # JSON or comma-separated: fatigue, headache, etc.
    diet_lifestyle: str | None = None
    weight_kg: float | None = None
    notes: str | None = None


class WeeklyFollowUpOut(BaseModel):
    id: str
    week_start_date: datetime
    mood_score: int | None = None
    mental_state: str | None = None
    pain_level: int | None = None
    pain_notes: str | None = None
    symptoms: str | None = None
    diet_lifestyle: str | None = None
    weight_kg: float | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MonthlyFollowUpCreate(BaseModel):
    month_start: datetime
    summary: str | None = None
    health_trends: str | None = None
    recommendations: str | None = None
    medical_alerts: str | None = None


class MonthlyFollowUpOut(BaseModel):
    id: str
    month_start: datetime
    summary: str | None = None
    health_trends: str | None = None
    recommendations: str | None = None
    medical_alerts: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── AI Chat ──────────────────────────────────────────────────────────────────

class ChatMessageIn(BaseModel):
    message: str
    session_id: str | None = None
    lang: str | None = None  # e.g. en, hi, es — for future response localization


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    suggestions: list[Any] | None = None
    emergency_alert: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    suggestions: list[Any] = []
    emergency_alert: bool = False
    nearby_facilities: list[dict[str, Any]] = []


# ─── Doctor dashboard (abnormal reports) ──────────────────────────────────────

class AbnormalReportItem(BaseModel):
    report_id: str
    abnormal_count: int
    patient_name: str | None = None
    app_user_id: str | None = None
    report_date: str | None = None
    lab_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
