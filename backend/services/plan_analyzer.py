"""
Plan Analyzer — motor IA del sistema de Análisis de Planos.

Módulo NUEVO e independiente (mismo criterio que opportunity_scanner): no toca
la Capa 2 de Agustín, sólo importa get_client() de anthropic_service. Tres
operaciones, todas con tool_choice forzado para respuesta estructurada:

  classify_plan(...)  → clasificación rápida (tipo, especialidad, lámina, escala…)
  analyze_plan(...)   → análisis completo según modo + perfil (resumen, riesgos,
                        observaciones accionables, score, checklist, preguntas)
  compare_plans(...)  → comparación entre dos planos / versiones

Reglas de calidad (spec de producto):
  - Lenguaje PRUDENTE: nunca afirmar incumplimientos normativos categóricos.
  - Confianza explícita por análisis y por observación (0-100).
  - El análisis es asistencia preliminar: no reemplaza profesionales matriculados.

Los archivos viajan como bloques nativos de Anthropic: imágenes → image block,
PDF → document block (visión de PDF nativa del modelo).
"""
from __future__ import annotations

import base64
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)

MAX_ANALYSIS_TOKENS = 8000
MAX_CLASSIFY_TOKENS = 1000
MAX_COMPARE_TOKENS = 8000

_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "planos"

DISCLAIMER = (
    "El análisis IA es una herramienta de asistencia y revisión preliminar. "
    "No reemplaza la validación de arquitectos, ingenieros, calculistas, "
    "instaladores ni profesionales matriculados."
)


@lru_cache(maxsize=1)
def load_frequent_errors() -> list[dict]:
    """Biblioteca curada de errores frecuentes (estática, viaja con el deploy)."""
    p = _DATA_DIR / "errores_frecuentes.json"
    if not p.exists():
        return []
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("errors", [])
    except Exception:  # noqa: BLE001 — biblioteca opcional, nunca rompe el análisis
        logger.warning("PlanAnalyzer: no se pudo leer errores_frecuentes.json")
        return []


def _media_block(file_type: str, file_data: bytes) -> dict:
    """Bloque multimodal para Anthropic según el tipo de archivo."""
    media = _MEDIA_TYPES.get(file_type.lower(), "application/pdf")
    b64 = base64.standard_b64encode(file_data).decode("ascii")
    if media == "application/pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": media, "data": b64}}
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}}


# ─────────────────────────── prompts base ───────────────────────────

_PRUDENCE = """REGLAS DE LENGUAJE (obligatorias):
- NUNCA afirmes incumplimientos normativos de forma categórica. Usá: "punto a verificar normativamente", "requiere validación profesional", "debe revisarse contra el código local aplicable".
- NUNCA digas "esto está mal construido", "esto incumple la norma", "este plano no sirve".
- Diferenciá explícitamente: detectado con alta confianza / posible riesgo / información faltante / punto a validar.
- Si no hay información suficiente para confirmar un punto, decilo.
- Cada observación lleva su nivel de confianza (0-100) honesto: si la imagen no permite leer una medida, la confianza es baja.
- Español rioplatense profesional, claro y accionable. Nada de relleno."""

_MODE_INSTRUCTIONS = {
    "simple": """MODO: EXPLICACIÓN SIMPLE (para usuarios que no saben leer planos).
Explicá qué tipo de plano es, qué muestra, qué ambientes/sectores aparecen, cómo se organiza, accesos, circulaciones, medidas generales, zonas húmedas, relación entre espacios y elementos importantes. Lenguaje claro, sin tecnicismos innecesarios. Las observaciones deben ser mayormente informativas o de prioridad baja/media, explicadas en lenguaje simple.""",
    "errores": """MODO: REVISIÓN DE ERRORES POTENCIALES (antes de obra).
Buscá activamente: medidas dudosas, ambientes ajustados, puertas que interfieren, circulaciones incómodas, accesos mal resueltos, baños/cocinas con ventilación dudosa, instalaciones alejadas o ineficientes, escaleras a revisar, cocheras con maniobra dudosa, columnas que afecten funcionalidad, falta de detalles constructivos, información incompleta para presupuestar, riesgos de adicionales, problemas de mantenimiento futuro. Cada hallazgo → una observación accionable con prioridad honesta.""",
    "desarrollador": """MODO: ANÁLISIS PARA DESARROLLADOR (negocio inmobiliario).
Evaluá: calidad comercial del producto, eficiencia de m², relación superficie útil/común/vendible, ambientes con baja calidad comercial, circulaciones excesivas, espacios que consumen costo sin agregar valor, vendibilidad del diseño, mejoras de layout posibles, riesgos que afecten precio, velocidad de venta o rentabilidad, puntos que encarecen obra o complican comercialización. Recomendaciones PRÁCTICAS de negocio, no teoría.""",
    "constructor": """MODO: ANÁLISIS PARA CONSTRUCTOR / JEFE DE OBRA (ejecución).
Detectá: información insuficiente para ejecutar, falta de detalles, posibles interferencias, riesgos de adicionales, secuencia constructiva compleja, partidas críticas, puntos que generan discusión con el cliente o atrasos, definiciones previas necesarias, aclaraciones a pedir antes de iniciar obra. Observaciones accionables para obra, con responsable sugerido cuando aplique.""",
}

_PROFILE_HINTS = {
    "no_tecnico": "PERFIL DEL USUARIO: no técnico. Priorizá explicación simple, glosario de términos que uses, riesgos en lenguaje claro.",
    "constructor": "PERFIL DEL USUARIO: constructor. Priorizá riesgos de ejecución, detalles faltantes, interferencias, posibles adicionales y checklist de obra.",
    "desarrollador": "PERFIL DEL USUARIO: desarrollador. Priorizá eficiencia de m², vendibilidad, calidad comercial, sobrecostos, plazo y rentabilidad.",
    "jefe_obra": "PERFIL DEL USUARIO: jefe de obra. Priorizá pendientes por sector, prioridad, responsable sugerido y checklist operativo.",
    "arquitecto": "PERFIL DEL USUARIO: arquitecto/proyectista. Priorizá inconsistencias, correcciones sugeridas por lámina e información faltante.",
}

_ALERT_PROPS = {
    "title": {"type": "string", "description": "Título corto y concreto"},
    "location": {"type": "string", "description": "Ubicación en el plano (sector, ambiente, nivel)"},
    "category": {"type": "string", "description": "Categoría del hallazgo (ej: circulaciones, ventilacion, detalles_faltantes)"},
    "description": {"type": "string"},
    "risk": {"type": "string", "description": "Riesgo concreto en obra/negocio"},
    "impact": {"type": "string", "description": "Impacto posible (costo, plazo, funcionalidad, venta)"},
    "recommendation": {"type": "string", "description": "Recomendación accionable y prudente"},
    "priority": {"type": "string", "enum": ["critica", "alta", "media", "baja", "informativa"]},
    "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
    "suggested_action": {"type": "string", "description": "Acción sugerida corta (ej: 'Pedir detalle al proyectista')"},
}

_SCORE_AXIS = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "why": {"type": "string", "description": "Por qué ese puntaje"},
        "improve": {"type": "string", "description": "Qué mejorar para subirlo"},
    },
    "required": ["score", "why", "improve"],
}

_ANALYZE_TOOL = {
    "name": "informe_analisis_plano",
    "description": "Informe estructurado del análisis de un plano.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Resumen ejecutivo (5-10 oraciones): qué plano es, qué muestra, estado general"},
            "detected_data": {
                "type": "object",
                "properties": {
                    "que_es": {"type": "string"},
                    "que_muestra": {"type": "string"},
                    "ambientes": {"type": "array", "items": {"type": "string"}},
                    "medidas_relevantes": {"type": "array", "items": {"type": "string"}},
                    "niveles": {"type": "string"},
                    "elementos_importantes": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["que_es", "que_muestra", "ambientes"],
            },
            "general_risk": {"type": "string", "enum": ["bajo", "medio", "alto", "critico"]},
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100,
                           "description": "Confianza global del análisis según legibilidad y completitud del documento"},
            "plan_score": {
                "type": "object",
                "properties": {
                    "calidad_general": _SCORE_AXIS,
                    "comprension_documental": _SCORE_AXIS,
                    "coherencia": _SCORE_AXIS,
                    "constructibilidad": _SCORE_AXIS,
                    "eficiencia_comercial": _SCORE_AXIS,
                },
                "required": ["calidad_general", "comprension_documental", "constructibilidad"],
            },
            "strengths": {"type": "array", "items": {"type": "string"}, "description": "Puntos fuertes del plano"},
            "alerts": {
                "type": "array", "maxItems": 18,
                "items": {"type": "object", "properties": _ALERT_PROPS,
                          "required": ["title", "description", "priority", "confidence", "recommendation"]},
                "description": "Observaciones accionables, priorizadas honestamente",
            },
            "missing_info": {"type": "array", "items": {"type": "string"},
                             "description": "Información faltante en la documentación"},
            "inconsistencies": {"type": "array", "items": {"type": "string"}},
            "recommendations": {"type": "array", "items": {"type": "string"}},
            "suggested_questions": {
                "type": "array", "maxItems": 10,
                "items": {"type": "object", "properties": {
                    "question": {"type": "string"},
                    "category": {"type": "string"},
                    "priority": {"type": "string", "enum": ["critica", "alta", "media", "baja"]},
                    "reason": {"type": "string"},
                    "responsible": {"type": "string", "description": "A quién preguntarle (proyectista, calculista, instalador…)"},
                }, "required": ["question", "category", "priority", "reason", "responsible"]},
            },
            "checklist": {
                "type": "array", "maxItems": 14,
                "items": {"type": "object", "properties": {
                    "item": {"type": "string"},
                    "priority": {"type": "string", "enum": ["critica", "alta", "media", "baja"]},
                }, "required": ["item", "priority"]},
                "description": "Checklist previo a obra generado desde este plano",
            },
        },
        "required": ["summary", "detected_data", "general_risk", "confidence", "plan_score",
                     "strengths", "alerts", "missing_info", "recommendations",
                     "suggested_questions", "checklist"],
    },
}

_CLASSIFY_TOOL = {
    "name": "clasificar_plano",
    "description": "Clasificación rápida de un plano técnico.",
    "input_schema": {
        "type": "object",
        "properties": {
            "plan_type": {"type": "string", "enum": [
                "arquitectura", "estructura", "electrica", "sanitaria", "gas", "hvac",
                "detalles", "implantacion", "corte", "fachada", "municipal", "ejecutivo", "otro"]},
            "discipline": {"type": "string", "description": "Especialidad (ej: arquitectura, estructura, instalaciones)"},
            "sheet_number": {"type": "string", "description": "Número de lámina si es visible (ej: A-02)"},
            "scale": {"type": "string", "description": "Escala si es visible (ej: 1:100)"},
            "plan_date": {"type": "string", "description": "Fecha del plano si es visible"},
            "floor_level": {"type": "string", "description": "Planta o nivel (ej: Planta baja, 3er piso)"},
            "detected_version": {"type": "string", "description": "Versión/revisión si es visible (ej: Rev. C)"},
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "initial_observations": {"type": "string", "description": "1-2 oraciones de observaciones iniciales"},
        },
        "required": ["plan_type", "discipline", "confidence", "initial_observations"],
    },
}

_COMPARE_TOOL = {
    "name": "informe_comparacion_planos",
    "description": "Comparación estructurada entre dos planos o versiones.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Resumen de la comparación (qué se comparó y conclusión general)"},
            "general_risk": {"type": "string", "enum": ["bajo", "medio", "alto", "critico"]},
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "changes": {"type": "array", "items": {"type": "string"}, "description": "Cambios relevantes detectados"},
            "added": {"type": "array", "items": {"type": "string"}, "description": "Elementos agregados en el plano B"},
            "removed": {"type": "array", "items": {"type": "string"}, "description": "Elementos eliminados respecto del plano A"},
            "measure_changes": {"type": "array", "items": {"type": "string"}, "description": "Cambios de medidas u ubicación"},
            "alerts": {
                "type": "array", "maxItems": 14,
                "items": {"type": "object", "properties": _ALERT_PROPS,
                          "required": ["title", "description", "priority", "confidence", "recommendation"]},
                "description": "Inconsistencias y riesgos generados por los cambios, priorizados",
            },
            "impact": {"type": "array", "items": {"type": "string"},
                       "description": "Impacto posible en costo, plazo o ejecución"},
            "recommendations": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["summary", "general_risk", "confidence", "changes", "alerts", "recommendations"],
    },
}


def _project_context(project: Any) -> str:
    return (
        f"CONTEXTO DEL PROYECTO: '{project.name}' — tipo de obra: {project.obra_type}; "
        f"ubicación: {project.location or 'no informada'}; superficie estimada: "
        f"{project.estimated_area or 'no informada'}; etapa: {project.stage}; "
        f"objetivo del análisis: {project.analysis_goal}."
        + (f" Descripción: {project.description}" if project.description else "")
    )


def _plan_context(plan: Any) -> str:
    parts = [f"Archivo: {plan.file_name} (versión {plan.version})"]
    if plan.detected_plan_type:
        parts.append(f"tipo: {plan.detected_plan_type}")
    if plan.discipline:
        parts.append(f"especialidad: {plan.discipline}")
    if plan.sheet_number:
        parts.append(f"lámina: {plan.sheet_number}")
    if plan.scale:
        parts.append(f"escala: {plan.scale}")
    if plan.floor_level:
        parts.append(f"nivel: {plan.floor_level}")
    return "DATOS DEL PLANO: " + "; ".join(parts) + "."


def _extract_tool_input(resp: Any, tool_name: str) -> dict:
    for block in resp.content:
        if getattr(block, "type", "") == "tool_use" and block.name == tool_name:
            return dict(block.input)
    raise ValueError(f"La respuesta del modelo no incluyó el tool {tool_name}")


async def classify_plan(file_type: str, file_data: bytes, file_name: str) -> dict:
    """Clasificación rápida del plano (tipo, especialidad, lámina, escala, nivel)."""
    from services.anthropic_service import get_client

    client = get_client()
    resp = await client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=MAX_CLASSIFY_TOKENS,
        system=("Sos un revisor de documentación técnica de obra en Argentina. "
                "Clasificá el plano adjunto leyendo su carátula/rótulo si existe. "
                "Si un dato no es visible, dejalo vacío — no inventes." ),
        messages=[{"role": "user", "content": [
            _media_block(file_type, file_data),
            {"type": "text", "text": f"Clasificá este plano (archivo: {file_name}). Usá el tool."},
        ]}],
        tools=[_CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "clasificar_plano"},
    )
    return _extract_tool_input(resp, "clasificar_plano")


async def analyze_plan(plan: Any, project: Any, mode: str, profile: str) -> dict:
    """Análisis completo de un plano según modo y perfil. Devuelve el informe estructurado."""
    from services.anthropic_service import get_client

    mode_txt = _MODE_INSTRUCTIONS.get(mode, _MODE_INSTRUCTIONS["errores"])
    profile_txt = _PROFILE_HINTS.get(profile, "")
    frecuentes = load_frequent_errors()
    biblioteca = ""
    if frecuentes:
        cats = sorted({e["category"] for e in frecuentes})
        biblioteca = (
            "\nBIBLIOTECA DE ERRORES FRECUENTES (usá estas categorías cuando apliquen, "
            "y revisá activamente estos patrones): " + ", ".join(cats) + ". Ejemplos: "
            + "; ".join(f"{e['title']}" for e in frecuentes[:10]) + "."
        )

    system = (
        "Sos un revisor senior de planos para real estate y construcción en Argentina. "
        "Actuás como segunda revisión inteligente antes de obra: tu trabajo es detectar "
        "riesgos, inconsistencias, información faltante y puntos críticos, y convertirlos "
        "en observaciones ACCIONABLES.\n\n" + _PRUDENCE + "\n\n" + mode_txt
        + ("\n\n" + profile_txt if profile_txt else "") + biblioteca
    )
    resp = await get_client().messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=MAX_ANALYSIS_TOKENS,
        system=system,
        messages=[{"role": "user", "content": [
            _media_block(plan.file_type, plan.file_data),
            {"type": "text", "text": (
                _project_context(project) + "\n" + _plan_context(plan)
                + "\n\nAnalizá el plano adjunto y devolvé el informe completo usando el tool. "
                  "El plan_score debe estar EXPLICADO (why + improve por eje), nunca decorativo. "
                  "El checklist debe salir de lo que viste en ESTE plano, no genérico."
            )},
        ]}],
        tools=[_ANALYZE_TOOL],
        tool_choice={"type": "tool", "name": "informe_analisis_plano"},
    )
    return _extract_tool_input(resp, "informe_analisis_plano")


async def compare_plans(plan_a: Any, plan_b: Any, project: Any, focus: str = "") -> dict:
    """Comparación entre dos planos (versiones o especialidades)."""
    from services.anthropic_service import get_client

    focus_txt = f"\nFOCO PEDIDO POR EL USUARIO: {focus}" if focus else ""
    resp = await get_client().messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=MAX_COMPARE_TOKENS,
        system=("Sos un revisor senior de documentación de obra en Argentina, especializado en "
                "coordinación entre láminas y control de versiones. Compará el PLANO A y el "
                "PLANO B: cambios, elementos agregados/eliminados, cambios de medidas o "
                "ubicación, inconsistencias entre especialidades y riesgos generados por los "
                "cambios (impacto en costo, plazo, ejecución).\n\n" + _PRUDENCE),
        messages=[{"role": "user", "content": [
            {"type": "text", "text": f"PLANO A — {_plan_context(plan_a)}"},
            _media_block(plan_a.file_type, plan_a.file_data),
            {"type": "text", "text": f"PLANO B — {_plan_context(plan_b)}"},
            _media_block(plan_b.file_type, plan_b.file_data),
            {"type": "text", "text": (
                _project_context(project) + focus_txt
                + "\n\nCompará ambos planos y devolvé el informe usando el tool."
            )},
        ]}],
        tools=[_COMPARE_TOOL],
        tool_choice={"type": "tool", "name": "informe_comparacion_planos"},
    )
    return _extract_tool_input(resp, "informe_comparacion_planos")
