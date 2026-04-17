"""
SQLAlchemy async engine, session, and declarative Base.

Uses asyncpg driver for PostgreSQL (Supabase). The engine and session
factory are created lazily on first use so that the metadata can be
inspected without an active DB connection.
"""
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config.settings import settings


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
    """Lazily create and return the shared async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _asyncpg_url(settings.DATABASE_URL),
            echo=settings.DEBUG,
            pool_pre_ping=True,
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
