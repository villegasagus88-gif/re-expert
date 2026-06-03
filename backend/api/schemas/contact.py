"""Pydantic schemas for Contacts API."""
from datetime import datetime
from uuid import UUID

from core.sanitize import SanitizedOptStr, SanitizedStr
from pydantic import BaseModel, Field


class CreateContactRequest(BaseModel):
    name: SanitizedStr = Field(..., min_length=1, max_length=200)
    phone: SanitizedOptStr = Field(None, max_length=32)
    email: SanitizedOptStr = Field(None, max_length=255)
    role: SanitizedOptStr = Field(None, max_length=80)
    notes: SanitizedOptStr = Field(None, max_length=2000)


class UpdateContactRequest(BaseModel):
    name: SanitizedOptStr = Field(None, min_length=1, max_length=200)
    phone: SanitizedOptStr = Field(None, max_length=32)
    email: SanitizedOptStr = Field(None, max_length=255)
    role: SanitizedOptStr = Field(None, max_length=80)
    notes: SanitizedOptStr = Field(None, max_length=2000)


class ContactOut(BaseModel):
    id: UUID
    name: str
    phone: str | None
    email: str | None
    telegram_chat_id: str | None
    role: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ContactListResponse(BaseModel):
    items: list[ContactOut]
    total: int
