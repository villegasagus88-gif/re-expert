"""
Monitor de Créditos — Fase 2 (detección de cambios con IA).

Para cada crédito del catálogo:
  1. Baja la página oficial (official_url) y la convierte a texto.
  2. Le pide a Claude que extraiga los términos VIGENTES (tasa, plazo,
     financiación, ingreso mínimo, estado) como JSON estructurado (tool forzada).
  3. Diffea contra lo guardado en la DB.
  4. Por cada diferencia con confianza suficiente, escribe una `CreditProposal`
     en estado `pending_review` (dedup: no duplica propuestas pendientes del
     mismo campo).

NO publica nada: todo queda en la cola para validación humana. Tampoco toca el
dominio del chat (Capa 2): usa el cliente Anthropic compartido con su propio
prompt de extracción, aislado del system prompt del asistente.

El disparo es un endpoint admin (manual o por cron de Railway). El cómputo es
barato: corre esporádicamente sobre pocos créditos.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

import httpx
from config.settings import settings
from models.credit import Credit, CreditProposal
from services.anthropic_service import get_client
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_MAX_PAGE_CHARS = 14000
_FETCH_TIMEOUT = 20.0
_MIN_CONFIDENCE = 0.45  # debajo de esto no generamos propuestas (poco señal)

# Campos numéricos que extraemos + tolerancia para considerar "cambió".
# (rel = diferencia relativa; abs = diferencia absoluta en la unidad del campo)
_NUMERIC_TOL: dict[str, dict] = {
    "interest_rate_tna": {"abs": 0.01},
    "max_term_years": {"abs": 0},
    "max_financing_percent": {"abs": 0.1},
    "min_income_ars": {"rel": 0.05},
}

_EXTRACT_TOOL: dict[str, Any] = {
    "name": "reportar_terminos_credito",
    "description": (
        "Reporta los términos VIGENTES del crédito hipotecario tal como aparecen "
        "en la página oficial. Devolvé null en cualquier campo que la página no "
        "indique claramente; NO inventes ni asumas."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "found": {
                "type": "boolean",
                "description": "true si la página contiene términos de este crédito; false si es una página genérica/sin datos/caída.",
            },
            "interest_rate_tna": {
                "type": ["number", "null"],
                "description": "Tasa Nominal Anual como número en %. Ej: 4,5% → 4.5. Para UVA es la tasa en pesos sobre UVA. null si no figura.",
            },
            "max_term_years": {
                "type": ["integer", "null"],
                "description": "Plazo máximo en años. null si no figura.",
            },
            "max_financing_percent": {
                "type": ["number", "null"],
                "description": "Porcentaje máximo financiado sobre el valor de la propiedad (ej 75). null si no figura.",
            },
            "min_income_ars": {
                "type": ["number", "null"],
                "description": "Ingreso mínimo mensual exigido en pesos. null si no figura.",
            },
            "status": {
                "type": ["string", "null"],
                "enum": ["active", "discontinued", None],
                "description": "active si el crédito se ofrece; discontinued SOLO si la página dice explícitamente que se dio de baja / suspendió. null si no es claro.",
            },
            "confidence": {
                "type": "number",
                "description": "Confianza global 0..1 en la extracción.",
            },
            "rationale": {
                "type": "string",
                "description": "Cita textual breve de la página que respalda lo extraído (máx ~200 caracteres).",
            },
        },
        "required": ["found", "confidence"],
    },
}

_EXTRACT_SYSTEM = (
    "Sos un extractor de datos de créditos hipotecarios de bancos argentinos. "
    "Recibís el texto de una página oficial y devolvés SOLO los términos vigentes "
    "que la página indica explícitamente, llamando a la tool. Reglas: números en "
    "formato decimal con punto (4,5% → 4.5); montos en pesos como enteros; si un "
    "dato no está claramente en la página, devolvé null (nunca inventes ni uses "
    "conocimiento previo). Sé conservador con la confianza."
)


def _strip_html(html: str) -> str:
    """HTML → texto plano (sin dependencias). Acota para no inflar tokens."""
    html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<!--.*?-->", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = (
        text.replace("&nbsp;", " ").replace("&amp;", "&")
        .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'")
    )
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n\s*", "\n", text)
    return text.strip()[:_MAX_PAGE_CHARS]


async def _fetch(url: str) -> str | None:
    if not url:
        return None
    try:
        async with httpx.AsyncClient(
            timeout=_FETCH_TIMEOUT, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RE-Expert-Monitor/1.0)"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return _strip_html(resp.text)
    except Exception as e:  # noqa: BLE001 — fallo de red/HTTP no debe tumbar el batch
        logger.warning("Monitor: no se pudo bajar %s — %s", url, e)
        return None


def _credit_context(c: Credit) -> str:
    return (
        f"Banco: {c.bank_name}\nProducto: {c.credit_name} ({c.credit_type}, {c.rate_type})\n"
        f"Valores guardados — TNA: {c.interest_rate_tna}; plazo_años: {c.max_term_years}; "
        f"financiación_%: {c.max_financing_percent}; ingreso_mínimo_ars: {c.min_income_ars}; "
        f"estado: {c.status}"
    )


async def _extract_terms(c: Credit, page_text: str) -> dict | None:
    client = get_client()
    user = (
        f"Datos guardados del crédito (referencia, NO los copies si la página dice otra cosa):\n"
        f"{_credit_context(c)}\n\n--- TEXTO DE LA PÁGINA OFICIAL ---\n{page_text}"
    )
    try:
        resp = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=700,
            system=_EXTRACT_SYSTEM,
            tools=[_EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "reportar_terminos_credito"},
            messages=[{"role": "user", "content": user}],
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Monitor: extracción falló para %s — %s", c.id, e)
        return None
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use":
            return dict(block.input)
    return None


def _numeric_changed(old: Any, new: Any, field: str) -> bool:
    if new is None:
        return False
    try:
        new_f = float(new)
    except (TypeError, ValueError):
        return False
    if old is None:
        return True
    try:
        old_f = float(old)
    except (TypeError, ValueError):
        return True
    tol = _NUMERIC_TOL.get(field, {})
    if "abs" in tol:
        return abs(new_f - old_f) > tol["abs"]
    if "rel" in tol:
        base = abs(old_f) or 1.0
        return abs(new_f - old_f) / base > tol["rel"]
    return new_f != old_f


def _diff(c: Credit, ext: dict) -> list[dict]:
    """Lista de cambios {field, change_type, old, new}."""
    changes: list[dict] = []
    for field in ("interest_rate_tna", "max_term_years", "max_financing_percent", "min_income_ars"):
        new = ext.get(field)
        if _numeric_changed(getattr(c, field), new, field):
            changes.append({"field": field, "change_type": "field_update",
                            "old": getattr(c, field), "new": new})
    new_status = ext.get("status")
    if new_status == "discontinued" and c.status != "discontinued":
        changes.append({"field": "status", "change_type": "discontinued",
                        "old": c.status, "new": "discontinued"})
    return changes


async def _pending_fields(db: AsyncSession, credit_id: str) -> set[str]:
    rows = (await db.scalars(
        select(CreditProposal.field).where(
            CreditProposal.credit_id == credit_id,
            CreditProposal.status == "pending_review",
        )
    )).all()
    return set(rows)


async def run_monitor(db: AsyncSession, credit_ids: list[str] | None = None) -> dict:
    """Escanea créditos, detecta cambios y encola propuestas. Devuelve un resumen."""
    stmt = select(Credit).where(Credit.status != "discontinued")
    if credit_ids:
        stmt = stmt.where(Credit.id.in_(credit_ids))
    credits = (await db.scalars(stmt)).all()

    today = datetime.now().strftime("%Y-%m-%d")
    summary: dict[str, Any] = {
        "checked": 0, "fetched": 0, "proposals_created": 0,
        "skipped_low_confidence": 0, "errors": [], "details": [],
    }

    for c in credits:
        summary["checked"] += 1
        url = c.official_url or (c.source_urls[0] if c.source_urls else "")
        page = await _fetch(url)
        c.last_checked_at = today  # metadata operativa, no requiere aprobación
        if page is None:
            summary["errors"].append({"credit_id": c.id, "error": "fetch_failed", "url": url})
            continue
        summary["fetched"] += 1

        ext = await _extract_terms(c, page)
        if not ext:
            summary["errors"].append({"credit_id": c.id, "error": "extract_failed"})
            continue
        conf = float(ext.get("confidence") or 0)
        if not ext.get("found") or conf < _MIN_CONFIDENCE:
            summary["skipped_low_confidence"] += 1
            continue

        pending = await _pending_fields(db, c.id)
        created_here = 0
        for ch in _diff(c, ext):
            if ch["field"] in pending:
                continue  # ya hay una propuesta pendiente para ese campo
            db.add(CreditProposal(
                credit_id=c.id,
                change_type=ch["change_type"],
                field=ch["field"],
                old_value=None if ch["old"] is None else str(ch["old"]),
                new_value=None if ch["new"] is None else str(ch["new"]),
                source_url=url,
                confidence=conf,
                rationale=(ext.get("rationale") or "")[:500],
            ))
            created_here += 1
        summary["proposals_created"] += created_here
        if created_here:
            summary["details"].append({"credit_id": c.id, "new_proposals": created_here})

    await db.commit()
    logger.info("Monitor créditos: %s", json.dumps(summary, ensure_ascii=False))
    return summary
