"""
Perfil global del usuario (Capa 1B).

Memoria persistente scopeada al usuario que viaja a TODOS los chats — incluso
chats sueltos (sin workspace). Datos estables como rol, zonas en las que
opera, tipologías habituales, preferencias de formato.

- GET    /api/profile             → listar items
- POST   /api/profile             → crear/actualizar item (upsert por key)
- PATCH  /api/profile/{id}        → editar item
- DELETE /api/profile/{id}        → borrar item
"""
from datetime import UTC, datetime
from uuid import UUID

from api.schemas.workspace import (
    ProfileItemCreate,
    ProfileItemOut,
    ProfileItemUpdate,
    ProfileListOut,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from models.base import get_db
from models.user import User
from models.workspace import UserProfileGlobal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/profile", tags=["profile"])

# El perfil global viaja a TODOS los chats. Capamos para no inflar el system
# prompt sin control. 100 items son ~5-10kb de texto: suficiente para perfil
# de usuario típico.
MAX_PROFILE_ITEMS_PER_USER = 100


def _to_out(item: UserProfileGlobal) -> ProfileItemOut:
    return ProfileItemOut(
        id=str(item.id),
        key=item.key,
        value=item.value,
        source=item.source,
        confidence=item.confidence,
        sort_order=item.sort_order,
        last_used_at=item.last_used_at,
        confirmed_at=item.confirmed_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get(
    "",
    response_model=ProfileListOut,
    summary="Listar items del perfil global del usuario",
)
async def list_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfileGlobal)
        .where(UserProfileGlobal.user_id == current_user.id)
        .order_by(
            UserProfileGlobal.sort_order.asc(),
            UserProfileGlobal.created_at.asc(),
        )
    )
    items = list(result.scalars().all())
    return ProfileListOut(items=[_to_out(i) for i in items])


@router.post(
    "",
    response_model=ProfileItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear o actualizar item del perfil global (upsert por key)",
    responses={409: {"description": "Límite de items alcanzado"}},
)
async def upsert_profile_item(
    body: ProfileItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(UserProfileGlobal).where(
            UserProfileGlobal.user_id == current_user.id,
            UserProfileGlobal.key == body.key,
        )
    )
    item = existing.scalar_one_or_none()

    if item is None:
        count = await db.execute(
            select(func.count())
            .select_from(UserProfileGlobal)
            .where(UserProfileGlobal.user_id == current_user.id)
        )
        n = count.scalar() or 0
        if n >= MAX_PROFILE_ITEMS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Máximo {MAX_PROFILE_ITEMS_PER_USER} datos en el perfil global.",
            )
        item = UserProfileGlobal(
            user_id=current_user.id,
            key=body.key,
            value=body.value,
            source=body.source,
            confidence=body.confidence,
            sort_order=body.sort_order,
            confirmed_at=datetime.now(UTC),
        )
        db.add(item)
    else:
        item.value = body.value
        item.source = body.source
        item.confidence = body.confidence
        item.sort_order = body.sort_order
        item.confirmed_at = datetime.now(UTC)
        item.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(item)
    return _to_out(item)


@router.patch(
    "/{item_id}",
    response_model=ProfileItemOut,
    summary="Editar item del perfil global",
    responses={404: {"description": "Item no encontrado"}},
)
async def update_profile_item(
    item_id: UUID,
    body: ProfileItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(UserProfileGlobal, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item de perfil no encontrado"
        )
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    item.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(item)
    return _to_out(item)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar item del perfil global",
    responses={404: {"description": "Item no encontrado"}},
)
async def delete_profile_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(UserProfileGlobal, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item de perfil no encontrado"
        )
    await db.delete(item)
    await db.commit()
