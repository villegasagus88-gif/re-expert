"""
Selector dinámico de modelo Anthropic (Haiku vs Sonnet).

Por qué existe:
  Sonnet 4.6 es ~3-4x más caro que Haiku 4.5 (input/output). Para
  queries simples (qué es X, cuál es el precio promedio de Y, etc.)
  Haiku da resultados igualmente buenos. Sonnet conviene para:
    - Razonamiento financiero complejo (TIR, sensibilidad, escenarios).
    - Análisis multimodal de planos (imágenes attachments).
    - Modo SOL (agente con tool-use y state persistence).
    - Análisis normativo/legal con citas precisas.

Heurística (ajustable sin tocar código si querés A/B test):
  - Cualquier attachment → Sonnet (multimodal).
  - context_type='sol' → Sonnet (agente).
  - Mensaje largo (> 280 chars) → Sonnet (probablemente requiere
    contexto del usuario rico).
  - Keywords explícitos de razonamiento profundo → Sonnet.
  - Por default → Haiku (~70% de las queries reales caen acá).

Costo objetivo (en escenario 100 users × 15 q/día):
  - Sin routing: USD 30/día solo en input → USD 900/mes Sonnet.
  - Con routing (70% Haiku): USD 12/día → USD 360/mes.
  - Con routing + prompt caching: ~USD 240/mes.

Estimación de impacto: -55-70% del costo respecto al baseline puro
Sonnet, sin pérdida apreciable de calidad en queries simples.
"""
from __future__ import annotations

import re
from typing import Final

from config.settings import settings

# Keywords que indican que la query necesita razonamiento (Sonnet).
# En minúsculas; se hace matching case-insensitive.
_SONNET_KEYWORDS: Final[frozenset[str]] = frozenset([
    # análisis financiero
    "tir", "van", "cap rate", "irr", "npv", "wacc", "discount",
    "sensibilidad", "escenario", "factibilidad", "viabilidad",
    "rentabilidad", "amortización", "payback", "cash flow",
    "cashflow", "flujo de caja", "apalancamiento", "leverage",
    # presupuestación
    "presupuesto", "cómputo", "computo", "metrado", "rubros",
    "desglose", "estimación", "cost-to-complete", "eac", "etc",
    "cpi", "spi", "costo unitario",
    # normativa / legal
    "código urbanístico", "codigo urbanistico", "ccyc", "ccycn",
    "ley 24", "ley 27", "decreto", "resolución", "dnu",
    "fideicomiso", "boleto", "escritura", "dominio", "tracto",
    "cadena dominial", "saneamiento", "prescripción", "donación",
    "consorcio", "propiedad horizontal", "uif", "blanqueo",
    # análisis profundo
    "comparar", "comparación", "vs", "diferencia entre",
    "evaluar", "evaluación", "diagnóstico", "estrategia",
    "qué conviene", "que conviene", "recomendación", "alternativa",
    "riesgo", "riesgos legales", "due diligence",
])

# Heurística de longitud: queries cortas suelen ser preguntas factuales.
_LONG_QUERY_CHARS: Final[int] = 280

# Pre-compilamos un regex que matchea cualquier keyword como substring
# rodeado de límites de palabra. Más rápido que `keyword in msg` para
# cada uno de los ~50 keywords.
_KEYWORDS_RE: Final[re.Pattern] = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in _SONNET_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def pick_model(
    message: str,
    *,
    context_type: str = "chat",
    has_attachments: bool = False,
    plan: str = "free",
) -> str:
    """
    Devuelve el id del modelo a usar para este turno de chat.

    No depende de saldo Anthropic — solo decide qué modelo PEDIRLE.
    Si Anthropic falla por billing, el llm_providers.py hace fallback
    a Gemini que es lo siguiente en la cadena (no problema de este
    módulo).
    """
    # Feature flag global. Si False, comportamiento legacy.
    if not settings.SMART_MODEL_ROUTING:
        return settings.ANTHROPIC_MODEL

    # 1. Multimodal → Sonnet (Haiku no maneja imágenes tan bien).
    if has_attachments:
        return settings.ANTHROPIC_MODEL

    # 2. SOL (agente con tool-use) → Sonnet por ahora.
    if context_type == "sol":
        return settings.ANTHROPIC_MODEL

    # 3. Queries largas (probablemente complejas) → Sonnet.
    msg = (message or "").strip()
    if len(msg) > _LONG_QUERY_CHARS:
        return settings.ANTHROPIC_MODEL

    # 4. Keywords de razonamiento profundo → Sonnet.
    if _KEYWORDS_RE.search(msg):
        return settings.ANTHROPIC_MODEL

    # 5. Default: Haiku (más rápido y barato para preguntas simples).
    return settings.ANTHROPIC_MODEL_FAST
