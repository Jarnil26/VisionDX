"""
VisionDX — AI Chat Doctor Service

Aggregates user's past 2 months data (reports, weekly/monthly follow-ups),
analyzes symptom input with ML predictor, returns suggestions and optional emergency alert.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from visiondx.database.models import (
    AppUser,
    ChatMessage,
    ChatSession,
    MonthlyFollowUp,
    Report,
    WeeklyFollowUp,
)
from visiondx.database.schemas import ParsedParameter
from visiondx.ml.predictor import DiseasePredictor


# Keywords that may indicate emergency — trigger nearby facilities
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "stroke", "unconscious", "severe bleeding",
    "can't breathe", "suicide", "overdose", "severe allergic", "anaphylaxis",
    "seizure", "severe headache", "sudden weakness", "poisoning",
]


def _is_emergency_text(text: str) -> bool:
    t = text.lower().strip()
    return any(kw in t for kw in EMERGENCY_KEYWORDS)


async def get_or_create_session(
    app_user_id: str, session_id: str | None, db: AsyncSession
) -> ChatSession:
    if session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.app_user_id == app_user_id,
            )
        )
        session = result.scalar_one_or_none()
        if session:
            return session
    session = ChatSession(app_user_id=app_user_id)
    db.add(session)
    await db.flush()
    return session


async def aggregate_last_two_months(
    app_user_id: str, db: AsyncSession
) -> tuple[list[ParsedParameter], str]:
    """
    Aggregate parameters from reports and text summary from weekly/monthly follow-ups
    in the last 2 months. Returns (list of ParsedParameter for ML, summary string).
    """
    two_months_ago = datetime.now(timezone.utc) - timedelta(days=60)
    params: list[ParsedParameter] = []
    seen: set[tuple[str, float | None]] = set()

    # Reports in last 2 months
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.parameters))
        .where(
            Report.app_user_id == app_user_id,
            Report.created_at >= two_months_ago,
            Report.status == "done",
        )
        .order_by(Report.created_at.desc())
        .limit(20)
    )
    reports = result.scalars().all()
    for report in reports:
        for p in report.parameters:
            key = (p.name, p.value)
            if key in seen:
                continue
            seen.add(key)
            params.append(
                ParsedParameter(
                    name=p.name,
                    raw_name=p.raw_name,
                    value=p.value,
                    raw_value=p.raw_value,
                    unit=p.unit,
                    reference_range=p.reference_range,
                    status=p.status or "NORMAL",
                )
            )

    # Weekly & monthly summaries for context
    weekly_result = await db.execute(
        select(WeeklyFollowUp)
        .where(
            WeeklyFollowUp.app_user_id == app_user_id,
            WeeklyFollowUp.created_at >= two_months_ago,
        )
        .order_by(WeeklyFollowUp.week_start_date.desc())
        .limit(8)
    )
    monthly_result = await db.execute(
        select(MonthlyFollowUp)
        .where(
            MonthlyFollowUp.app_user_id == app_user_id,
            MonthlyFollowUp.month_start >= two_months_ago,
        )
        .order_by(MonthlyFollowUp.month_start.desc())
        .limit(2)
    )
    parts = []
    for w in weekly_result.scalars().all():
        if w.symptoms or w.notes:
            parts.append(f"Week: {w.symptoms or ''} {w.notes or ''}")
    for m in monthly_result.scalars().all():
        if m.summary or m.medical_alerts:
            parts.append(f"Month: {m.summary or ''} {m.medical_alerts or ''}")
    summary = " ".join(parts) if parts else ""
    return params, summary


def _build_suggestions(
    user_text: str,
    predictions: list[Any],
    emergency: bool,
) -> list[dict[str, Any]]:
    suggestions = []
    if predictions:
        suggestions.append({
            "type": "possible_conditions",
            "title": "Possible conditions (from your history)",
            "items": [{"condition": p.disease, "confidence": p.confidence} for p in predictions[:5]],
        })
    suggestions.append({
        "type": "recommendation",
        "title": "Recommendation",
        "text": (
            "If symptoms persist or worsen, please consult a doctor or book a lab test for a clearer picture."
            if not emergency else
            "This may require urgent care. Please visit the nearest emergency facility or call emergency services."
        ),
    })
    if emergency:
        suggestions.append({
            "type": "emergency",
            "title": "Emergency",
            "text": "We've included nearby facilities below. Please seek immediate medical attention if needed.",
        })
    return suggestions


# Map predicted conditions to medical specialty for relevant doctor/hospital suggestions
DISEASE_TO_SPECIALTY: dict[str, str] = {
    "diabetes": "Endocrinologist",
    "anemia": "General Physician / Hematologist",
    "thyroid": "Endocrinologist",
    "kidney": "Nephrologist",
    "liver": "Gastroenterologist / Hepatologist",
    "hyperlipidemia": "Cardiologist / General Physician",
    "infection": "Infectious Disease / General Physician",
    "allergy": "Allergist / Immunologist",
    "digestive": "Gastroenterologist",
    "stomach": "Gastroenterologist",
    "heart": "Cardiologist",
    "mental": "Psychiatrist / Psychologist",
    "depression": "Psychiatrist / Psychologist",
}


def _condition_to_specialty(condition: str) -> str:
    c = condition.lower()
    for key, specialty in DISEASE_TO_SPECIALTY.items():
        if key in c:
            return specialty
    return "General Physician"


def _get_nearby_facilities(
    limit: int = 5,
    emergency: bool = False,
    predicted_conditions: list[Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Return nearby facilities. If emergency=True, return emergency/hospitals.
    If predicted_conditions given, include specialty-relevant doctors (e.g. gastroenterologist for stomach).
    """
    base = [
        {"name": "City General Hospital", "type": "hospital", "address": "123 Medical Ave", "phone": "555-0100", "specialty": "Emergency"},
        {"name": "Urgent Care Center", "type": "clinic", "address": "456 Health St", "phone": "555-0101", "specialty": "Urgent Care"},
        {"name": "Emergency Room - Central", "type": "hospital", "address": "789 Emergency Blvd", "phone": "555-0102", "specialty": "Emergency"},
        {"name": "Digestive Health Clinic", "type": "clinic", "address": "100 Gastro St", "phone": "555-0200", "specialty": "Gastroenterologist"},
        {"name": "Cardiology Center", "type": "clinic", "address": "200 Heart Ave", "phone": "555-0201", "specialty": "Cardiologist"},
        {"name": "Mental Wellness Center", "type": "clinic", "address": "300 Mind Blvd", "phone": "555-0202", "specialty": "Psychiatrist"},
    ]
    if emergency:
        return [f for f in base if f.get("specialty") in ("Emergency", "Urgent Care")][:limit]
    if predicted_conditions:
        top = predicted_conditions[0] if predicted_conditions else None
        specialty = _condition_to_specialty(top.disease) if top else None
        if specialty:
            key = specialty.split("/")[0].strip().split(" ")[0]
            relevant = [f for f in base if key in (f.get("specialty") or "")]
            if relevant:
                return (relevant + [f for f in base if f not in relevant])[:limit]
    return base[:limit]


async def process_chat_message(
    app_user_id: str,
    message: str,
    session_id: str | None,
    db: AsyncSession,
    lang: str | None = None,
) -> tuple[str, str, list[dict], bool, list[dict]]:
    """
    Process user message: load history, run prediction, build reply.
    lang: optional language code for future i18n (e.g. en, hi, es). Reply is in English for now.
    Returns (reply_text, session_id, suggestions, emergency_alert, nearby_facilities).
    """
    session = await get_or_create_session(app_user_id, session_id, db)
    params, history_summary = await aggregate_last_two_months(app_user_id, db)

    emergency = _is_emergency_text(message)
    predictor = DiseasePredictor.get()
    predictions = predictor.predict(params) if params else []

    # Build a short reply (multilingual: lang can drive translation in future)
    if emergency:
        reply = (
            "Your message suggests you may be experiencing a serious situation. "
            "We strongly recommend seeking immediate medical attention. "
            "Please see the list of nearby facilities below or call emergency services."
        )
    elif predictions:
        top = predictions[0]
        reply = (
            f"Based on your recent health data and your message, one possibility that stands out is **{top.disease}** (confidence: {top.confidence:.0%}). "
            "This is not a diagnosis. We recommend discussing your symptoms and any recent lab results with a doctor. "
            "You may also consider a follow-up lab test if you haven't had one recently."
        )
    else:
        reply = (
            "Thank you for sharing. We don't have enough recent lab data to run a detailed analysis. "
            "Consider uploading a recent blood test report or completing your weekly follow-up to get more personalized insights. "
            "If you have specific symptoms, we recommend consulting a healthcare provider."
        )

    suggestions = _build_suggestions(message, predictions, emergency)
    # When emergency: show emergency facilities; when predictions (even non-emergency): show condition-relevant doctors
    show_facilities = emergency or (predictions and len(predictions) > 0)
    facilities = (
        _get_nearby_facilities(emergency=emergency, predicted_conditions=predictions if not emergency else None)
        if show_facilities
        else []
    )

    return reply, session.id, suggestions, emergency, facilities


async def save_chat_messages(
    session_id: str,
    user_content: str,
    assistant_content: str,
    suggestions: list[dict],
    emergency_alert: bool,
    db: AsyncSession,
) -> None:
    """Persist user and assistant messages."""
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=user_content,
    )
    db.add(user_msg)
    await db.flush()
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=assistant_content,
        suggestions=json.dumps(suggestions) if suggestions else None,
        emergency_alert=emergency_alert,
    )
    db.add(assistant_msg)
    await db.flush()
