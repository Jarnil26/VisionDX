"""
VisionDX — Comprehensive Pydantic Schemas (Request/Response)

Production-grade request/response models with validation.
"""
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRoleEnum(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    LAB_STAFF = "lab_staff"
    ADMIN = "admin"


class BookingStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SAMPLE_COLLECTED = "sample_collected"
    PROCESSING = "processing"
    REPORT_READY = "report_ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RiskLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ───────────────────────────────────────────────────────────────────────────
# 1️⃣ AUTHENTICATION SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: str = Field(min_length=2)
    age: Optional[int] = Field(None, ge=1, le=150)
    gender: Optional[str] = Field(None, pattern="^(M|F|Other)$")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    phone: Optional[str]
    full_name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    language_preference: str = "en"
    created_at: datetime

    model_config = {"from_attributes": True}


# ───────────────────────────────────────────────────────────────────────────
# 2️⃣ LAB & BOOKING SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class LabResponse(BaseModel):
    """Lab information response."""
    id: str
    name: str
    slug: str
    address: Optional[str]
    city: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    services: list[str]  # Parsed from JSON
    is_active: bool

    model_config = {"from_attributes": True}


class BookLabTestRequest(BaseModel):
    """Book a lab test request."""
    lab_id: str
    test_type: str = Field(description="Blood, Urine, COVID, etc.")
    booking_type: str = Field(pattern="^(home|lab_visit)$")
    scheduled_date: datetime
    address: Optional[str] = None  # Required if booking_type == "home"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class LabBookingResponse(BaseModel):
    """Lab booking response."""
    id: str
    lab_id: str
    test_type: str
    booking_type: str
    status: BookingStatusEnum
    scheduled_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class LabBookingDetailResponse(LabBookingResponse):
    """Detailed booking with lab info."""
    lab: LabResponse
    address: Optional[str]


# ───────────────────────────────────────────────────────────────────────────
# 3️⃣ REPORT SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class ParameterResponse(BaseModel):
    """Lab parameter response."""
    id: str
    name: str
    value: Optional[float]
    unit: Optional[str]
    reference_range: Optional[str]
    status: str  # NORMAL, LOW, HIGH

    model_config = {"from_attributes": True}


class PredictionResponse(BaseModel):
    """ML prediction response."""
    condition: str
    confidence: float = Field(ge=0, le=1)
    severity: str  # info, warning, critical

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    """Report summary response."""
    id: str
    report_date: datetime
    pdf_url: Optional[str]
    status: str  # pending, processing, completed, failed
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ReportDetailResponse(BaseModel):
    """Detailed report response."""
    id: str
    report_date: datetime
    status: str
    parameters: list[ParameterResponse] = []
    predictions: list[PredictionResponse] = []
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ReportAnalysisResponse(BaseModel):
    """Report analysis summary."""
    total_parameters: int
    normal_count: int
    low_count: int
    high_count: int
    abnormal_parameters: list[ParameterResponse]
    predictions: list[PredictionResponse]
    risk_assessment: str


# ───────────────────────────────────────────────────────────────────────────
# 4️⃣ HEALTH TRACKING SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class WeeklyFollowUpRequest(BaseModel):
    """Weekly health check-in request."""
    week_start: datetime  # Monday of that week
    weight: Optional[float] = Field(None, ge=20, le=300)  # kg
    mood: Optional[str] = Field(None, pattern="^(happy|sad|stressed|anxious|calm|neutral)$")
    stress_level: Optional[int] = Field(None, ge=0, le=10)
    pain_level: Optional[int] = Field(None, ge=0, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    exercise: Optional[str] = None  # "30min jogging", "1hr yoga"
    diet_quality: Optional[str] = Field(None, pattern="^(poor|fair|good|excellent)$")
    symptoms: Optional[list[str]] = None  # ["headache", "fatigue"]
    notes: Optional[str] = None


class WeeklyFollowUpResponse(BaseModel):
    """Weekly follow-up response."""
    id: str
    week_start: datetime
    weight: Optional[float]
    mood: Optional[str]
    stress_level: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class MonthlyFollowUpRequest(BaseModel):
    """Monthly health report request."""
    month: str = Field(pattern="^\\d{4}-\\d{2}$")  # YYYY-MM
    weight: Optional[float]
    blood_pressure: Optional[str] = Field(None, pattern="^\\d{1,3}/\\d{1,3}$")  # 120/80
    sugar_level: Optional[float]  # mg/dL
    cholesterol: Optional[float]  # mg/dL
    lifestyle_notes: Optional[str]
    mental_health_status: Optional[str]
    recommendations: Optional[list[str]] = None


class MonthlyFollowUpResponse(BaseModel):
    """Monthly follow-up response."""
    id: str
    month: str
    weight: Optional[float]
    blood_pressure: Optional[str]
    mental_health_status: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthMetricRequest(BaseModel):
    """Record health metric request."""
    metric_name: str  # weight, bp, glucose, heart_rate, sleep_quality
    value: float
    unit: str  # kg, mmHg, mg/dL, bpm, hours
    notes: Optional[str] = None


# ───────────────────────────────────────────────────────────────────────────
# 5️⃣ AI CHAT DOCTOR SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    """Chat message request (text)."""
    message: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en")  # en, hi, gu, ta, te


class ChatVoiceRequest(BaseModel):
    """Chat voice request (audio)."""
    # Audio file sent as form-data
    language: str = Field(default="en")
    

class ConditionPrediction(BaseModel):
    """Predicted health condition."""
    condition: str
    likelihood: float = Field(ge=0, le=1)  # 0-1 confidence
    severity: RiskLevelEnum
    description: str


class ChatResponse(BaseModel):
    """Chat response from AI doctor."""
    session_id: str
    response: str  # AI's text response
    predicted_conditions: list[ConditionPrediction] = []
    risk_level: RiskLevelEnum
    confidence_score: float = Field(ge=0, le=1)
    recommended_actions: list[str] = []
    nearby_doctors_needed: bool = False
    urgent_medical_attention: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    """Chat history item."""
    session_id: str
    message: str
    response: str
    risk_level: RiskLevelEnum
    created_at: datetime

    model_config = {"from_attributes": True}


# ───────────────────────────────────────────────────────────────────────────
# 6️⃣ DOCTOR DASHBOARD SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class PatientSummary(BaseModel):
    """Patient summary for doctor."""
    user_id: str
    name: str
    age: Optional[int]
    gender: Optional[str]
    last_report_date: Optional[datetime]
    abnormal_count: int
    risk_level: RiskLevelEnum
    last_check_in: Optional[datetime]

    model_config = {"from_attributes": True}


class HighRiskPatientResponse(BaseModel):
    """High-risk patient alert."""
    user_id: str
    name: str
    age: Optional[int]
    risk_level: RiskLevelEnum
    alert_reason: str  # e.g., "Weight dropped 5kg in 2 weeks"
    recommended_action: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AbnormalAlert(BaseModel):
    """Abnormal health alert."""
    id: str
    alert_type: str
    severity: str  # info, warning, critical
    description: str
    recommended_action: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ───────────────────────────────────────────────────────────────────────────
# 7️⃣ NEARBY FACILITIES SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class FacilityResponse(BaseModel):
    """Nearby facility (hospital, clinic) response."""
    id: str
    name: str
    facility_type: str
    address: str
    city: str
    latitude: float
    longitude: float
    phone: str
    specialities: list[str]
    distance_km: Optional[float] = None  # Calculated based on user location
    available_24h: bool
    rating: Optional[float]

    model_config = {"from_attributes": True}


class FacilitySearchRequest(BaseModel):
    """Search for nearby facilities."""
    latitude: float
    longitude: float
    radius_km: int = Field(default=10, ge=1, le=100)
    facility_type: Optional[str] = None  # hospital, clinic, emergency
    speciality: Optional[str] = None  # Cardiology, Pediatrics, etc.


# ───────────────────────────────────────────────────────────────────────────
# 8️⃣ DEVELOPER/API SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class APIKeyCreateRequest(BaseModel):
    """Create new API key request."""
    name: str = Field(min_length=1, max_length=200)
    rate_limit: int = Field(default=1000, ge=10)


class APIKeyResponse(BaseModel):
    """API key response."""
    id: str
    name: str
    key_preview: str  # Last 4 chars: "...xyzabc"
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime]

    model_config = {"from_attributes": True}


class APIKeyWithSecretResponse(APIKeyResponse):
    """API key with secret (only shown on creation)."""
    secret: str  # Full API key (only shown once)


# ───────────────────────────────────────────────────────────────────────────
# 9️⃣ ERROR & GENERAL SCHEMAS
# ───────────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: str
    code: int
    timestamp: datetime


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str
    data: Optional[dict] = None


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: list[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


# ───────────────────────────────────────────────────────────────────────────
# 🔟 HEALTH DATA SUMMARY SCHEMA
# ───────────────────────────────────────────────────────────────────────────

class HealthDataSummary(BaseModel):
    """Complete health data summary for user."""
    user_id: str
    latest_report: Optional[ReportResponse]
    latest_weekly_check_in: Optional[WeeklyFollowUpResponse]
    latest_monthly_summary: Optional[MonthlyFollowUpResponse]
    abnormal_alerts: list[AbnormalAlert]
    upcoming_bookings: list[LabBookingResponse]
    health_score: float = Field(ge=0, le=100)  # Overall health score
    risk_assessment: RiskLevelEnum
    recommendations: list[str]

    model_config = {"from_attributes": True}
