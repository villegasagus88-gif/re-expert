"""
Track D — ingest persistence round-trip (D2) + ownership 404 scoping.

El test_ingest.py existente es schema-only; acá verificamos el WRITE PATH:
que POST /api/data/ingest mapee cada `type` a la fila ORM correcta con el
user_id del usuario. Más tests de ownership (404) sobre el patrón db.get +
user_id que comparten todos los CRUD (contacts como muestra).
"""
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from core.auth import get_current_user
from core.rate_limit import limiter
from main import app
from models.base import get_db
from models.budget import Budget
from models.contact import Contact
from models.material import Material
from models.milestone import Milestone
from models.payment import Payment


@pytest.fixture(autouse=True)
def _disable_limiter():
    prev = limiter.enabled
    limiter.enabled = False
    try:
        yield
    finally:
        limiter.enabled = prev


def _make_user():
    u = MagicMock()
    u.id = uuid4()
    u.email = "u@example.com"
    u.plan = "free"
    return u


class _IngestDB:
    """Captura los objetos agregados; asigna id en commit/refresh."""

    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        for o in self.added:
            if getattr(o, "id", None) is None:
                o.id = uuid4()

    async def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()

    async def rollback(self):
        pass


@contextmanager
def _client(user=None, db=None):
    user = user or _make_user()
    db = db if db is not None else _IngestDB()

    async def _get_user():
        return user

    async def _get_db():
        yield db

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db
    try:
        yield TestClient(app), db, user
    finally:
        app.dependency_overrides.clear()


# ── ingest round-trip por tipo ───────────────────────────────────────

def test_ingest_payment_creates_payment_row():
    with _client() as (client, db, user):
        r = client.post(
            "/api/data/ingest",
            json={
                "type": "payment",
                "amount": 500000,
                "currency": "ARS",
                "provider": "Albañil Juan",
                "concept": "anticipo",
                "paid_at": "2026-04-20",
            },
        )
    assert r.status_code == 201
    assert r.json()["type"] == "payment"
    rec = db.added[0]
    assert isinstance(rec, Payment)
    assert rec.user_id == user.id
    assert float(rec.monto) == 500000
    assert rec.estado == "pagado"
    assert rec.concepto == "anticipo"
    assert rec.proveedor == "Albañil Juan"


def test_ingest_milestone_creates_milestone_row():
    with _client() as (client, db, user):
        r = client.post(
            "/api/data/ingest",
            json={"type": "milestone", "name": "Hormigonado losa P1", "status": "done", "completed_at": "2026-04-22"},
        )
    assert r.status_code == 201
    rec = db.added[0]
    assert isinstance(rec, Milestone)
    assert rec.user_id == user.id
    assert rec.name == "Hormigonado losa P1"
    assert rec.status == "done"


def test_ingest_material_creates_material_row():
    with _client() as (client, db, user):
        r = client.post(
            "/api/data/ingest",
            json={"type": "material", "name": "Cemento Loma Negra", "unit": "bolsa", "unit_price": 12500, "supplier": "Easy"},
        )
    assert r.status_code == 201
    rec = db.added[0]
    assert isinstance(rec, Material)
    assert rec.user_id == user.id
    assert rec.name == "Cemento Loma Negra"
    assert float(rec.unit_price) == 12500


def test_ingest_budget_creates_budget_row():
    with _client() as (client, db, user):
        r = client.post(
            "/api/data/ingest",
            json={"type": "budget", "category": "Albañilería", "amount": 8500000, "kind": "planned"},
        )
    assert r.status_code == 201
    rec = db.added[0]
    assert isinstance(rec, Budget)
    assert rec.user_id == user.id
    assert rec.category == "Albañilería"
    assert float(rec.amount) == 8500000


def test_ingest_rejects_unknown_type():
    with _client() as (client, _db, _user):
        r = client.post("/api/data/ingest", json={"type": "spaceship", "x": 1})
    assert r.status_code == 422


# ── ownership 404 scoping (contacts como muestra del patrón común) ────

def _contacts_db(get_return):
    db = MagicMock()
    db.get = AsyncMock(return_value=get_return)
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    return db


def test_delete_other_users_contact_returns_404():
    foreign = MagicMock(spec=Contact)
    foreign.id = uuid4()
    foreign.user_id = uuid4()  # otro dueño
    with _client(db=_contacts_db(foreign)) as (client, _db, _user):
        r = client.delete(f"/api/contacts/{foreign.id}")
    assert r.status_code == 404


def test_delete_missing_contact_returns_404():
    with _client(db=_contacts_db(None)) as (client, _db, _user):
        r = client.delete(f"/api/contacts/{uuid4()}")
    assert r.status_code == 404


def test_delete_own_contact_succeeds():
    user = _make_user()
    own = MagicMock(spec=Contact)
    own.id = uuid4()
    own.user_id = user.id
    db = _contacts_db(own)
    with _client(user=user, db=db) as (client, _db, _u):
        r = client.delete(f"/api/contacts/{own.id}")
    assert r.status_code == 204
    db.delete.assert_awaited_once()
