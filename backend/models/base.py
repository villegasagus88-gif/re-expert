"""
SQLAlchemy async engine, session, and declarative Base.

Uses asyncpg driver for PostgreSQL (Supabase). The engine and session
factory are created lazily on first use so that the metadata can be
inspected without an active DB connection.
"""
import json
from datetime import date
from decimal import Decimal

from config.settings import settings
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


def _json_default(obj):
    """Hace JSON-serializable lo que una columna JSONB no soporta nativo.

    Sin esto, guardar un Decimal (p.ej. los costos por rubro del proyecto) en
    una columna JSONB rompe con 'Object of type Decimal is not JSON
    serializable' → 500. Decimal→float (queda como número), date→ISO.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, date):  # date y datetime (datetime hereda de date)
        return obj.isoformat()
    return str(obj)


def _json_serializer(obj) -> str:
    return json.dumps(obj, default=_json_default, ensure_ascii=False)


def _asyncpg_url(url: str) -> str:
    """Convert postgres://... or postgresql://... to postgresql+asyncpg://..."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""
    pass


_engine: AsyncEngine | None = None
_SessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Lazily create and return the shared async engine.

    Pool config:
      - pool_size: conexiones warm permanentes.
      - max_overflow: conexiones extra bajo picos (temporales).
      - pool_recycle: cierra conexiones idle después de N segundos
        (evita que Supabase Pooler las corte y nos quedemos con stale
        sockets).
      - pool_pre_ping: hace SELECT 1 antes de usar la conexión.
      - pool_timeout: cuánto esperar una conexión libre antes de
        levantar TimeoutError (mejor que esperar infinito).

    asyncpg connect_args:
      - statement_cache_size=0 + prepared_statement_cache_size=0 son
        requeridos por Supabase Pooler en transaction mode (no soporta
        prepared statements). Safe en direct connection también.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _asyncpg_url(settings.DATABASE_URL),
            echo=settings.DEBUG,
            json_serializer=_json_serializer,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
            },
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Lazily create and return the shared session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _SessionLocal


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a DB session and closes it."""
    async with get_session_factory()() as session:
        yield session
