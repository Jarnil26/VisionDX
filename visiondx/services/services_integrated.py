"""
VisionDX — Core Service Layer

Business logic implementation for healthcare features.
"""
from datetime import datetime, timedelta
import json
from typing import Optional
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from visiondx.database.models import (
    AppUser,
    LabBooking,
    WeeklyFollowUp,
    MonthlyFollowUp,
    ChatSession,
    Report,
    Parameter,
    HealthMetric,
    AbnormalAlert,
)


# ─────────────────────────────────────────────────────────────────────────
# 1️⃣ HEALTH TRACKING SERVICE
# ─────────────────────────────────────────────────────────────────────────

class HealthTrackingService:
    """Service for weekly/monthly health tracking and analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_weekly_followup(
        self,
        user_id: str,
        week_start: datetime,
        weight: Optional[float],
        mood: Optional[str],
        stress_level: Optional[int],
        pain_level: Optional[int],
        sleep_hours: Optional[float],
        exercise: Optional[str],
        diet_quality: Optional[str],
        symptoms: Optional[list[str]],
        notes: Optional[str],
    ) -> WeeklyFollowUp:
        """Create weekly health follow-up."""
        followup = WeeklyFollowUp(
            user_id=user_id,
            week_start=week_start,
            weight=weight,
            mood=mood,
            stress_level=stress_level,
            pain_level=pain_level,
            sleep_hours=sleep_hours,
            exercise=exercise,
            diet_quality=diet_quality,
            symptoms=json.dumps(symptoms) if symptoms else None,
            notes=notes,
        )
        self.db.add(followup)
        await self.db.commit()
        await self.db.refresh(followup)

        # Check for anomalies
        await self._detect_anomalies(user_id)

        return followup

    async def get_weekly_history(
        self, user_id: str, weeks: int = 4
    ) -> list[WeeklyFollowUp]:
        """Get weekly follow-up history."""
        cutoff_date = datetime.utcnow() - timedelta(weeks=weeks)
        result = await self.db.execute(
            select(WeeklyFollowUp)
            .where(
                and_(
                    WeeklyFollowUp.user_id == user_id,
                    WeeklyFollowUp.week_start >= cutoff_date,
                )
            )
            .order_by(WeeklyFollowUp.week_start.desc())
        )
        return result.scalars().all()

    async def create_monthly_followup(
        self,
        user_id: str,
        month: str,  # YYYY-MM
        weight: Optional[float],
        blood_pressure: Optional[str],
        sugar_level: Optional[float],
        cholesterol: Optional[float],
        lifestyle_notes: Optional[str],
        mental_health_status: Optional[str],
        doctor_notes: Optional[str],
        recommendations: Optional[list[str]],
    ) -> MonthlyFollowUp:
        """Create monthly health report."""
        followup = MonthlyFollowUp(
            user_id=user_id,
            month=month,
            weight=weight,
            blood_pressure=blood_pressure,
            sugar_level=sugar_level,
            cholesterol=cholesterol,
            lifestyle_notes=lifestyle_notes,
            mental_health_status=mental_health_status,
            doctor_notes=doctor_notes,
            recommendations=json.dumps(recommendations) if recommendations else None,
        )
        self.db.add(followup)
        await self.db.commit()
        await self.db.refresh(followup)
        return followup

    async def _detect_anomalies(self, user_id: str) -> None:
        """Detect anomalies in health data."""
        # Get last 4 weeks of data
        four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
        result = await self.db.execute(
            select(WeeklyFollowUp)
            .where(
                and_(
                    WeeklyFollowUp.user_id == user_id,
                    WeeklyFollowUp.week_start >= four_weeks_ago,
                )
            )
            .order_by(WeeklyFollowUp.week_start)
        )
        followups = result.scalars().all()

        if len(followups) < 2:
            return  # Not enough data

        # Example: Check for weight drop
        first_weight = followups[0].weight
        last_weight = followups[-1].weight

        if (
            first_weight
            and last_weight
            and (first_weight - last_weight) > 5
        ):  # Drop > 5kg in 4 weeks
            alert = AbnormalAlert(
                user_id=user_id,
                alert_type="weight_drop",
                severity="warning",
                description=f"Weight dropped {first_weight - last_weight:.1f}kg in 4 weeks",
                recommended_action="Consult with doctor for health evaluation",
                status="active",
            )
            self.db.add(alert)
            await self.db.commit()


# ─────────────────────────────────────────────────────────────────────────
# 2️⃣ AI CHAT DOCTOR SERVICE
# ─────────────────────────────────────────────────────────────────────────

class ChatDoctorService:
    """Service for AI-powered chat doctor."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ml_predictor = None  # Injected from ML module

    async def process_chat_message(
        self,
        user_id: str,
        message: str,
        language: str = "en",
        message_type: str = "text",
        transcription: Optional[str] = None,
    ) -> ChatSession:
        """Process chat message and generate response."""
        # 1. Retrieve user's health history
        health_history = await self._get_health_history(user_id)

        # 2. Analyze message (symptom extraction)
        symptoms = await self._extract_symptoms(message, language)

        # 3. Predict conditions using ML
        predictions = await self._predict_conditions(symptoms, health_history)

        # 4. Score risk level
        risk_level = await self._score_risk(predictions, health_history)

        # 5. Generate recommendations
        recommendations = await self._generate_recommendations(
            predictions, risk_level, health_history, language
        )

        # 6. Generate response text
        response_text = await self._generate_response_text(
            predictions, recommendations, language
        )

        # 7. Store chat session
        chat = ChatSession(
            user_id=user_id,
            message_text=message,
            message_type=message_type,
            transcription=transcription,
            response_text=response_text,
            predicted_conditions=json.dumps(
                [p.dict() for p in predictions]
            ),
            risk_level=risk_level,
            confidence_score=sum(p.confidence for p in predictions) / len(predictions)
            if predictions
            else 0.0,
            recommended_action=json.dumps(recommendations),
            nearby_doctors_needed=risk_level in ["high", "critical"],
            language=language,
        )
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)

        return chat

    async def _get_health_history(self, user_id: str) -> dict:
        """Get user's health history from last 2 months."""
        two_months_ago = datetime.utcnow() - timedelta(days=60)

        # Get recent reports
        reports = await self.db.execute(
            select(Report)
            .where(
                and_(
                    Report.user_id == user_id, Report.created_at >= two_months_ago
                )
            )
            .order_by(Report.created_at.desc())
        )
        reports_list = reports.scalars().all()

        # Get weekly follow-ups
        followups = await self.db.execute(
            select(WeeklyFollowUp)
            .where(
                and_(
                    WeeklyFollowUp.user_id == user_id,
                    WeeklyFollowUp.week_start >= two_months_ago,
                )
            )
            .order_by(WeeklyFollowUp.week_start.desc())
        )
        followups_list = followups.scalars().all()

        # Get health metrics
        metrics = await self.db.execute(
            select(HealthMetric)
            .where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.recorded_at >= two_months_ago,
                )
            )
            .order_by(HealthMetric.recorded_at.desc())
        )
        metrics_list = metrics.scalars().all()

        return {
            "reports": reports_list,
            "followups": followups_list,
            "metrics": metrics_list,
            "period_days": 60,
        }

    async def _extract_symptoms(self, message: str, language: str) -> list[str]:
        """Extract symptoms from user message using NLP."""
        # TODO: Implement NLP-based symptom extraction
        # For now, simple keyword matching
        symptoms_keywords = {
            "headache": ["headache", "head pain", "migraine"],
            "stomach_pain": ["stomach ache", "abdominal pain", "belly pain"],
            "fatigue": ["tired", "fatigue", "exhausted", "low energy"],
            "fever": ["fever", "temperature", "hot"],
            "cough": ["cough", "coughing"],
            "breathing_issue": ["shortness of breath", "difficulty breathing"],
            "chest_pain": ["chest pain", "chest discomfort"],
        }

        message_lower = message.lower()
        found_symptoms = []

        for symptom, keywords in symptoms_keywords.items():
            if any(kw in message_lower for kw in keywords):
                found_symptoms.append(symptom)

        return found_symptoms

    async def _predict_conditions(
        self, symptoms: list[str], health_history: dict
    ) -> list[dict]:
        """Predict possible health conditions."""
        # TODO: Implement ML-based prediction
        # For now, simple rule-based prediction
        predictions = []

        if "stomach_pain" in symptoms:
            predictions.append(
                {
                    "condition": "Gastritis",
                    "confidence": 0.7,
                    "severity": "medium",
                }
            )
            predictions.append(
                {
                    "condition": "Indigestion",
                    "confidence": 0.6,
                    "severity": "low",
                }
            )

        if "headache" in symptoms:
            predictions.append(
                {
                    "condition": "Migraine",
                    "confidence": 0.5,
                    "severity": "medium",
                }
            )

        return predictions

    async def _score_risk(self, predictions: list[dict], health_history: dict) -> str:
        """Score overall health risk level."""
        if not predictions:
            return "low"

        max_severity = max(p.get("severity", "low") for p in predictions)

        severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}

        if severity_scores.get(max_severity, 1) >= 3:
            return "high"
        elif severity_scores.get(max_severity, 1) >= 2:
            return "medium"
        else:
            return "low"

    async def _generate_recommendations(
        self,
        predictions: list[dict],
        risk_level: str,
        health_history: dict,
        language: str,
    ) -> list[str]:
        """Generate health recommendations."""
        recommendations = []

        if risk_level in ["high", "critical"]:
            recommendations.append("Consult with a doctor immediately")
            recommendations.append("Visit nearest hospital/clinic")

        if any(p["condition"] == "Gastritis" for p in predictions):
            recommendations.append("Avoid spicy and oily foods")
            recommendations.append("Drink plenty of water")

        return recommendations

    async def _generate_response_text(
        self, predictions: list[dict], recommendations: list[str], language: str
    ) -> str:
        """Generate response message."""
        # TODO: Implement proper response generation
        response = "Based on your symptoms and health history, "

        if predictions:
            conditions = ", ".join(p["condition"] for p in predictions)
            response += f"you may be experiencing {conditions}. "

        response += "Please follow the recommendations provided."

        return response


# ─────────────────────────────────────────────────────────────────────────
# 3️⃣ BOOKING SERVICE
# ─────────────────────────────────────────────────────────────────────────

class BookingService:
    """Service for managing lab bookings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_booking(
        self,
        user_id: str,
        lab_id: str,
        test_type: str,
        booking_type: str,  # home | lab_visit
        scheduled_date: datetime,
        address: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> LabBooking:
        """Create new booking."""
        booking = LabBooking(
            user_id=user_id,
            lab_id=lab_id,
            test_type=test_type,
            booking_type=booking_type,
            address=address,
            latitude=latitude,
            longitude=longitude,
            scheduled_date=scheduled_date,
            notes=notes,
            status="pending",
        )
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def get_user_bookings(self, user_id: str) -> list[LabBooking]:
        """Get user's bookings."""
        result = await self.db.execute(
            select(LabBooking)
            .where(LabBooking.user_id == user_id)
            .order_by(LabBooking.created_at.desc())
        )
        return result.scalars().all()

    async def cancel_booking(self, booking_id: str, user_id: str) -> bool:
        """Cancel booking."""
        result = await self.db.execute(
            select(LabBooking).where(
                and_(
                    LabBooking.id == booking_id,
                    LabBooking.user_id == user_id,
                )
            )
        )
        booking = result.scalar_one_or_none()

        if not booking:
            return False

        booking.status = "cancelled"
        await self.db.commit()
        return True


# ─────────────────────────────────────────────────────────────────────────
# 4️⃣ LOCATION SERVICE
# ─────────────────────────────────────────────────────────────────────────

class LocationService:
    """Service for finding nearby doctors/hospitals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_nearby_facilities(
        self,
        latitude: float,
        longitude: float,
        radius_km: int = 10,
        facility_type: Optional[str] = None,
        speciality: Optional[str] = None,
    ) -> list[dict]:
        """Find nearby medical facilities using geolocation."""
        # TODO: Implement proper geospatial query (PostGIS)
        # For now, simple distance calculation
        from math import radians, sin, cos, sqrt, atan2

        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth's radius in km
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = (
                sin(dlat / 2) ** 2
                + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            )
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        from visiondx.database.models import Facility

        query = select(Facility)
        if facility_type:
            query = query.where(Facility.facility_type == facility_type)

        result = await self.db.execute(query)
        facilities = result.scalars().all()

        # Calculate distances
        nearby = []
        for facility in facilities:
            distance = haversine_distance(
                latitude, longitude, facility.latitude, facility.longitude
            )
            if distance <= radius_km:
                nearby.append(
                    {
                        "id": facility.id,
                        "name": facility.name,
                        "distance_km": round(distance, 2),
                        "facility": facility,
                    }
                )

        # Sort by distance
        nearby.sort(key=lambda x: x["distance_km"])
        return nearby


# ─────────────────────────────────────────────────────────────────────────
# Abstract Service Factory
# ─────────────────────────────────────────────────────────────────────────

class ServiceContainer:
    """Service dependency container."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._services = {}

    def get_health_tracking_service(self) -> HealthTrackingService:
        """Get health tracking service instance."""
        if "health_tracking" not in self._services:
            self._services["health_tracking"] = HealthTrackingService(self.db)
        return self._services["health_tracking"]

    def get_chat_doctor_service(self) -> ChatDoctorService:
        """Get chat doctor service instance."""
        if "chat_doctor" not in self._services:
            self._services["chat_doctor"] = ChatDoctorService(self.db)
        return self._services["chat_doctor"]

    def get_booking_service(self) -> BookingService:
        """Get booking service instance."""
        if "booking" not in self._services:
            self._services["booking"] = BookingService(self.db)
        return self._services["booking"]

    def get_location_service(self) -> LocationService:
        """Get location service instance."""
        if "location" not in self._services:
            self._services["location"] = LocationService(self.db)
        return self._services["location"]
