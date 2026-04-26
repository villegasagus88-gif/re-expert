"""
Anthropic client service: streams Claude responses and builds system prompt
with optional knowledge base context loaded from Supabase Storage.
"""
import asyncio
import logging
from collections.abc import AsyncIterator

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

    md_files = [f for f in files if f["name"].lower().endswith(".md")]
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


async def build_system_prompt(context_type: str = "chat", project_context: str = "") -> str:
    """
    Arma el system prompt para el request actual.

    - context_type="chat" (default): prompt general + base de conocimiento.
    - context_type="sol": prompt de intake de datos + datos reales del proyecto
      del usuario (si están disponibles).
    """
    if context_type == "sol":
        if project_context:
            return (
                f"{SOL_SYSTEM_PROMPT}\n\n"
                f"## Datos actuales del proyecto del usuario\n\n"
                f"{project_context}"
            )
        return SOL_SYSTEM_PROMPT

    knowledge = await load_knowledge_context()
    if not knowledge:
        return BASE_SYSTEM_PROMPT
    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"## Base de conocimiento\n\n"
        f"{knowledge}"
    )


async def stream_chat(
    messages: list[dict],
    system: str,
    max_tokens: int = 4096,
) -> AsyncIterator[dict]:
    """
    Streams Claude's response. Yields event dicts:
      - {"type": "delta", "text": <chunk>}
      - {"type": "end", "input_tokens": N, "output_tokens": M}

    Raises anthropic exceptions on API errors (caller handles).
    The final "end" event is emitted once, after the text stream completes.
    """
    client = get_client()
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
