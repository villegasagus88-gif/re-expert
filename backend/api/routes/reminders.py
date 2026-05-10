"""
Reminders CRUD — para que el frontend muestre/edite recordatorios del usuario.

Endpoints:
  GET    /api/reminders            ?status=pending|sent|all
  POST   /api/reminders
  PATCH  /api/reminders/{id}       (cambia título/cuerpo/due_at/canal/cancela)
  DELETE /api/reminders/{id}       (cancela; preferimos soft delete)
"""
from datetime import datetime, timezone
from uuid import UUID

from api.schemas.reminder import (
    CreateReminderRequest,
    ReminderListResponse,
    ReminderOut,
    UpdateReminderRequest,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.base import get_db
from models.reminder import Reminder
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


def _to_out(r: Reminder) -> ReminderOut:
    return ReminderOut(
        id=r.id,
        title=r.title,
        body=r.body,
        due_at=r.due_at,
        channel=r.channel,
        status=r.status,
        meta=r.meta,
        last_error=r.last_error,
        sent_at=r.sent_at,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=ReminderListResponse)
async def list_reminders(
    status_filter: str = Query("pending", alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Reminder).where(Reminder.user_id == current_user.id)
    if status_filter != "all":
        q = q.where(Reminder.status == status_filter)
    q = q.order_by(Reminder.due_at.asc())
    rows = list((await db.execute(q)).scalars().all())
    return ReminderListResponse(items=[_to_out(r) for r in rows], total=len(rows))


@router.post("", response_model=ReminderOut, status_code=201)
async def create_reminder(
    body: CreateReminderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    due_at = body.due_at
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    if due_at <= datetime.now(timezone.utc):
        raise HTTPException(400, "due_at debe estar en el futuro")
    r = Reminder(
        user_id=current_user.id,
        title=body.title,
        body=body.body,
        due_at=due_at,
        channel=body.channel,
        meta=body.meta,
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return _to_out(r)


@router.patch("/{reminder_id}", response_model=ReminderOut)
async def update_reminder(
    reminder_id: UUID,
    body: UpdateReminderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.get(Reminder, reminder_id)
    if not r or r.user_id != current_user.id:
        raise HTTPException(404, "Recordatorio no encontrado")
    if body.title is not None:
        r.title = body.title
    if body.body is not None:
        r.body = body.body
    if body.due_at is not None:
        due_at = body.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        r.due_at = due_at
    if body.channel is not None:
        r.channel = body.channel
    if body.status is not None:
        if body.status not in ("pending", "cancelled"):
            raise HTTPException(400, "status sólo puede ser pending|cancelled aquí")
        r.status = body.status
    await db.commit()
    await db.refresh(r)
    return _to_out(r)


@router.delete("/{reminder_id}", status_code=204)
async def delete_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.get(Reminder, reminder_id)
    if not r or r.user_id != current_user.id:
        raise HTTPException(404, "Recordatorio no encontrado")
    if r.status == "pending":
        r.status = "cancelled"
        await db.commit()
    return None
