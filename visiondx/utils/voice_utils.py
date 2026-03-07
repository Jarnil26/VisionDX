"""
VisionDX — Voice (speech-to-text) support for Chat Doctor.

Supports multiple languages. Uses optional speech_recognition (or Whisper) when available.
"""
from __future__ import annotations

import io
from typing import Tuple


def transcribe_audio(audio_bytes: bytes, content_type: str, language: str | None = None) -> Tuple[str | None, str | None]:
    """
    Transcribe audio to text. Supports all languages via language hint.
    Returns (transcribed_text, error_message). If error_message is set, transcribed_text is None.
    """
    # Prefer speech_recognition (Google / Sphinx) if available
    try:
        import speech_recognition as sr
    except ImportError:
        return (
            None,
            "Voice support requires 'speech_recognition' (pip install SpeechRecognition). "
            "Alternatively use text input via POST /chat.",
        )

    recognizer = sr.Recognizer()
    # Map short codes to full locale for Google; supports all languages
    lang_code = (language or "en").strip().lower()
    if len(lang_code) == 2:
        locale_map = {"en": "en-US", "hi": "hi-IN", "es": "es-ES", "fr": "fr-FR", "ar": "ar-SA", "bn": "bn-IN", "ta": "ta-IN"}
        lang_code = locale_map.get(lang_code, f"{lang_code}-{lang_code.upper()}")

    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            data = recognizer.record(source)
    except Exception as e:
        return None, f"Could not read audio file: {e}"

    try:
        text = recognizer.recognize_google(data, language=lang_code)
        return (text.strip(), None)
    except sr.UnknownValueError:
        return None, "Could not understand audio. Please try again or use text input."
    except sr.RequestError as e:
        return None, f"Speech service error: {e}"
    except Exception as e:
        return None, str(e)
