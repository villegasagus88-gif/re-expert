"""
Context Router — clasifica la pregunta del usuario a un dominio de Real
Estate y selecciona del KnowledgeBase los archivos relevantes a ese dominio.

Dominios soportados:
    costos, materiales, normativa, financiero, proyecto, general

Uso típico:

    from services.context_router import select_context_for_message

    kb_context = await select_context_for_message(user_message)

`select_context_for_message` devuelve texto listo para inyectar en el
system prompt, truncado a ~4000 tokens (≈16000 chars).
"""
from __future__ import annotations

import logging
import unicodedata
from typing import Literal

from services.knowledge_base_service import _tokenize, knowledge_base

logger = logging.getLogger(__name__)

Domain = Literal["costos", "materiales", "normativa", "financiero", "proyecto", "general"]

# Todos los dominios soportados (orden = prioridad en caso de empate).
ALL_DOMAINS: tuple[Domain, ...] = (
    "costos",
    "materiales",
    "normativa",
    "financiero",
    "proyecto",
    "general",
)

# Keywords por dominio. Se normalizan (minúsculas, sin acentos) al cargar.
# Se agregan sinónimos comunes de RE argentino.
_RAW_KEYWORDS: dict[Domain, tuple[str, ...]] = {
    "costos": (
        "costo", "costos", "precio", "precios", "presupuesto", "presupuestos",
        "valor", "valores", "cotizacion", "cotizaciones", "m2", "metro",
        "metros", "cuadrado", "cuadrados", "usd", "dolar", "dolares", "peso",
        "pesos", "tarifa", "honorarios", "cuanto", "sale", "cuesta",
    ),
    "materiales": (
        "material", "materiales", "hormigon", "cemento", "arena", "cal",
        "ladrillo", "ladrillos", "bloque", "bloques", "acero", "hierro",
        "varilla", "malla", "pintura", "piso", "pisos", "porcelanato",
        "ceramica", "azulejo", "membrana", "aislante", "aislacion", "cano",
        "canos", "caneria", "aluminio", "chapa", "madera", "durlock", "yeso",
        "revestimiento", "revoque", "mamposteria", "insumo", "insumos",
    ),
    "normativa": (
        "normativa", "normativas", "ley", "leyes", "codigo", "codigos",
        "reglamento", "reglamentos", "ordenanza", "ordenanzas", "permiso",
        "permisos", "habilitacion", "municipalidad", "municipal", "zonificacion",
        "zona", "zonas", "fot", "fos", "plano", "planos", "plusvalia",
        "abl", "catastro", "escritura", "dominio", "titulo", "titulos",
        "subdivision", "loteo", "factibilidad",
    ),
    "financiero": (
        "financiacion", "financiamiento", "credito", "creditos", "hipoteca",
        "hipotecario", "hipotecaria", "prestamo", "prestamos", "cuota",
        "cuotas", "tasa", "tasas", "interes", "intereses", "rentabilidad",
        "roi", "retorno", "inversion", "inversiones", "alquiler", "alquileres",
        "renta", "rentas", "capital", "flujo", "caja", "ganancia", "ganancias",
        "dividendo", "dividendos", "yield", "cap", "rate", "uva", "pagos",
        "plazo", "plazos", "seguro", "seguros",
    ),
    "proyecto": (
        "proyecto", "proyectos", "obra", "obras", "etapa", "etapas",
        "cronograma", "cronogramas", "planificacion", "planificar",
        "arquitecto", "arquitecta", "ingeniero", "ingeniera", "contratista",
        "demolicion", "excavacion", "fundacion", "fundaciones", "estructura",
        "estructuras", "terminacion", "terminaciones", "entrega", "llave",
        "fiscal", "director", "plazo", "timing", "ejecucion", "gantt",
    ),
    "general": (
        # 'general' no tiene keywords propias; se usa como fallback explícito.
    ),
}


def _normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# Pre-normalize keyword sets at import time.
DOMAIN_KEYWORDS: dict[Domain, frozenset[str]] = {
    domain: frozenset(_normalize(kw) for kw in kws)
    for domain, kws in _RAW_KEYWORDS.items()
}


# ~4000 tokens de presupuesto. Heurística: 1 token ≈ 4 chars en inglés,
# un poco menos en español; usamos 4 como aprox conservador.
MAX_CONTEXT_TOKENS = 4000
CHARS_PER_TOKEN = 4
MAX_CONTEXT_CHARS = MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN  # 16000


def classify_query(message: str) -> Domain:
    """
    Devuelve el dominio con más matches de keywords. Si ninguno matchea,
    devuelve 'general'. Desempates: orden de `ALL_DOMAINS`.
    """
    tokens = set(_tokenize(message))
    if not tokens:
        return "general"

    best: Domain = "general"
    best_score = 0
    for domain in ALL_DOMAINS:
        if domain == "general":
            continue
        kws = DOMAIN_KEYWORDS[domain]
        score = len(tokens & kws)
        if score > best_score:
            best_score = score
            best = domain

    return best if best_score > 0 else "general"


def estimate_tokens(text: str) -> int:
    """Estimación barata del nro de tokens a partir de chars."""
    return len(text) // CHARS_PER_TOKEN


async def select_context_for_message(
    message: str,
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> tuple[Domain, str]:
    """
    Clasifica el mensaje, pide al KB el contenido relevante del dominio
    detectado, y devuelve (domain, context_text) truncado a ~max_tokens.
    Si el dominio clasificado es 'general', pasamos domain=None al KB
    para que busque en todo el bucket.
    """
    domain = classify_query(message)
    kb_domain: str | None = None if domain == "general" else domain
    max_chars = max_tokens * CHARS_PER_TOKEN

    try:
        context = await knowledge_base.get_context(
            query=message,
            domain=kb_domain,
            max_chars=max_chars,
        )
    except Exception as e:
        logger.warning("Context router: KB falló (%s), devuelvo vacío", e)
        context = ""

    # Safety net por si el KB excedió max_chars
    if len(context) > max_chars:
        context = context[:max_chars]

    return domain, context
