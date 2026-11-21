"""Speech-to-Text (`gemini-3.5-transcribe`) and Text-to-Speech (`gemini-3.8-flash-tts`).

Uses the v1beta Interactions API client per docs/GEMINI4_BUILDER_GUIDE.pdf and official docs.
"""
from __future__ import annotations

import asyncio
import base64
import logging

import models
from shop import redact_sensitive

logger = logging.getLogger("shop_counter.speech")


def _transcribe_sync(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    beta_client = models.get_beta_client()
    b64_data = base64.b64encode(audio_bytes).decode("ascii")
    interaction = beta_client.interactions.create(
        model=models.TRANSCRIBE_MODEL,
        input=[
            {
                "type": "audio",
                "data": b64_data,
                "mime_type": mime_type or "audio/wav",
            }
        ],
    )
    return (interaction.output_text or "").strip()


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """Transcribe WAV/audio bytes to text with `gemini-3.5-transcribe`."""
    if not audio_bytes:
        return ""
    try:
        return await asyncio.to_thread(_transcribe_sync, audio_bytes, mime_type)
    except Exception as exc:
        logger.error("Transcribe error: %s", redact_sensitive(str(exc)))
        raise


def _tts_sync(text: str, voice: str = "Sulafat") -> tuple[str | None, str]:
    beta_client = models.get_beta_client()
    interaction = beta_client.interactions.create(
        model=models.TTS_MODEL,
        input=[
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "annotations": [
                            {
                                "type": "speech_metadata",
                                "style": "warm, concise, natural shop assistant",
                            }
                        ],
                    }
                ],
            }
        ],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": voice}]},
    )
    aud = interaction.output_audio
    if aud and getattr(aud, "data", None):
        return str(aud.data), str(getattr(aud, "mime_type", None) or "audio/wav")
    return None, "audio/wav"


async def synthesize_speech(text: str, voice: str = "Sulafat") -> dict[str, str | None]:
    """Synthesize spoken reply to WAV base64 with `gemini-3.8-flash-tts`."""
    if not text or not text.strip():
        return {"audio_b64": None, "mime_type": "audio/wav"}
    try:
        audio_b64, mime_type = await asyncio.to_thread(_tts_sync, text.strip(), voice)
        return {"audio_b64": audio_b64, "mime_type": mime_type}
    except Exception as exc:
        logger.warning("TTS synthesis warning: %s", redact_sensitive(str(exc)))
        return {"audio_b64": None, "mime_type": "audio/wav"}
