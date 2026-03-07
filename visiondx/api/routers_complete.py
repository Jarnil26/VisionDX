"""
VisionDX — Complete API Routers

RESTful API endpoints for all platform features.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.database.connection import get_db
from visiondx.services.service_layer import (
    HealthTrackingService,
    ChatDoctorService,
    BookingService,
    LocationService,
    ServiceContainer,
)
from visiondx.database.schemas_complete import (
    WeeklyFollowUpRequest,
    WeeklyFollowUpResponse,
    MonthlyFollowUpRequest,
    MonthlyFollowUpResponse,
    LabResponse,
    BookingStatusEnum,
    LabBookingResponse,
    LabBookingDetailResponse,
    ChatMessageRequest,
    ChatResponse,
    ChatHistoryResponse,
    FacilitySearchRequest,
    FacilityResponse,
    ReportDetailResponse,
    PatientSummary,
    HighRiskPatientResponse,
    AbnormalAlert,
    HealthDataSummary,
)


# ─────────────────────────────────────────────────────────────────────────
# 1️⃣ FOLLOW-UPS ROUTER
# ─────────────────────────────────────────────────────────────────────────

follow_ups_router = APIRouter(prefix="/follow-ups", tags=["Health Tracking"])


@follow_ups_router.post("/weekly", response_model=WeeklyFollowUpResponse)
async def create_weekly_followup(
    request: WeeklyFollowUpRequest,
    user_id: str,  # From JWT token - would be dependency
    db: AsyncSession = Depends(get_db),
):
    """
    Submit weekly health check-in.

    **Fields:**
    - weight: Current weight in kg
    - mood: happy, sad, stressed, anxious, calm, neutral
    - stress_level: 0-10 scale
    - pain_level: 0-10 scale
    - sleep_hours: Hours of sleep
    - exercise: Exercise description
    - diet_quality: poor, fair, good, excellent
    - symptoms: Array of symptoms
    - notes: Additional notes
    """
    service = HealthTrackingService(db)
    followup = await service.create_weekly_followup(
        user_id=user_id,
        week_start=request.week_start,
        weight=request.weight,
        mood=request.mood,
        stress_level=request.stress_level,
        pain_level=request.pain_level,
        sleep_hours=request.sleep_hours,
        exercise=request.exercise,
        diet_quality=request.diet_quality,
        symptoms=request.symptoms,
        notes=request.notes,
    )
    return WeeklyFollowUpResponse.model_validate(followup)


@follow_ups_router.get("/weekly", response_model=list[WeeklyFollowUpResponse])
async def get_weekly_history(
    user_id: str,
    weeks: int = Query(4, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly follow-up history."""
    service = HealthTrackingService(db)
    followups = await service.get_weekly_history(user_id, weeks=weeks)
    return [WeeklyFollowUpResponse.model_validate(f) for f in followups]


@follow_ups_router.post("/monthly", response_model=MonthlyFollowUpResponse)
async def create_monthly_followup(
    request: MonthlyFollowUpRequest,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit monthly health report.

    **Fields:**
    - month: YYYY-MM format
    - weight: Current weight
    - blood_pressure: Format "120/80"
    - sugar_level: mg/dL
    - cholesterol: mg/dL
    - lifestyle_notes: Summary of lifestyle
    - mental_health_status: Good, Fair, Poor
    - recommendations: Array of suggestions
    """
    service = HealthTrackingService(db)
    followup = await service.create_monthly_followup(
        user_id=user_id,
        month=request.month,
        weight=request.weight,
        blood_pressure=request.blood_pressure,
        sugar_level=request.sugar_level,
        cholesterol=request.cholesterol,
        lifestyle_notes=request.lifestyle_notes,
        mental_health_status=request.mental_health_status,
        doctor_notes=None,
        recommendations=request.recommendations,
    )
    return MonthlyFollowUpResponse.model_validate(followup)


@follow_ups_router.get("/monthly", response_model=list[MonthlyFollowUpResponse])
async def get_monthly_history(
    user_id: str,
    months: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
):
    """Get monthly follow-up history."""
    # TODO: Implement monthly history retrieval
    pass


# ─────────────────────────────────────────────────────────────────────────
# 2️⃣ CHAT DOCTOR ROUTER
# ─────────────────────────────────────────────────────────────────────────

chat_router = APIRouter(prefix="/chat", tags=["AI Chat Doctor"])


@chat_router.post("", response_model=ChatResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Send message to AI Chat Doctor (text input).

    **Request:**
    - message: User's symptom description
    - language: en, hi, gu, ta, te (optional, defaults to en)

    **Response:**
    - response: AI's response
    - predicted_conditions: List of possible conditions with confidence
    - risk_level: low, medium, high, critical
    - recommended_actions: List of suggested actions
    - nearby_doctors_needed: Whether to show nearby doctors
    """
    service = ChatDoctorService(db)
    chat = await service.process_chat_message(
        user_id=user_id,
        message=request.message,
        language=request.language,
        message_type="text",
    )
    return ChatResponse.model_validate(chat)


@chat_router.post("/voice", response_model=ChatResponse)
async def send_voice_message(
    file: UploadFile = File(...),
    user_id: str = Query(...),
    language: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    """
    Send voice message to AI Chat Doctor.

    **Request:**
    - file: Audio file (WAV, MP3, M4A)
    - language: Language of voice (en, hi, gu, etc.)

    **Process:**
    1. Transcribe audio to text
    2. Run same analysis as text chat
    3. Return response with transcription

    **Response:**
    Same as text chat, plus transcription field
    """
    # TODO: Implement voice transcription (Whisper API)
    # Convert audio to text
    # Then call service.process_chat_message()
    pass


@chat_router.get("/history", response_model=list[ChatHistoryResponse])
async def get_chat_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for user."""
    # TODO: Implement chat history retrieval
    pass


# ─────────────────────────────────────────────────────────────────────────
# 3️⃣ BOOKINGS ROUTER
# ─────────────────────────────────────────────────────────────────────────

bookings_router = APIRouter(prefix="/bookings", tags=["Lab Bookings"])


@bookings_router.post("", response_model=LabBookingResponse)
async def create_booking(
    lab_id: str,
    test_type: str,
    booking_type: str,  # home | lab_visit
    scheduled_date: datetime,
    user_id: str,
    address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Book a lab test.

    **Parameters:**
    - lab_id: Lab partner ID
    - test_type: Blood, Urine, COVID, etc.
    - booking_type: "home" or "lab_visit"
    - scheduled_date: Appointment datetime
    - address: Address (required if booking_type == "home")
    """
    service = BookingService(db)
    booking = await service.create_booking(
        user_id=user_id,
        lab_id=lab_id,
        test_type=test_type,
        booking_type=booking_type,
        scheduled_date=scheduled_date,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )
    return LabBookingResponse.model_validate(booking)


@bookings_router.get("", response_model=list[LabBookingDetailResponse])
async def get_my_bookings(
    user_id: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get user's bookings."""
    service = BookingService(db)
    bookings = await service.get_user_bookings(user_id)

    if status:
        bookings = [b for b in bookings if b.status == status]

    return [LabBookingDetailResponse.model_validate(b) for b in bookings]


@bookings_router.get("/{booking_id}", response_model=LabBookingDetailResponse)
async def get_booking(
    booking_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get booking details."""
    # TODO: Implement get_booking
    pass


@bookings_router.patch("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel booking."""
    service = BookingService(db)
    success = await service.cancel_booking(booking_id, user_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Booking not found or unauthorized",
        )

    return {"success": True, "message": "Booking cancelled"}


# ─────────────────────────────────────────────────────────────────────────
# 4️⃣ NEARBY FACILITIES ROUTER
# ─────────────────────────────────────────────────────────────────────────

nearby_router = APIRouter(prefix="/nearby", tags=["Find Doctors/Hospitals"])


@nearby_router.post("/doctors", response_model=list[FacilityResponse])
async def find_nearby_doctors(
    request: FacilitySearchRequest,
    speciality: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Find nearby doctors.

    **Parameters:**
    - latitude, longitude: User's current location
    - radius_km: Search radius (default 10km, max 100km)
    - speciality: Filter by medical speciality (optional)

    **Example Specialities:**
    - Cardiology
    - Pediatrics
    - Gastroenterology
    - Orthopedics
    - Gynecology
    """
    service = LocationService(db)
    facilities = await service.find_nearby_facilities(
        latitude=request.latitude,
        longitude=request.longitude,
        radius_km=request.radius_km,
        facility_type="clinic",
        speciality=speciality,
    )

    return [FacilityResponse.model_validate(f["facility"]) for f in facilities]


@nearby_router.post("/hospitals", response_model=list[FacilityResponse])
async def find_nearby_hospitals(
    request: FacilitySearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Find nearby hospitals."""
    service = LocationService(db)
    facilities = await service.find_nearby_facilities(
        latitude=request.latitude,
        longitude=request.longitude,
        radius_km=request.radius_km,
        facility_type="hospital",
    )

    return [FacilityResponse.model_validate(f["facility"]) for f in facilities]


@nearby_router.post("/emergency", response_model=list[FacilityResponse])
async def find_emergency_services(
    request: FacilitySearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Find nearby emergency services (hospitals with 24h availability)."""
    service = LocationService(db)
    facilities = await service.find_nearby_facilities(
        latitude=request.latitude,
        longitude=request.longitude,
        radius_km=request.radius_km,
        facility_type="hospital",
    )

    # Filter for 24h facilities
    emergency = [
        f
        for f in facilities
        if f.get("facility") and f["facility"].available_24h
    ]

    return [FacilityResponse.model_validate(f["facility"]) for f in emergency]


# ─────────────────────────────────────────────────────────────────────────
# 5️⃣ DOCTOR DASHBOARD ROUTER
# ─────────────────────────────────────────────────────────────────────────

doctor_router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])


@doctor_router.get("/patients", response_model=list[PatientSummary])
async def get_patients_list(
    doctor_id: str,
    risk_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of patients (for doctor).

    **Optional filters:**
    - risk_level: low, medium, high, critical
    """
    # TODO: Implement doctor-patient relationship
    # For now, return empty list
    pass


@doctor_router.get("/high-risk", response_model=list[HighRiskPatientResponse])
async def get_high_risk_patients(
    doctor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get high-risk patients requiring immediate attention."""
    # TODO: Query alerts and predict high-risk patients
    pass


@doctor_router.get("/reports", response_model=list[ReportDetailResponse])
async def get_abnormal_reports(
    doctor_id: str,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get reports with abnormal findings."""
    # TODO: Query reports with abnormal parameters
    pass


@doctor_router.get("/alerts", response_model=list[AbnormalAlert])
async def get_patient_alerts(
    doctor_id: str,
    status: str = "active",
    db: AsyncSession = Depends(get_db),
):
    """Get active alerts for doctor's patients."""
    # TODO: Implement alert query
    pass


# ─────────────────────────────────────────────────────────────────────────
# 6️⃣ HEALTH DASHBOARD ROUTER
# ─────────────────────────────────────────────────────────────────────────

health_router = APIRouter(prefix="/health", tags=["Health Dashboard"])


@health_router.get("/summary", response_model=HealthDataSummary)
async def get_health_summary(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete health data summary for user.

    **Returns:**
    - Latest report
    - Latest weekly check-in
    - Latest monthly summary
    - Active alerts
    - Upcoming bookings
    - Overall health score
    - Risk assessment
    - Personalized recommendations
    """
    # TODO: Aggregate all health data for user
    pass


@health_router.get("/trends")
async def get_health_trends(
    user_id: str,
    metric: str,  # weight, bp, glucose, sleep, etc.
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Get health metric trends over time.

    **Metrics:**
    - weight
    - blood_pressure
    - glucose
    - sleep_hours
    - stress_level
    - exercise
    """
    # TODO: Query and aggregate health metrics
    pass


# ─────────────────────────────────────────────────────────────────────────
# Example Combined Router Usage
# ─────────────────────────────────────────────────────────────────────────

def create_routers() -> APIRouter:
    """Create combined router with all endpoints."""
    main_router = APIRouter()

    main_router.include_router(follow_ups_router)
    main_router.include_router(chat_router)
    main_router.include_router(bookings_router)
    main_router.include_router(nearby_router)
    main_router.include_router(doctor_router)
    main_router.include_router(health_router)

    return main_router
