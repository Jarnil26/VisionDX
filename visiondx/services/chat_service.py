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


from visiondx.ml.nlp_pipeline import prepare_text_for_ai, translate_from_english


# ---------------------------------------------------------------------------
# Symptom-Based Text Analyzer — works WITHOUT lab data
# ---------------------------------------------------------------------------
# Each entry: list of trigger keywords (ANY match), context keywords (bonus),
# condition name, advice text, and recommended specialty.
SYMPTOM_RULES: list[dict[str, Any]] = [
    {
        "triggers": ["back pain", "backpain", "lower back", "upper back", "spine pain", "spinal"],
        "context": ["sitting", "laptop", "desk", "chair", "hours", "work", "office", "computer", "bed", "posture"],
        "condition": "Postural / Ergonomic Back Pain",
        "advice": (
            "### 🧘 Symptom Analysis: Postural Back Pain\n"
            "Based on your description, this sounds like **postural back pain** — very common when sitting for long hours (10+ hours) on a chair or bed while working on a laptop.\n\n"
            "#### ⚡ Immediate Relief\n"
            "• **Move & Stretch:** Take a 5-minute break every 45 minutes — stand, stretch, and walk around.\n"
            "• **Heat Therapy:** Apply a hot compress or heating pad to the affected area for 15-20 minutes.\n"
            "• **Gentle Stretches:** Try the cat-cow pose, child's pose, or a seated spinal twist.\n\n"
            "#### 🛠️ Long-term Fixes\n"
            "• **Ergonomic Setup:** Use an ergonomic chair with proper lumbar support. Avoid working from your bed.\n"
            "• **Screen Height:** Keep your laptop screen at eye level using a stand or books.\n"
            "• **Core Strength:** Strengthen your core with planks (3-4 times/week) to support your spine.\n\n"
            "#### 👨‍⚕️ When to See a Doctor\n"
            "If pain persists beyond 2 weeks, radiates down your legs, or is accompanied by numbness, please consult an **Orthopedist** or **Physiotherapist**."
        ),
        "specialty": "Orthopedist / Physiotherapist",
    },
    {
        "triggers": ["headache", "head pain", "migraine", "head ache"],
        "context": ["screen", "laptop", "computer", "stress", "work", "hours", "sleep", "tension"],
        "condition": "Tension Headache / Screen Fatigue",
        "advice": (
            "### 🧠 Symptom Analysis: Tension Headache\n"
            "This sounds like a **tension headache**, likely caused by prolonged screen time, mental stress, or poor posture.\n\n"
            "#### ⚡ Quick Relief\n"
            "• **Digital Detox:** Take a 20-minute break from all screens — close your eyes and breathe deeply.\n"
            "• **Hydration:** Drink a glass of water immediately; dehydration is a common headache trigger.\n"
            "• **Pressure Points:** Gently massage your temples and the base of your neck.\n\n"
            "#### 🛠️ Prevention\n"
            "• **20-20-20 Rule:** Every 20 mins, look at something 20 feet away for 20 seconds.\n"
            "• **Sleep Hygiene:** Ensure 7-8 hours of quality sleep to let your brain recover.\n"
            "• **Brightness:** Reduce screen brightness and enable 'Night Shift' or blue-light filters.\n\n"
            "#### 👨‍⚕️ When to See a Doctor\n"
            "If headaches are severe, frequent, or accompanied by vomiting or vision changes, consult a **Neurologist**."
        ),
        "specialty": "Neurologist / General Physician",
    },
    {
        "triggers": ["eye strain", "eye pain", "blurry vision", "dry eyes", "eyes burning", "eyes tired", "eyes hurt"],
        "context": ["screen", "laptop", "computer", "phone", "hours", "work"],
        "condition": "Digital Eye Strain",
        "advice": (
            "### 👁️ Symptom Analysis: Digital Eye Strain\n"
            "You're likely experiencing **Digital Eye Strain** (Computer Vision Syndrome) from prolonged screen use.\n\n"
            "#### ⚡ Immediate Steps\n"
            "• **The 20-20-20 Rule:** Every 20 mins, look 20 feet away for 20 seconds to relax eye muscles.\n"
            "• **Lubrication:** Use preservative-free artificial tears if your eyes feel 'gritty' or dry.\n"
            "• **Blink More:** We blink 60% less when staring at screens. Catch yourself and blink often!\n\n"
            "#### 🛠️ Prevention\n"
            "• **Monitor Position:** Adjust your screen so the top is at eye level, roughly 25 inches away.\n"
            "• **Anti-Glare:** Use a matte screen filter or adjust lighting to reduce glare.\n\n"
            "#### 👨‍⚕️ When to See a Doctor\n"
            "If you experience persistent blurry vision or eye pain despite rest, consult an **Ophthalmologist**."
        ),
        "specialty": "Ophthalmologist",
    },
    {
        "triggers": ["neck pain", "stiff neck", "neck stiffness", "neck ache"],
        "context": ["laptop", "phone", "screen", "desk", "pillow", "sleep", "posture"],
        "condition": "Tech Neck / Cervical Strain",
        "advice": (
            "### 🦒 Symptom Analysis: Tech Neck\n"
            "This appears to be **cervical strain** (often called 'tech neck'), common from looking down at phones or laptops.\n\n"
            "#### ⚡ Relief\n"
            "• **Chin Tuck:** Gently pull your chin straight back (like making a double chin) to reset posture.\n"
            "• **Heat Therapy:** Apply warmth to the back of your neck for 15 minutes.\n"
            "• **Shoulder Rolls:** Roll your shoulders back and down 10 times.\n\n"
            "#### 🛠️ Prevention\n"
            "• **Eye Level:** Always bring your phone/screen up to eye level instead of tilting your head down.\n"
            "• **Pillow Check:** Ensure your pillow maintains the natural curve of your neck.\n\n"
            "#### 👨‍⚕️ When to See a Doctor\n"
            "If pain radiates into your arms or causes weakness in your hands, consult an **Orthopedist**."
        ),
        "specialty": "Orthopedist",
    },
    {
        "triggers": ["tired", "fatigue", "exhausted", "no energy", "always sleepy", "weakness", "lethargic"],
        "context": ["work", "stress", "sleep", "hours", "diet", "eating"],
        "condition": "Lifestyle Fatigue",
        "advice": (
            "### 🔋 Symptom Analysis: Lifestyle Fatigue\n"
            "Your symptoms suggest **fatigue**, likely caused by overwork, high stress levels, or nutritional gaps.\n\n"
            "#### ⚡ Immediate Actions\n"
            "• **Quick Walk:** 10 minutes of walking in natural light can boost cortisol and alertness.\n"
            "• **Nap Wisely:** A 20-minute power nap can reset your focus without causing grogginess.\n"
            "• **Magnesium/Iron:** Ensure you're eating greens, nuts, and seeds.\n\n"
            "#### 🛠️ Long-term Strategy\n"
            "• **Consistent Schedule:** Go to bed and wake up at the same time every day.\n"
            "• **Limit Caffeine:** Avoid caffeine after 2:00 PM to improve deep sleep quality.\n\n"
            "**Note:** If fatigue lasts >2 weeks, it could be Anemia or Vitamin D deficiency. **Uploading a blood report** would help me analyze this better."
        ),
        "specialty": "General Physician",
    },
    {
        "triggers": ["stomach pain", "stomach ache", "abdominal pain", "acidity", "gas", "bloating", "indigestion", "nausea"],
        "context": ["food", "eating", "spicy", "stress", "meal", "dinner", "lunch"],
        "condition": "Gastric Distress",
        "advice": (
            "### 🤢 Symptom Analysis: Gastric Distress\n"
            "Based on your symptoms, this could be **acidity, indigestion, or bloating**.\n\n"
            "#### ⚡ Quick Relief\n"
            "• **Herbal Aid:** Drink lukewarm water with carom seeds (ajwain) or ginger tea.\n"
            "• **Posture:** Walk slowly for 10 minutes; do not lie down for at least 2 hours after a meal.\n"
            "• **Small Sips:** Stay hydrated with small sips of water throughout the hour.\n\n"
            "#### 🛠️ Prevention\n"
            "• **Mindful Eating:** Chew your food at least 20 times per bite to aid digestion.\n"
            "• **Avoid Triggers:** Limit oily, spicy, and highly processed foods for a few days.\n\n"
            "#### 👨‍⚕️ When to See a Doctor\n"
            "If pain is sharp, located in the lower right, or accompanied by fever, consult a **Gastroenterologist** immediately."
        ),
        "specialty": "Gastroenterologist",
    },
    {
        "triggers": ["stress", "anxiety", "worried", "nervous", "panic", "overwhelmed", "can't sleep", "insomnia", "depressed", "sad"],
        "context": ["work", "pressure", "deadline", "family", "money", "exam"],
        "condition": "Stress & Anxiety",
        "advice": (
            "### 🧘‍♀️ Symptom Analysis: Stress / Anxiety\n"
            "It sounds like you're dealing with **stress or anxiety**, which can significantly affect your physical health.\n\n"
            "#### ⚡ Calming Techniques\n"
            "• **4-7-8 Breathing:** Inhale for 4s, hold for 7s, exhale for 8s. Repeat 4 times.\n"
            "• **Grounding:** Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, and 1 you taste.\n\n"
            "#### 🛠️ Management\n"
            "• **Journaling:** Write down your worries before bed to 'empty' your mind.\n"
            "• **Limit News:** Reduce consumption of stressful media or social feeds.\n\n"
            "**Remember:** There is no shame in seeking help. If this persists, a **Psychologist** can provide vital tools for recovery."
        ),
        "specialty": "Psychologist / Psychiatrist",
    },
    {
        "triggers": ["fever", "temperature", "chills", "shivering", "cold", "flu", "cough", "sore throat", "runny nose", "sneezing"],
        "context": ["days", "weather", "rain", "season"],
        "condition": "Viral Syndrome (Common Cold)",
        "advice": (
            "### 🤒 Symptom Analysis: Viral Syndrome\n"
            "Your symptoms suggest a **common cold or mild viral infection**.\n\n"
            "#### ⚡ Home Care\n"
            "• **Gargle:** Warm salt water gargles 3 times a day for your throat.\n"
            "• **Steam:** Use a steamer or a bowl of hot water for 5-10 mins to clear congestion.\n"
            "• **Fluids:** Drink at least 3 liters of water/liquids (soups, herbal tea).\n\n"
            "#### 🛠️ Recovery\n"
            "• **Complete Rest:** Your body heals fastest when you are asleep.\n"
            "• **Vitamin C:** Eat citrus fruits or take a supplement to support your immune system.\n\n"
            "#### 👨‍⚕️ When to See a Doctor\n"
            "If your fever is >102°F or you have difficulty breathing, consult a **General Physician**."
        ),
        "specialty": "General Physician",
    },
    {
        "triggers": ["wrist pain", "carpal tunnel", "hand pain", "finger pain", "typing pain"],
        "context": ["laptop", "typing", "mouse", "keyboard", "work", "computer", "hours"],
        "condition": "Repetitive Strain (RSI)",
        "advice": (
            "### ⌨️ Symptom Analysis: Repetitive Strain\n"
            "This sounds like **RSI (Repetitive Strain Injury)**, common from excessive typing or mouse use.\n\n"
            "#### ⚡ Relief\n"
            "• **Shake it Out:** Gently shake your hands and rotate your wrists every 30 minutes.\n"
            "• **Icing:** Apply ice to the wrist for 10 minutes if there is noticeable heat or swelling.\n"
            "• **Rest:** Avoid heavy lifting or excessive typing for the next 24 hours.\n\n"
            "#### 🛠️ Ergonomics\n"
            "• **Neutral Wrist:** Ensure your wrist stays straight, not tilted up or down, while typing.\n"
            "• **Soft Touch:** Try to type with a lighter touch; don't 'bang' the keys.\n\n"
            "#### 👨‍⚕️ When to See a Doctor\n"
            "If you feel constant numbness or 'pins and needles' in your thumb or fingers, consult an **Orthopedist**."
        ),
        "specialty": "Orthopedist",
    },
]


def _analyze_symptoms_from_text(text: str) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    """
    Analyze the user's message for common symptom patterns.
    Returns (condition_name, advice_text, symptom_suggestions) or (None, None, []) if no match.
    """
    t = text.lower()
    best_match = None
    best_score = 0

    for rule in SYMPTOM_RULES:
        # Count how many trigger keywords match
        trigger_hits = sum(1 for kw in rule["triggers"] if kw in t)
        if trigger_hits == 0:
            continue

        # Count context keyword matches for better ranking
        context_hits = sum(1 for kw in rule["context"] if kw in t)
        score = trigger_hits * 3 + context_hits  # Triggers weigh more

        if score > best_score:
            best_score = score
            best_match = rule

    if best_match is None:
        return None, None, []

    suggestions = [
        {
            "type": "symptom_analysis",
            "title": f"Detected: {best_match['condition']}",
            "text": f"Based on your description, this may be related to {best_match['condition']}.",
        },
        {
            "type": "recommendation",
            "title": "Recommended Specialist",
            "text": f"If symptoms persist, consider consulting a {best_match['specialty']}.",
        },
    ]

    return best_match["condition"], best_match["advice"], suggestions


async def process_chat_message(
    app_user_id: str,
    message: str,
    session_id: str | None,
    db: AsyncSession,
    lang: str | None = None,
) -> tuple[str, str, list[dict], bool, list[dict]]:
    """
    Process user message: NLP translation pipeline, run prediction, build reply.
    lang: optional language code. If not provided, it is auto-detected.
    Returns (reply_text, session_id, suggestions, emergency_alert, nearby_facilities).
    """
    session = await get_or_create_session(app_user_id, session_id, db)
    params, history_summary = await aggregate_last_two_months(app_user_id, db)

    # 1. NLP Pipeline: Detect language, correct spelling, translate to English for the Model
    english_text, detected_lang = prepare_text_for_ai(message)
    user_lang = lang or detected_lang

    emergency = _is_emergency_text(english_text)
    predictor = DiseasePredictor.get()
    predictions = predictor.predict(params) if params else []

    # 2. Symptom-based text analysis (works even without lab data)
    symptom_condition, symptom_advice, symptom_suggestions = _analyze_symptoms_from_text(english_text)

    # Build a short reply in English natively
    if emergency:
        reply_en = (
            "Your message suggests you may be experiencing a serious situation. "
            "We strongly recommend seeking immediate medical attention. "
            "Please see the list of nearby facilities below or call emergency services."
        )
        suggestions = _build_suggestions(english_text, predictions, emergency)
    elif predictions:
        top = predictions[0]
        reply_en = (
            f"Based on your recent health data and symptoms, one possibility that stands out is **{top.disease}** (confidence: {top.confidence:.0%}). "
            "This is not a diagnosis. We recommend discussing your symptoms and any recent lab results with a doctor. "
            "You may also consider a follow-up lab test if you haven't had one recently."
        )
        # If we also detected symptoms from text, append the practical advice
        if symptom_advice:
            reply_en += f"\n\n---\n\n**Regarding your symptoms — {symptom_condition}:**\n\n{symptom_advice}"
        suggestions = _build_suggestions(english_text, predictions, emergency)
    elif symptom_condition and symptom_advice:
        # No lab data but we detected symptoms from the text — give practical advice!
        reply_en = f"**{symptom_condition}**\n\n{symptom_advice}"
        suggestions = symptom_suggestions
    else:
        reply_en = (
            "Thank you for sharing. I'd like to help you better! "
            "Could you describe your symptoms in more detail? For example:\n\n"
            "• Where exactly do you feel discomfort?\n"
            "• How long have you been experiencing this?\n"
            "• Is the pain constant or does it come and go?\n\n"
            "You can also upload a recent blood test report for a more personalized analysis."
        )
        suggestions = _build_suggestions(english_text, predictions, emergency)

    # Translate english reply back to the user's original language
    reply = translate_from_english(reply_en, user_lang)

    # Translate suggestion texts back to the user's language
    for sugg in suggestions:
        if "title" in sugg:
            sugg["title"] = translate_from_english(sugg["title"], user_lang)
        if "text" in sugg:
            sugg["text"] = translate_from_english(sugg["text"], user_lang)

    # When emergency: show emergency facilities; when predictions or symptom match: show relevant doctors
    show_facilities = emergency or (predictions and len(predictions) > 0) or (symptom_condition is not None)
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
