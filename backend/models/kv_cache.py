"""Cache clave-valor persistente con TTL (tabla kv_cache).

Pensado para caches que hoy viven en RAM del proceso y se PIERDEN en cada
redeploy de Railway → el próximo usuario vuelve a pagar la generación. Ej:
resúmenes de noticias (digests) y traducciones. NO es fuente de verdad: si algo
falla, se regenera. El contenido es idéntico al del cache en memoria.
"""
from datetime import datetime
from typing import Any

from models.base import Base
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class KVCache(Base):
    __tablename__ = "kv_cache"

    key: Mapped[str] = mapped_column(String(512), primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
