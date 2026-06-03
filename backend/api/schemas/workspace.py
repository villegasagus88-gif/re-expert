"""
Workspace, memory and profile schemas (Capa 1B).
"""
from datetime import datetime
from typing import Literal

from core.sanitize import CleanText, SanitizedStr
from pydantic import BaseModel, Field

# ── Workspace ──

class WorkspaceCreate(BaseModel):
    name: SanitizedStr = Field(..., min_length=1, max_length=120)
    color: SanitizedStr | None = Field(default=None, max_length=7)
    description: CleanText | None = Field(default=None, max_length=2000)


class WorkspaceUpdate(BaseModel):
    name: SanitizedStr | None = Field(default=None, min_length=1, max_length=120)
    color: SanitizedStr | None = Field(default=None, max_length=7)
    description: CleanText | None = Field(default=None, max_length=2000)
    archived: bool | None = None


class WorkspaceOut(BaseModel):
    id: str
    name: str
    color: str | None = None
    description: str | None = None
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    # Conteo de conversaciones; lo seteamos a mano (no es ORM field).
    conversation_count: int = 0


# ── Workspace memory ──

MemoryScope = Literal["workspace", "global"]
MemorySource = Literal["manual", "auto-confirmed", "auto-silent"]
MemoryConfidence = Literal["high", "medium", "low"]


class MemoryItemCreate(BaseModel):
    key: SanitizedStr = Field(..., min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    value: CleanText = Field(..., min_length=1, max_length=1000)
    source: MemorySource = "manual"
    confidence: MemoryConfidence = "high"


class MemoryItemUpdate(BaseModel):
    value: CleanText | None = Field(default=None, min_length=1, max_length=1000)
    confidence: MemoryConfidence | None = None


class MemoryItemOut(BaseModel):
    id: str
    key: str
    value: str
    source: str
    confidence: str
    last_used_at: datetime | None = None
    confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MemoryListOut(BaseModel):
    items: list[MemoryItemOut]


# ── User profile global ──

class ProfileItemCreate(BaseModel):
    key: SanitizedStr = Field(..., min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    value: CleanText = Field(..., min_length=1, max_length=1000)
    source: MemorySource = "manual"
    confidence: MemoryConfidence = "high"
    sort_order: int = 0


class ProfileItemUpdate(BaseModel):
    value: CleanText | None = Field(default=None, min_length=1, max_length=1000)
    confidence: MemoryConfidence | None = None
    sort_order: int | None = None


class ProfileItemOut(BaseModel):
    id: str
    key: str
    value: str
    source: str
    confidence: str
    sort_order: int
    last_used_at: datetime | None = None
    confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProfileListOut(BaseModel):
    items: list[ProfileItemOut]
