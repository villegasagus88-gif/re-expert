"""
Chat request/response schemas.
"""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# Contextos soportados por /api/chat. Cada uno selecciona un system prompt
# distinto en el backend (ver services.anthropic_service.build_system_prompt).
ChatContextType = Literal["chat", "sol"]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: UUID | None = None
    context_type: ChatContextType = "chat"
