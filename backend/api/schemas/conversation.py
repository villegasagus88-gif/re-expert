"""
Conversation CRUD request/response schemas.
"""
from datetime import datetime

from core.sanitize import SanitizedStr
from pydantic import BaseModel, Field

# ── Requests ──

class CreateConversationRequest(BaseModel):
    title: SanitizedStr = Field(default="Nueva conversación", min_length=1, max_length=255)
    section: str = Field(default="general", max_length=50, pattern="^(general|sol)$")
    workspace_id: str | None = None


class UpdateConversationRequest(BaseModel):
    """Editar título o mover conversación entre workspaces.

    `workspace_id`:
      - string UUID  → mover al workspace indicado
      - cadena vacía "" o null → desasignar (queda como "chat suelto")
      - field ausente → no se modifica
    """
    title: SanitizedStr | None = Field(default=None, min_length=1, max_length=255)
    workspace_id: str | None = None


# ── Responses ──

class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    tokens_used: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    """Conversation summary (used in list view)."""
    id: str
    title: str
    section: str
    workspace_id: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_preview: str | None = None

    model_config = {"from_attributes": True}


class ConversationDetailOut(BaseModel):
    """Conversation with full message history."""
    id: str
    title: str
    section: str
    workspace_id: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}


class PaginatedConversations(BaseModel):
    items: list[ConversationOut]
    total: int
    page: int
    page_size: int
    total_pages: int
