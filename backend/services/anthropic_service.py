"""
Anthropic client service: streams Claude responses and builds system prompt
with knowledge base context loaded from Supabase Storage.

Routing strategy:
- Si `user_message` se provee a `build_system_prompt`, usamos el router
  inteligente (`context_router.select_context_for_message`) para inyectar
  solo el `_meta/` obligatorio + top-K docs relevantes al tema preguntado.
  Esto reduce ~80% los tokens de input vs bulk dump y mantiene calidad
  (las reglas + índice + glosario siempre están).
- Si el router falla o no se provee mensaje, caemos al legacy bulk dump
  (`load_knowledge_context`) como red de seguridad.
"""
import asyncio
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from anthropic import AsyncAnthropic
from config.settings import settings
from services.knowledge_storage import knowledge_storage

logger = logging.getLogger(__name__)

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    """Lazily build the shared async Anthropic client."""
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


BASE_SYSTEM_PROMPT = """Sos RE Expert, un asistente experto en Real Estate argentino.
Ayudas a desarrolladores, inversores e inmobiliarias con preguntas sobre costos de
construcción, rendimientos de inversión, normativa básica y rubros de obra en
Argentina.

Respondés en español rioplatense, de forma clara y concisa. Cuando corresponda,
usá la información de la sección "Base de conocimiento" que se adjunta más abajo
para fundamentar tus respuestas. Si no tenés información suficiente, decilo
directamente en lugar de inventar.

## Tools de fuentes oficiales (CRÍTICO — leer antes de responder)

Tenés acceso a tres herramientas para consultar fuentes oficiales en tiempo real.
**Usalas SIEMPRE que la respuesta dependa de un dato volátil**, en vez de
inventar el número o decir "no sé".

  • `get_dolar_cotizaciones` — cotizaciones del dólar (oficial, blue, MEP, CCL,
    cripto, tarjeta, mayorista). Datos en tiempo real (5 min de caché). USAR
    cuando pregunten "a cuánto está el dólar X", o necesites convertir ARS↔USD
    con tipo de cambio actual.

  • `get_indec_serie` — series oficiales (INDEC vía datos.gob.ar): IPC, ICC
    (costo de la construcción), EMAE, tipo de cambio promedio mensual BCRA, etc.
    USAR para inflación, costo de construcción mensual, salarios, índices.

  • `fetch_official_source(url)` — GET genérico a fuentes oficiales whitelisteadas
    (.gob.ar, .gov.ar, BCRA, INDEC, ARBA, AGIP, AFIP, infoleg, BORA, GCBA,
    apis.datos.gob.ar). USAR para leer un artículo de ley en infoleg, una
    alícuota en ARBA/AGIP, o una norma reciente en BORA.

### Reglas de uso de tools

1. **Datos volátiles → SIEMPRE tool, nunca memoria del modelo.** FX, alícuotas,
   índices, jornales UOCRA, precios de materiales, normativa reciente.
2. **Citá la fuente y el `fetched_at` que devolvió la tool.** Ej: "Según
   dolarapi.com (consultado hace 2 min): MEP = $1.145."
3. **Si la tool devuelve `error`**, decile al usuario "no pude consultar la
   fuente oficial en este momento" + sugerí dónde mirarlo (BCRA, INDEC, etc.).
   NO inventes el dato como compensación.
4. **Una pasada eficiente**: si necesitás 2 datos, podés llamar las 2 tools en
   el mismo turno. No hagas más de 4 llamadas por respuesta.
5. **Cuando uses datos de la Base de conocimiento abajo** (que es estructural y
   estable: teoría, normativa de base, fórmulas), citala como "según la base
   curada" o "según el material de referencia".
"""


# Prompt para el contexto "sol": asistente de intake de datos del proyecto.
# A diferencia del chat general, SOL no necesita la base de conocimiento —
# lo que importa es extraer datos estructurados del mensaje del usuario y
# confirmar en qué sección se cargan.
SOL_SYSTEM_PROMPT = """Sos SOL, asistente de carga de datos del sistema RE Expert.
Tu rol es recibir información en lenguaje natural del usuario y:

1. ANALIZAR qué tipo de dato es (pago, avance de obra, precio de material,
   proveedor, hito, gasto extra, etc.).
2. Si falta información crítica, hacer MÁXIMO 1-2 preguntas cortas y simples
   para completar el dato.
3. Confirmar el dato estructurado y decir en qué sección se cargó.

## Secciones del sistema donde podés rutear datos
- **Pagos** → pagos realizados, pendientes, montos, proveedores, fechas
- **Cronograma** → hitos, fechas, avances de etapa, retrasos, entregas
- **Materiales** → precios actualizados, cotizaciones, variaciones
- **Costos** → gastos presupuestados o extra, desvíos, rubros
- **Proveedores** → datos de contacto, rubros, condiciones

## Reglas
- Respondés en español rioplatense, tono amigable pero profesional.
- Sé MUY concisa: respuestas cortas y claras.
- Cuando confirmes un dato cargado, indicá la sección destino con este
  formato exacto: `[CARGADO→Sección]`
- Si el usuario quiere conversar o preguntar algo (no cargar datos),
  respondé normalmente usando tu conocimiento del proyecto y del sector.
- Usá Markdown simple, sin exceso.
- No hagas preguntas innecesarias si el dato ya está completo.
- Siempre confirmá el dato antes de "cargarlo".

## Formato estructurado al cargar un dato
Cuando detectes un dato completo y lo vayas a cargar, incluí un bloque JSON
al final de tu respuesta dentro de un fence ```json ... ``` con esta forma:

```json
{
  "section": "pagos|cronograma|materiales|costos|proveedores",
  "fields": { ... campos relevantes del dato ... }
}
```

Esto le permite al frontend extraer el dato estructurado. No inventes campos:
usá solamente los que el usuario te dio explícitamente."""


async def load_knowledge_context() -> str:
    """
    Carga todos los archivos .md del bucket 'knowledge' de Supabase Storage
    y los concatena en un único string. Si falla (bucket vacío, red caída, etc.),
    loguea un warning y devuelve "".
    """
    try:
        files = await asyncio.wait_for(knowledge_storage.list_files(), timeout=5)
    except Exception as e:
        logger.warning("No se pudo listar archivos de knowledge: %s", e)
        return ""

    # Extensiones legibles directo por el LLM (markdown + texto + datos en YAML).
    # CSV/JSON los maneja KnowledgeBaseService con parser propio; acá nos quedamos
    # con los formatos que ya son texto plano y aprovechables sin transformación.
    SUPPORTED_EXTS = (".md", ".txt", ".yaml", ".yml")
    md_files = [f for f in files if f["name"].lower().endswith(SUPPORTED_EXTS)]
    chunks: list[str] = []
    for f in md_files:
        try:
            content = await asyncio.wait_for(
                knowledge_storage.get_text_content(f["path"]), timeout=5
            )
            chunks.append(f"# {f['name']}\n\n{content}")
        except Exception as e:
            logger.warning("No se pudo leer %s: %s", f["path"], e)

    return "\n\n---\n\n".join(chunks)


async def _load_routed_knowledge(user_message: str) -> str:
    """
    Usa el context router para devolver solo el contexto relevante a la pregunta
    del usuario (meta obligatorio + top-K docs por dominio). Si falla, devuelve
    "" para que el caller decida el fallback.
    """
    try:
        # Import diferido para evitar ciclo + permitir monkeypatch en tests.
        from services.context_router import select_context_for_message

        _domain, ctx = await select_context_for_message(user_message)
        return ctx
    except Exception as e:
        logger.warning("build_system_prompt: router falló (%s), fallback a bulk", e)
        return ""


async def build_system_prompt(
    context_type: str = "chat",
    project_context: str = "",
    user_message: str | None = None,
) -> str:
    """
    Arma el system prompt para el request actual.

    - context_type="chat" (default): prompt general + base de conocimiento.
      Si `user_message` viene, ruteamos por dominio (router inteligente).
      Si no, caemos al bulk dump (legacy, para compat con callers viejos).
    - context_type="sol": prompt de intake de datos + datos reales del proyecto
      del usuario (no necesita el KB general).
    """
    if context_type == "sol":
        if project_context:
            return (
                f"{SOL_SYSTEM_PROMPT}\n\n"
                f"## Datos actuales del proyecto del usuario\n\n"
                f"{project_context}"
            )
        return SOL_SYSTEM_PROMPT

    knowledge = ""
    if user_message:
        knowledge = await _load_routed_knowledge(user_message)

    # Fallback de seguridad: si el router no devolvió nada (o no se pasó
    # user_message), cargamos el KB completo como antes.
    if not knowledge:
        knowledge = await load_knowledge_context()

    if not knowledge:
        return BASE_SYSTEM_PROMPT
    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"## Base de conocimiento\n\n"
        f"{knowledge}"
    )


ToolRunner = Callable[[str, dict[str, Any]], Awaitable[dict]]

# Tope de iteraciones del loop tool-use. Cada iteración es una llamada al
# modelo. 4 alcanza para casos típicos (1-2 fetch + síntesis) sin riesgo
# de bucle infinito si el modelo se queda pidiendo tools.
MAX_TOOL_ITERATIONS = 4


async def stream_chat(
    messages: list[dict],
    system: str,
    max_tokens: int = 4096,
    tools: list[dict] | None = None,
    tool_runner: ToolRunner | None = None,
) -> AsyncIterator[dict]:
    """
    Streams Claude's response. Yields event dicts:
      - {"type": "delta", "text": <chunk>}
      - {"type": "tool_use", "name": "...", "input": {...}}     (si tools)
      - {"type": "tool_result", "name": "...", "result": {...}} (si tools)
      - {"type": "end", "input_tokens": N, "output_tokens": M}

    Cuando `tools` y `tool_runner` se proveen, hace loop tool-use:
      stream → si stop_reason=='tool_use' → ejecutamos tools →
      stream con tool_results → repetir hasta end_turn o tope.

    Mutamos `messages` para acumular bloques de assistant/tool_result (es
    requisito del protocolo de Anthropic para la continuación del turno).

    Raises anthropic exceptions on API errors (caller handles).
    """
    client = get_client()

    # Path simple: sin tools, comportamiento idéntico al original.
    if not tools or not tool_runner:
        async with client.messages.stream(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield {"type": "delta", "text": text}

            final = await stream.get_final_message()
            yield {
                "type": "end",
                "input_tokens": final.usage.input_tokens,
                "output_tokens": final.usage.output_tokens,
            }
        return

    # Path con tools: loop hasta que el modelo no pida más tools.
    total_input = 0
    total_output = 0

    for _ in range(MAX_TOOL_ITERATIONS):
        async with client.messages.stream(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield {"type": "delta", "text": text}

            final = await stream.get_final_message()
            total_input += final.usage.input_tokens
            total_output += final.usage.output_tokens

        # Recolectar bloques: texto que ya emitimos por delta + tool_uses.
        tool_uses: list[Any] = []
        assistant_blocks: list[dict] = []
        for b in final.content:
            btype = getattr(b, "type", None)
            if btype == "text":
                assistant_blocks.append({"type": "text", "text": b.text or ""})
            elif btype == "tool_use":
                assistant_blocks.append(
                    {
                        "type": "tool_use",
                        "id": b.id,
                        "name": b.name,
                        "input": b.input or {},
                    }
                )
                tool_uses.append(b)

        # Si no llamó tools, terminamos.
        if final.stop_reason != "tool_use" or not tool_uses:
            break

        # Ejecutar tools en serie. Si una falla, devolvemos el error como
        # parte del tool_result (el modelo lo lee y puede compensar).
        messages.append({"role": "assistant", "content": assistant_blocks})
        tool_result_blocks: list[dict] = []
        for tu in tool_uses:
            inputs = tu.input or {}
            yield {"type": "tool_use", "name": tu.name, "input": inputs}
            try:
                result = await tool_runner(tu.name, inputs)
            except Exception as e:
                logger.exception("tool_runner falló para %s", tu.name)
                result = {"error": f"Tool {tu.name} crashed: {e}"}
            yield {"type": "tool_result", "name": tu.name, "result": result}
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )
        messages.append({"role": "user", "content": tool_result_blocks})

    yield {
        "type": "end",
        "input_tokens": total_input,
        "output_tokens": total_output,
    }
