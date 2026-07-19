"""
Voz del Chat Experto — endpoints de STT y TTS.

  GET  /api/voice/status      → {enabled} (¿hay OPENAI_API_KEY? el frontend
                                decide voz premium vs voz del navegador)
  POST /api/voice/transcribe  → multipart audio → {text}
  POST /api/voice/speak       → {text} → audio/mpeg

El contenido conversacional NUNCA pasa por acá: el texto transcripto entra
por el mismo /api/chat de siempre desde el frontend.
"""
import logging

from core.auth import get_current_user
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from models.user import User
from pydantic import BaseModel, Field
from services import voice_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

MAX_AUDIO_BYTES = 8 * 1024 * 1024  # el body global capea en 10 MB
_ALLOWED_AUDIO = ("audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/wav", "video/webm", "video/mp4")


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class SpeakScriptRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)


class WebSearchRequest(BaseModel):
    consulta: str = Field(min_length=2, max_length=300)


class RealtimeSessionRequest(BaseModel):
    # Memoria compacta del usuario (la maneja el frontend, viaja como contexto)
    user_context: str = Field(default="", max_length=1500)


@router.get("/status", summary="¿Está habilitada la voz premium?")
async def voice_status(_user: User = Depends(get_current_user)):
    enabled = voice_service.is_enabled()
    return {"enabled": enabled, "realtime": enabled}


@router.post("/realtime-session", summary="Clave efímera para la conversación en vivo (WebRTC)")
async def realtime_session(body: RealtimeSessionRequest,
                           _user: User = Depends(get_current_user)):
    if not voice_service.is_enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Voz premium no configurada")
    try:
        return await voice_service.create_realtime_session(body.user_context)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Voice: realtime-session falló")
        raise HTTPException(status_code=502, detail="No se pudo iniciar la sesión de voz") from exc


@router.post("/speak-script", summary="Respuesta escrita → guion natural para leer en voz alta")
async def speak_script(body: SpeakScriptRequest, _user: User = Depends(get_current_user)):
    try:
        return {"script": await voice_service.spoken_script(body.text)}
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Voice: speak-script falló")
        raise HTTPException(status_code=502, detail="No se pudo preparar la lectura") from exc


@router.post("/web-search", summary="Búsqueda web en vivo para el asesor de voz")
async def voice_web_search(body: WebSearchRequest, _user: User = Depends(get_current_user)):
    try:
        return await voice_service.web_search(body.consulta)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Voice: web_search falló")
        raise HTTPException(status_code=502, detail="La búsqueda falló") from exc


@router.post("/transcribe", summary="Audio → texto (voz del usuario)")
async def transcribe(audio: UploadFile = File(...), _user: User = Depends(get_current_user)):
    if not voice_service.is_enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Voz premium no configurada")
    ctype = (audio.content_type or "").split(";")[0].strip().lower()
    if ctype and ctype not in _ALLOWED_AUDIO:
        raise HTTPException(status_code=422, detail=f"Formato de audio no soportado: {ctype}")
    data = await audio.read()
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="El audio supera el máximo de 8 MB")
    if len(data) < 500:
        raise HTTPException(status_code=422, detail="Audio vacío o demasiado corto")
    try:
        text = await voice_service.transcribe(data, audio.filename or "audio.webm", ctype)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Voice: transcribe falló")
        raise HTTPException(status_code=502, detail="La transcripción falló") from exc
    return {"text": text}


@router.post("/speak", summary="Texto → voz (respuesta del experto)")
async def speak(body: SpeakRequest, _user: User = Depends(get_current_user)):
    if not voice_service.is_enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Voz premium no configurada")
    try:
        audio = await voice_service.speak(body.text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Voice: speak falló")
        raise HTTPException(status_code=502, detail="La síntesis de voz falló") from exc
    return Response(content=audio, media_type="audio/mpeg",
                    headers={"Cache-Control": "no-store"})
