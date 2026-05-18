"""
Chat request/response schemas.
"""
import base64
import binascii
from typing import Literal
from uuid import UUID

from core.sanitize import CleanText
from pydantic import BaseModel, Field, model_validator

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

# Primeros bytes característicos por formato. Verificamos contenido real
# para que un cliente malicioso no pueda mandar un binario arbitrario
# con un `media_type` falso.
_MAGIC_BYTES: dict[str, tuple[bytes, ...]] = {
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/gif": (b"GIF87a", b"GIF89a"),
    # WEBP layout: "RIFF" .... "WEBP" en bytes 0-3 y 8-11.
    "image/webp": (b"RIFF",),  # full check abajo
}


class ChatAttachment(BaseModel):
    """Imagen embebida en un mensaje del usuario (análisis de planos).

    `data` es el contenido base64 SIN el prefijo `data:image/...;base64,`.
    El frontend lo extrae con `dataURL.split(',')[1]` antes de enviar.

    Cap de 8 MB en base64 ≈ 6 MB binarios. La pared más dura es el
    Body Size middleware en main.py (10 MB para todo el request).

    Validación server-side de magic bytes: si el cliente declara
    `media_type=image/png` pero los bytes son otra cosa, rechazamos.
    Evita gastar tokens de Anthropic con basura y bloquea intentos de
    inyección via tipos de contenido arbitrarios.
    """

    type: Literal["image"] = "image"
    media_type: AttachmentMediaType
    data: str = Field(..., min_length=1, max_length=8_000_000)

    @model_validator(mode="after")
    def _check_magic_bytes(self) -> "ChatAttachment":
        try:
            raw = base64.b64decode(self.data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(
                "El contenido de la imagen no es base64 válido"
            ) from exc

        # Tope efectivo en binario (~6 MB). El cap a base64 es 8 MB,
        # pero post-decode debe seguir siendo razonable.
        if len(raw) > 6_500_000:
            raise ValueError(
                "La imagen es demasiado grande (máximo ~6 MB)"
            )
        if len(raw) < 32:
            raise ValueError("La imagen es demasiado chica para ser válida")

        prefixes = _MAGIC_BYTES.get(self.media_type, ())
        if not any(raw.startswith(p) for p in prefixes):
            raise ValueError(
                f"El contenido no coincide con {self.media_type}"
            )
        # Validación extra para WEBP: "RIFF" + 4 bytes + "WEBP".
        if self.media_type == "image/webp":
            if len(raw) < 12 or raw[8:12] != b"WEBP":
                raise ValueError("WEBP malformado")
        return self


class ChatRequest(BaseModel):
    message: CleanText = Field(..., min_length=1, max_length=10000)
    conversation_id: UUID | None = None
    context_type: ChatContextType = "chat"
    # Imágenes adjuntas (planos). Máximo 4 por request.
    attachments: list[ChatAttachment] = Field(default_factory=list, max_length=4)
