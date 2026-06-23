"""
Runner standalone del monitor de créditos (Fase 2) — pensado para cron.

Uso (desde el directorio backend/):
    python -m scripts.monitor_creditos

Abre una sesión de DB, siembra el catálogo si hace falta y corre el monitor:
baja las fuentes oficiales de cada crédito, detecta cambios con IA y encola
propuestas en estado `pending_review`. NO publica nada por sí solo: las
propuestas se revisan y aprueban desde la consola admin (admin-creditos.html).

Para automatizarlo, configurar un cron en Railway (ej. diario) que ejecute este
módulo. Corre con las mismas env vars del servicio (DB + ANTHROPIC_API_KEY).
Sale con código 0 si terminó (aunque alguna fuente falle) y 1 ante un error
inesperado.
"""
from __future__ import annotations

import asyncio
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("monitor_creditos")


async def _run() -> dict:
    from models.base import get_session_factory
    from services import creditos_repo
    from services.creditos_monitor import run_monitor

    async with get_session_factory()() as db:
        await creditos_repo.seed_if_empty(db)
        return await run_monitor(db)


def main() -> None:
    try:
        summary = asyncio.run(_run())
    except Exception:
        logger.exception("Monitor de créditos falló")
        raise SystemExit(1)
    logger.info("Resumen: %s", json.dumps(summary, ensure_ascii=False))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0)


if __name__ == "__main__":
    main()
