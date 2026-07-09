"""
Voice Service — oído y voz premium del Chat Experto (OpenAI STT + TTS).

Arquitectura elegida: el navegador graba audio crudo (MediaRecorder, permiso
estándar de micrófono), el backend lo transcribe (STT) y sintetiza las
respuestas (TTS). El CEREBRO sigue siendo el Chat Experto de siempre: acá
solo se convierte audio↔texto, nunca se genera contenido.

Sin SDK nuevo: llamadas directas a la API de OpenAI con httpx (ya en
requirements). Si OPENAI_API_KEY está vacía, is_enabled() da False y el
frontend cae automáticamente a las APIs nativas del navegador.

Costos de referencia (para el tope de gasto del dashboard de OpenAI):
STT ≈ US$0,003/min hablado · TTS ≈ US$0,015/min de audio.
"""
from __future__ import annotations

import logging

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

_OPENAI_BASE = "https://api.openai.com/v1"
_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

MAX_TTS_CHARS = 4000  # límite de input del endpoint de speech de OpenAI


def is_enabled() -> bool:
    return bool(settings.OPENAI_API_KEY)


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}


async def transcribe(audio: bytes, filename: str, content_type: str) -> str:
    """Audio → texto (español). Lanza RuntimeError con mensaje claro si falla."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_OPENAI_BASE}/audio/transcriptions",
            headers=_headers(),
            files={"file": (filename, audio, content_type or "audio/webm")},
            data={
                "model": settings.OPENAI_STT_MODEL,
                "language": "es",
                "response_format": "json",
            },
        )
    if resp.status_code != 200:
        logger.warning("Voice STT %s: %s", resp.status_code, resp.text[:300])
        raise RuntimeError("La transcripción falló. Probá de nuevo en unos segundos.")
    return (resp.json().get("text") or "").strip()


async def speak(text: str) -> bytes:
    """Texto → audio MP3. El texto ya viene limpio (sin markdown) del frontend."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_OPENAI_BASE}/audio/speech",
            headers=_headers(),
            json={
                "model": settings.OPENAI_TTS_MODEL,
                "voice": settings.OPENAI_TTS_VOICE,
                "input": text[:MAX_TTS_CHARS],
                "response_format": "mp3",
            },
        )
    if resp.status_code != 200:
        logger.warning("Voice TTS %s: %s", resp.status_code, resp.text[:300])
        raise RuntimeError("La síntesis de voz falló. Probá de nuevo en unos segundos.")
    return resp.content
