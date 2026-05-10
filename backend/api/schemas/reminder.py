"""Pydantic schemas for the Reminders API."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ReminderChannel = Literal["in_app", "email", "telegram", "whatsapp", "push"]
ReminderStatus = Literal["pending", "sent", "failed", "cancelled"]


class CreateReminderRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    body: str | None = Field(None, max_length=4000)
    due_at: datetime
    channel: ReminderChannel = "in_app"
    meta: dict | None = None


class UpdateReminderRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    body: str | None = Field(None, max_length=4000)
    due_at: datetime | None = None
    channel: ReminderChannel | None = None
    status: Literal["pending", "cancelled"] | None = None


class ReminderOut(BaseModel):
    id: UUID
    title: str
    body: str | None
    due_at: datetime
    channel: ReminderChannel
    status: ReminderStatus
    meta: dict | None
    last_error: str | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReminderListResponse(BaseModel):
    items: list[ReminderOut]
    total: int
