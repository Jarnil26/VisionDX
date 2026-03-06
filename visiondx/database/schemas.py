"""
VisionDX — Pydantic v2 Schemas (Request / Response)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, EmailStr


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
