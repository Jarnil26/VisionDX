"""
VisionDX — AI Chat Doctor Routes

POST /chat       — Send text message; get AI reply, suggestions, emergency + nearby facilities.
POST /chat/voice — Send audio; transcribe (all languages) → same ML flow as /chat.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status

from visiondx.database.connection import get_db
from visiondx.database.models import AppUser
from visiondx.database.schemas import ChatMessageIn, ChatResponse
from visiondx.api.routes.users import get_current_app_user
from visiondx.services import chat_service
from visiondx.utils.voice_utils import transcribe_audio
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/chat", tags=["AI Chat Doctor"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatMessageIn,
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
    accept_language: str | None = Header(None, alias="Accept-Language"),
):
    """
    AI Chat Doctor: send your symptoms as **text**.
    Uses your past 2 months of reports and follow-ups for predictive analysis.
    Returns suggestions; on critical patterns: emergency_alert + nearby_facilities (by condition when relevant).
    **Multilingual**: Use body.lang or Accept-Language for response language (e.g. en, hi, es).
    """
    lang = body.lang or (accept_language.split(",")[0].strip()[:5] if accept_language else None)
    reply, session_id, suggestions, emergency_alert, nearby_facilities = (
        await chat_service.process_chat_message(
            current_user.id, body.message, body.session_id, db, lang=lang
        )
    )
    await chat_service.save_chat_messages(
        session_id, body.message, reply, suggestions, emergency_alert, db
    )
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        suggestions=suggestions,
        emergency_alert=emergency_alert,
        nearby_facilities=nearby_facilities,
    )


@router.post("/voice", response_model=ChatResponse)
async def chat_voice(
    audio: UploadFile = File(..., description="Audio file (WAV preferred; or MP3)"),
    session_id: str | None = Form(None),
    lang: str | None = Form(None),
    _lang_header: str | None = Header(None, alias="X-Lang"),
    current_user: AppUser = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI Chat Doctor: send your symptoms by **voice** (speech-to-text).
    Audio is transcribed (supports **all languages** via lang form or X-Lang header, e.g. en, hi, es),
    then the same ML flow as POST /chat runs. Returns reply, suggestions, emergency + nearby facilities.
    """
    content_type = audio.content_type or ""
    if not content_type.startswith("audio/") and not (audio.filename or "").lower().endswith((".wav", ".mp3", ".webm", ".ogg")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload an audio file (e.g. WAV, MP3).",
        )
    audio_bytes = await audio.read()
    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Audio file too short.")
    language = lang or _lang_header
    text, err = transcribe_audio(audio_bytes, content_type, language=language)
    if err is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    reply, sid, suggestions, emergency_alert, nearby_facilities = (
        await chat_service.process_chat_message(
            current_user.id, text, session_id, db, lang=language
        )
    )
    await chat_service.save_chat_messages(
        sid, text, reply, suggestions, emergency_alert, db
    )
    return ChatResponse(
        session_id=sid,
        reply=reply,
        suggestions=suggestions,
        emergency_alert=emergency_alert,
        nearby_facilities=nearby_facilities,
    )
