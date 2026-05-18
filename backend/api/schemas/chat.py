"""
Chat request/response schemas.
"""
from typing import Literal
from uuid import UUID

from core.sanitize import CleanText
from pydantic import BaseModel, Field

# Contextos soportados por /api/chat. Cada uno selecciona un system prompt
# distinto en el backend (ver services.anthropic_service.build_system_prompt).
ChatContextType = Literal["chat", "sol"]

# Media types soportados por Claude para análisis multimodal de imágenes.
# https://docs.anthropic.com/en/api/messages#image-content-blocks
AttachmentMediaType = Literal[
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
]


class ChatAttachment(BaseModel):
    """Imagen embebida en un mensaje del usuario (análisis de planos).

    `data` es el contenido base64 SIN el prefijo `data:image/...;base64,`.
    El frontend lo extrae con `dataURL.split(',')[1]` antes de enviar.

    Cap de 8 MB en base64 ≈ 6 MB binarios. La pared más dura es el
    Body Size middleware en main.py (10 MB para todo el request).
    """

    type: Literal["image"] = "image"
    media_type: AttachmentMediaType
    data: str = Field(..., min_length=1, max_length=8_000_000)


class ChatRequest(BaseModel):
    message: CleanText = Field(..., min_length=1, max_length=10000)
    conversation_id: UUID | None = None
    context_type: ChatContextType = "chat"
    # Imágenes adjuntas (planos). Máximo 4 por request.
    attachments: list[ChatAttachment] = Field(default_factory=list, max_length=4)
