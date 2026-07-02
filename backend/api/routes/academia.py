"""
Academia endpoints.

Sirve cursos y rutas de aprendizaje desde JSONs en `backend/data/academia/`.
Mismo patrón que `materials.py`: data curada (low-churn) en archivos
versionados, leídos on-demand con cache en memoria.

Endpoints:
  GET /api/academia/courses → catálogo de cursos agrupados por categoría
  GET /api/academia/paths   → rutas de aprendizaje (caminos progresivos)
"""
import json
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from api.schemas.academia import (
    CartCheckoutRequest,
    CartCheckoutResponse,
    CourseCheckoutRequest,
    CourseCheckoutResponse,
    CourseDemand,
    CoursesResponse,
    DemandResponse,
    MyCoursesResponse,
    OwnedCourse,
    PathsResponse,
    RecordInterestRequest,
    TopicDemand,
)
from core.auth import get_current_user, require_admin
from fastapi import APIRouter, Depends, HTTPException, status
from models.academia import AcademiaInterest
from models.base import get_db
from models.course_purchase import CoursePurchase
from models.user import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/academia", tags=["academia"])

# Misma estructura que materials.py: el data vive dentro del backend
# para que viaje con el Docker image. Si en el futuro queremos editar
# sin redeploy, migrar al bucket de Supabase Storage.
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "academia"
_COURSES_PATH = _DATA_DIR / "cursos.json"
_PATHS_PATH = _DATA_DIR / "rutas.json"


@lru_cache(maxsize=2)
def _load_json(path: str) -> dict:
    """Cache en memoria — el contenido es estático, no cambia entre requests."""
    p = Path(path)
    if not p.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Archivo de academia no disponible: {p.name}",
        )
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/courses",
    response_model=CoursesResponse,
    summary="Catálogo de cursos curados",
    responses={
        401: {"description": "Token inválido o ausente"},
        503: {"description": "Archivo de cursos no disponible"},
    },
)
async def get_courses(_user: User = Depends(get_current_user)) -> CoursesResponse:
    data = _load_json(str(_COURSES_PATH))
    return CoursesResponse(**data)


@router.get(
    "/paths",
    response_model=PathsResponse,
    summary="Rutas de aprendizaje progresivas",
    responses={
        401: {"description": "Token inválido o ausente"},
        503: {"description": "Archivo de rutas no disponible"},
    },
)
async def get_paths(_user: User = Depends(get_current_user)) -> PathsResponse:
    data = _load_json(str(_PATHS_PATH))
    return PathsResponse(**data)


def _find_course(course_id: str) -> dict | None:
    """Busca un curso por id en el catálogo (categories[].courses[]). El precio y
    el is_free SIEMPRE se leen del catálogo del backend, nunca del cliente."""
    data = _load_json(str(_COURSES_PATH))
    for cat in data.get("categories", []):
        for c in cat.get("courses", []):
            if c.get("id") == course_id:
                return c
    return None


# ── Compra de cursos (Checkout Pro de Mercado Pago) ──

@router.post(
    "/checkout",
    response_model=CourseCheckoutResponse,
    summary="Comprar un curso (o inscribirse si es gratis)",
    responses={
        401: {"description": "Token inválido o ausente"},
        404: {"description": "Curso no encontrado"},
        409: {"description": "Ya tenés el curso"},
        422: {"description": "Curso pago sin precio configurado en el catálogo"},
        503: {"description": "Mercado Pago no configurado"},
    },
)
async def checkout_course(
    body: CourseCheckoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CourseCheckoutResponse:
    course = _find_course(body.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    # ¿Ya lo tiene? (approved o free) → no re-comprar.
    owned = (await db.execute(
        select(CoursePurchase).where(
            CoursePurchase.user_id == user.id,
            CoursePurchase.course_id == body.course_id,
            CoursePurchase.status.in_(("approved", "free")),
        )
    )).scalar_one_or_none()
    if owned:
        raise HTTPException(status_code=409, detail="Ya tenés acceso a este curso.")

    title = str(course.get("title", ""))[:255]

    # Curso GRATIS → inscripción directa, sin MP.
    if course.get("is_free"):
        db.add(CoursePurchase(
            user_id=user.id, course_id=body.course_id, course_title=title,
            price_ars=0, status="free",
        ))
        try:
            await db.commit()
        except IntegrityError:
            # Race (doble click): otro request ya lo inscribió — mismo resultado.
            await db.rollback()
        return CourseCheckoutResponse(kind="enrolled", course_id=body.course_id, status="free")

    price = int(course.get("price_ars") or 0)
    if price <= 0:
        # 422 (no 409): el 409 significa "ya lo tenés"; esto es data del catálogo.
        raise HTTPException(
            status_code=422, detail="Este curso no tiene precio configurado."
        )

    # Reusar la compra pendiente si ya hay una (reintento de pago): evita
    # acumular N filas pending + N preferences del mismo curso.
    purchase = (await db.execute(
        select(CoursePurchase).where(
            CoursePurchase.user_id == user.id,
            CoursePurchase.course_id == body.course_id,
            CoursePurchase.status == "pending",
        ).order_by(CoursePurchase.created_at.desc())
    )).scalars().first()
    if purchase is None:
        purchase = CoursePurchase(
            user_id=user.id, course_id=body.course_id, course_title=title,
            price_ars=price, status="pending",
        )
        db.add(purchase)
        await db.flush()  # obtener purchase.id para el external_reference
    else:
        # El catálogo puede haber cambiado entre reintentos: la fila refleja
        # siempre lo que la preference nueva va a cobrar.
        purchase.course_title = title
        purchase.price_ars = price

    from services.mercadopago_service import create_course_preference
    pref = await create_course_preference(
        user, purchase_id=str(purchase.id), title=title, price_ars=price,
    )
    purchase.mp_preference_id = pref.get("preference_id") or None
    await db.commit()
    return CourseCheckoutResponse(
        kind="redirect", url=pref["url"], course_id=body.course_id, status="pending",
    )


@router.post(
    "/checkout-cart",
    response_model=CartCheckoutResponse,
    summary="Comprar varios cursos en un solo pago (carrito)",
    responses={
        401: {"description": "Token inválido o ausente"},
        404: {"description": "Algún curso no existe"},
        409: {"description": "Ya tenés todos esos cursos"},
        422: {"description": "Curso pago sin precio configurado"},
        503: {"description": "Mercado Pago no configurado"},
    },
)
async def checkout_cart(
    body: CartCheckoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartCheckoutResponse:
    # Dedup preservando orden; el precio SIEMPRE sale del catálogo del backend.
    ids = list(dict.fromkeys(body.course_ids))
    courses = []
    for cid in ids:
        c = _find_course(cid)
        if not c:
            raise HTTPException(status_code=404, detail=f"Curso no encontrado: {cid}")
        courses.append(c)

    owned_ids = {
        r.course_id
        for r in (await db.execute(
            select(CoursePurchase).where(
                CoursePurchase.user_id == user.id,
                CoursePurchase.course_id.in_(ids),
                CoursePurchase.status.in_(("approved", "free")),
            )
        )).scalars().all()
    }
    skipped = [c["id"] for c in courses if c["id"] in owned_ids]
    to_buy = [c for c in courses if c["id"] not in owned_ids]
    if not to_buy:
        raise HTTPException(status_code=409, detail="Ya tenés acceso a todos esos cursos.")

    free_courses = [c for c in to_buy if c.get("is_free")]
    paid_courses = [c for c in to_buy if not c.get("is_free")]
    for c in paid_courses:
        if int(c.get("price_ars") or 0) <= 0:
            raise HTTPException(
                status_code=422,
                detail=f"El curso {c['id']} no tiene precio configurado.",
            )

    # Gratis → inscripción directa, sin MP.
    for c in free_courses:
        db.add(CoursePurchase(
            user_id=user.id, course_id=c["id"],
            course_title=str(c.get("title", ""))[:255], price_ars=0, status="free",
        ))

    if not paid_courses:
        try:
            await db.commit()
        except IntegrityError:
            # Race (doble click): otro request ya inscribió alguno — mismo resultado.
            await db.rollback()
        return CartCheckoutResponse(
            kind="enrolled", enrolled=[c["id"] for c in free_courses], skipped=skipped,
        )

    # Pagos → una orden (order_id) con N compras pending + UNA preference de MP.
    order_id = uuid4()
    pendings = []
    for c in paid_courses:
        p = CoursePurchase(
            user_id=user.id, course_id=c["id"],
            course_title=str(c.get("title", ""))[:255],
            price_ars=int(c["price_ars"]), status="pending", order_id=order_id,
        )
        db.add(p)
        pendings.append(p)
    await db.flush()

    from services.mercadopago_service import create_cart_preference
    pref = await create_cart_preference(
        user, order_id=str(order_id),
        items=[{"title": c["title"], "price_ars": int(c["price_ars"])} for c in paid_courses],
    )
    for p in pendings:
        p.mp_preference_id = pref.get("preference_id") or None
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Algún curso ya estaba comprado. Refrescá e intentá de nuevo.",
        ) from None
    return CartCheckoutResponse(
        kind="redirect", url=pref["url"],
        enrolled=[c["id"] for c in free_courses],
        pending=[c["id"] for c in paid_courses], skipped=skipped,
        total_ars=sum(int(c["price_ars"]) for c in paid_courses),
    )


@router.get(
    "/my-courses",
    response_model=MyCoursesResponse,
    summary="Cursos comprados / inscriptos del usuario",
    responses={401: {"description": "Token inválido o ausente"}},
)
async def my_courses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MyCoursesResponse:
    rows = list((await db.execute(
        select(CoursePurchase).where(
            CoursePurchase.user_id == user.id,
            CoursePurchase.status.in_(("approved", "free", "pending")),
        ).order_by(CoursePurchase.created_at.desc())
    )).scalars().all())
    # Un solo item por curso: preferimos el estado con acceso sobre pending.
    best: dict[str, OwnedCourse] = {}
    rank = {"approved": 0, "free": 0, "pending": 1}
    for r in rows:
        cur = best.get(r.course_id)
        if cur is None or rank.get(r.status, 9) < rank.get(cur.status, 9):
            best[r.course_id] = OwnedCourse(
                course_id=r.course_id, course_title=r.course_title, status=r.status,
            )
    return MyCoursesResponse(items=list(best.values()))


# ── Medición de demanda ──

@router.post(
    "/interest",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Registrar interés en un curso (abrir detalle / solicitar info / inscribirse)",
)
async def record_interest(
    body: RecordInterestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.add(AcademiaInterest(
        user_id=user.id, course_id=body.course_id, course_title=body.course_title,
        topic=body.topic, action=body.action,
    ))
    await db.commit()


@router.get(
    "/demand",
    response_model=DemandResponse,
    summary="Demanda agregada por tema y curso (solo admin)",
    responses={403: {"description": "Requiere admin"}},
)
async def get_demand(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> DemandResponse:
    rows = list((await db.execute(select(AcademiaInterest))).scalars().all())

    topic_counts: dict[str, int] = {}
    course_agg: dict[str, dict] = {}
    for r in rows:
        topic = r.topic or "sin_tema"
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        c = course_agg.setdefault(
            r.course_id,
            {"course_title": r.course_title or r.course_id, "total": 0, "inscribir": 0, "info": 0, "view": 0},
        )
        c["total"] += 1
        if r.action in ("inscribir", "info", "view"):
            c[r.action] += 1
        if r.course_title:
            c["course_title"] = r.course_title

    by_topic = [TopicDemand(topic=t, count=n) for t, n in
                sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)]
    by_course = [CourseDemand(course_id=cid, **agg) for cid, agg in
                 sorted(course_agg.items(), key=lambda x: x[1]["total"], reverse=True)]
    return DemandResponse(total_events=len(rows), by_topic=by_topic, by_course=by_course)
