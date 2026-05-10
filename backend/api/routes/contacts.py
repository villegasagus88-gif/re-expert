"""
Contacts CRUD — libreta de contactos del usuario.

Endpoints:
  GET    /api/contacts            ?q=carlos
  POST   /api/contacts
  PATCH  /api/contacts/{id}
  DELETE /api/contacts/{id}
"""
from uuid import UUID

from api.schemas.contact import (
    ContactListResponse,
    ContactOut,
    CreateContactRequest,
    UpdateContactRequest,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from models.base import get_db
from models.contact import Contact
from models.user import User
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


def _to_out(c: Contact) -> ContactOut:
    return ContactOut(
        id=c.id,
        name=c.name,
        phone=c.phone,
        email=c.email,
        telegram_chat_id=c.telegram_chat_id,
        role=c.role,
        notes=c.notes,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    q: str | None = Query(None, description="Búsqueda por nombre / teléfono / email"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    qry = select(Contact).where(Contact.user_id == current_user.id)
    if q:
        like = f"%{q.strip()}%"
        qry = qry.where(
            or_(
                Contact.name.ilike(like),
                Contact.phone.ilike(like),
                Contact.email.ilike(like),
            )
        )
    qry = qry.order_by(Contact.name.asc()).limit(500)
    rows = list((await db.execute(qry)).scalars().all())
    return ContactListResponse(items=[_to_out(c) for c in rows], total=len(rows))


@router.post("", response_model=ContactOut, status_code=201)
async def create_contact(
    body: CreateContactRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = Contact(
        user_id=current_user.id,
        name=body.name,
        phone=_normalize_phone(body.phone),
        email=body.email,
        role=body.role,
        notes=body.notes,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _to_out(c)


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: UUID,
    body: UpdateContactRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(Contact, contact_id)
    if not c or c.user_id != current_user.id:
        raise HTTPException(404, "Contacto no encontrado")
    if body.name is not None:
        c.name = body.name
    if body.phone is not None:
        c.phone = _normalize_phone(body.phone)
    if body.email is not None:
        c.email = body.email
    if body.role is not None:
        c.role = body.role
    if body.notes is not None:
        c.notes = body.notes
    await db.commit()
    await db.refresh(c)
    return _to_out(c)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(Contact, contact_id)
    if not c or c.user_id != current_user.id:
        raise HTTPException(404, "Contacto no encontrado")
    await db.delete(c)
    await db.commit()
    return None


# ─── Helpers ──────────────────────────────────────────────────────────
def _normalize_phone(phone: str | None) -> str | None:
    """Normaliza teléfono a formato internacional sin espacios.

    Acepta:
      "+5491155555555"  → "+5491155555555"
      "5491155555555"   → "+5491155555555"  (asume internacional sin +)
      "11 5555-5555"    → None  (ambiguo, dejamos pasar tal cual sin +)
                            → mejor: lo guarda como vino, el agente puede pedir aclaración.

    Se queda con dígitos + un único '+' inicial. Si no empieza con '+' y tiene
    >= 10 dígitos, le agrega '+'.
    """
    if not phone:
        return phone
    s = phone.strip()
    if not s:
        return None
    # Mantener solo dígitos y un '+' inicial
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return s  # devolver crudo, el agente verá que no es estándar
    if s.startswith("+"):
        return "+" + digits
    if len(digits) >= 10:
        return "+" + digits
    return digits
