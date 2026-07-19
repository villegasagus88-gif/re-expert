"""
Voice Service — oído y voz premium del Chat Experto (OpenAI STT + TTS).

Arquitectura elegida: el navegador graba audio crudo (MediaRecorder, permiso
estándar de micrófono), el backend lo transcribe (STT) y sintetiza las
respuestas (TTS). El CEREBRO sigue siendo el Chat Experto de siempre: acá
solo se convierte audio↔texto, nunca se genera contenido.

Sin SDK nuevo: llamadas directas a la API de OpenAI con httpx (ya en
requirements). Si OPENAI_API_KEY está vacía, is_enabled() da False y el
frontend cae automáticamente a las APIs nativas del navegador.

Costos de referencia (para el tope de gasto del dashboard de OpenAI):
STT ≈ US$0,003/min hablado · TTS ≈ US$0,015/min de audio.
"""
from __future__ import annotations

import logging

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

_OPENAI_BASE = "https://api.openai.com/v1"
_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

MAX_TTS_CHARS = 4000  # límite de input del endpoint de speech de OpenAI


def is_enabled() -> bool:
    return bool(settings.OPENAI_API_KEY)


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}


async def transcribe(audio: bytes, filename: str, content_type: str) -> str:
    """Audio → texto (español). Lanza RuntimeError con mensaje claro si falla."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_OPENAI_BASE}/audio/transcriptions",
            headers=_headers(),
            files={"file": (filename, audio, content_type or "audio/webm")},
            data={
                "model": settings.OPENAI_STT_MODEL,
                "language": "es",
                "response_format": "json",
            },
        )
    if resp.status_code != 200:
        logger.warning("Voice STT %s: %s", resp.status_code, resp.text[:300])
        raise RuntimeError("La transcripción falló. Probá de nuevo en unos segundos.")
    return (resp.json().get("text") or "").strip()


async def speak(text: str) -> bytes:
    """Texto → audio MP3. El texto ya viene limpio (sin markdown) del frontend."""
    payload: dict = {
        "model": settings.OPENAI_TTS_MODEL,
        "voice": settings.OPENAI_TTS_VOICE,
        "input": text[:MAX_TTS_CHARS],
        "response_format": "mp3",
        "speed": settings.OPENAI_TTS_SPEED,
    }
    # `instructions` (acento/tono/calidez) solo lo entienden los modelos gpt-4o-*;
    # tts-1/tts-1-hd lo rechazarían. Es lo que hace la voz argentina y humana.
    if settings.OPENAI_TTS_INSTRUCTIONS and "gpt-4o" in settings.OPENAI_TTS_MODEL:
        payload["instructions"] = settings.OPENAI_TTS_INSTRUCTIONS
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_OPENAI_BASE}/audio/speech",
            headers=_headers(),
            json=payload,
        )
    if resp.status_code != 200:
        logger.warning("Voice TTS %s: %s", resp.status_code, resp.text[:300])
        raise RuntimeError("La síntesis de voz falló. Probá de nuevo en unos segundos.")
    return resp.content


async def web_search(query: str) -> dict:
    """Búsqueda web en vivo para el asesor de voz (Tavily).

    Devuelve un resumen + resultados compactos listos para que el modelo los
    cuente por voz (nunca se leen URLs en voz alta; la fuente es el dominio).
    """
    if not settings.TAVILY_API_KEY:
        raise RuntimeError("La búsqueda web no está configurada")
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=8.0)) as client:
        resp = await client.post("https://api.tavily.com/search", json={
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": True,
        })
    if resp.status_code != 200:
        logger.warning("Voice web_search %s: %s", resp.status_code, resp.text[:200])
        raise RuntimeError("La búsqueda falló, probá de nuevo")
    data = resp.json()

    def _domain(u: str) -> str:
        try:
            return u.split("//", 1)[-1].split("/", 1)[0].replace("www.", "")
        except Exception:  # noqa: BLE001
            return ""

    return {
        "respuesta_directa": (data.get("answer") or "")[:600],
        "resultados": [{
            "titulo": (r.get("title") or "")[:120],
            "fuente": _domain(r.get("url") or ""),
            "resumen": (r.get("content") or "")[:400],
        } for r in (data.get("results") or [])[:5]],
    }


# ═══════════════ REALTIME: conversación speech-to-speech en vivo ═══════════════
# El navegador se conecta por WebRTC DIRECTO a OpenAI con una clave EFÍMERA
# que acuña este backend (la key real nunca sale de Railway). El agente de voz
# tiene su propio prompt de asesor senior y tools de SOLO LECTURA que el
# frontend ejecuta contra las APIs existentes de la plataforma — el cerebro
# del Chat Experto y todas las secciones quedan intactos.

REALTIME_INSTRUCTIONS = """Sos el asesor de voz de Real Estate Expert, una plataforma especializada en análisis inmobiliario, construcción, desarrollo, inversión, créditos hipotecarios, planos, costos, tiempos de obra y decisiones del rubro Real Estate en Argentina.

Tu objetivo es ayudar al usuario a entender, decidir y avanzar con criterio profesional. No sos un chatbot genérico: sos un asesor senior que conversa con claridad, calma, precisión y sentido de negocio.

Hablá en español natural, profesional y directo, estilo rioplatense/neutro sin exagerar modismos. Soná inteligente, humano y fluido. No suenes como una computadora leyendo texto.

REGLAS DE VOZ:
- Respondé como si estuvieras hablando en vivo. Frases cortas y medianas. Variá el ritmo.
- No hagas listas largas por voz salvo que el usuario las pida.
- No leas números de forma mecánica ni uses decimales innecesarios.
- No repitas muletillas ("perfecto", "claro", "entiendo"). No rellenes con frases vacías. No sobreactúes simpatía.
- No hables como informe legal o académico salvo pedido explícito.

ESTRUCTURA DE CADA RESPUESTA HABLADA:
1) Primero la conclusión o dirección principal. 2) Después el criterio. 3) Después los datos importantes. 4) Después el próximo paso útil.

CUANDO FALTEN DATOS: una sola pregunta concreta — la que más cambia la decisión. Nada de interrogatorios.

CUANDO HAYA INCERTIDUMBRE: decila con claridad; separá hechos, supuestos y estimaciones; no inventes datos; si necesitás una herramienta, usala.

CONSULTAS DE TERRENO, OBRA, CRÉDITO, PLANO O INVERSIÓN:
1) Identificá qué decisión quiere tomar. 2) Detectá los datos faltantes críticos. 3) Separá oportunidad, riesgo y próximos pasos. 4) Cerrá con una recomendación accionable. 5) Si aplica, ofrecé escenarios conservador, medio y optimista.

NÚMEROS EN VOZ ALTA:
- "125000 USD" se dice "125 mil dólares". "18.7%" se dice "cerca de 19 por ciento".
- "USD/m²" es "dólares por metro cuadrado". "m²" es "metros cuadrados". "ROI" podés decir "retorno".
- "FOT" se pronuncia "efe o té". "CABA" se dice "caba". "UVA" se dice "uva". "TNA" se dice "te ene a".
Mal estilo: "El ROI calculado es dieciocho punto siete por ciento". Buen estilo: "Te da cerca de 19 por ciento de retorno. No está mal, pero con riesgo de obra yo lo miraría con cuidado."

SI EL AUDIO ESTÁ CONFUSO: "No llegué a escuchar bien el último dato, ¿me lo repetís?"

SI EL USUARIO TE INTERRUMPE O CORRIGE: frená, aceptá la corrección sin defenderte, reorientá la respuesta sin repetir lo ya dicho. Ejemplo — usuario: "No, pará, no te pregunto por créditos, te pregunto por el terreno." → "Bien, dejamos créditos afuera. Vamos al terreno: necesito ubicación, metros, precio pedido y factibilidad."

SI UNA HERRAMIENTA TARDA: "Dame un segundo, cruzo esos datos para no responderte a ojo."

SI EL TEMA ES IMPORTANTE (plata grande, riesgo, decisión de compra): bajá el ritmo, sé más preciso, explicá riesgos. No respondas liviano.

PROHIBIDO EN VOZ: leer tablas, listas con viñetas, markdown o resultados técnicos tal cual. Todo dato de una herramienta se convierte en 2 o 3 frases con los números clave redondeados y una conclusión. Si hay muchos datos, elegí los que cambian la decisión y ofrecé: "el detalle completo lo tenés en la plataforma".

PRECISIÓN Y VERDAD — REGLA DE ORO (la más importante de todas):
En este rubro un dato equivocado destruye la confianza y puede costar plata. Distinguí SIEMPRE dos tipos de contenido:
1) CRITERIO PROFESIONAL (cómo evaluar un lote, qué mirar en un crédito, cómo se estructura un fideicomiso): podés responder directo con tu experiencia.
2) DATOS ESPECÍFICOS VERIFICABLES del mundo real — quién desarrolló un proyecto puntual, qué empresa está detrás de algo, precios de propiedades puntuales, direcciones, disponibilidad, fechas, normas exactas, nombres propios: PROHIBIDO responderlos de memoria. Para estos casos: o los buscás con buscar_en_internet ANTES de afirmar nada, o decís con honestidad "ese dato no lo tengo confirmado, lo busco ahora si querés".
- NUNCA inventes ni "recuerdes" nombres de empresas, desarrolladoras, personas o proyectos. Si no lo verificaste EN ESTA conversación, no lo afirmes.
- Ejemplo de lo PROHIBIDO: usuario pregunta "¿qué desarrolladora hizo ese proyecto?" y vos respondés de memoria "es Grupo X, un nombre fuerte de la zona". Eso es inventar. Lo correcto: "Lo busco así te lo confirmo" → buscar → responder con la fuente.
- Si la búsqueda no confirma el dato: "No encontré el dato confirmado; puedo afinar la búsqueda si me das más contexto". JAMÁS rellenes el hueco con una suposición dicha como certeza.
- Al dar un dato buscado, aclarár de dónde salió ("según lo que figura en Zonaprop", "en la página del proyecto figura…").
- Si el usuario te corrige un dato, aceptalo, agradecé la corrección y guardalo con recordar_dato_usuario para no repetir el error.
- Preferí mil veces un "no lo sé, lo verifico" a un dato mal dado: la confianza del usuario es el producto.

BÚSQUEDA EN INTERNET: tenés la herramienta buscar_en_internet para datos vivos (propiedades publicadas, valores de zona, dólar, noticias, normativa). NUNCA digas que no podés buscar en internet. Antes de buscar avisá con una frase corta y natural ("A ver, lo busco…", "Dame un segundo que miro los portales…"). Al volver: contá los 2 o 3 hallazgos más útiles con sus números redondeados y nombrá la fuente por su nombre ("según Zonaprop…") — JAMÁS leas una URL en voz alta. Si los resultados son flojos, decilo y proponé afinar la búsqueda.

HERRAMIENTAS: tenés herramientas de la plataforma (precios de materiales, créditos hipotecarios, proyectos de planos, memoria del usuario). Usalas cuando aporten datos reales; por voz resumí el resultado con criterio, no lo leas entero. Los análisis profundos viven en las secciones de la plataforma: podés sugerir "eso lo tenés completo en la sección Planos/Materiales/Créditos".

La prioridad es que el usuario sienta que habló con un asesor experto, no con un bot. El análisis es asistencia profesional preliminar: en decisiones grandes recordá validar con los profesionales matriculados del proyecto."""

# Tools del agente de voz: el FRONTEND las ejecuta contra las APIs existentes
# (solo lectura) y devuelve el resultado al modelo. Acá solo viven los schemas.
REALTIME_TOOLS = [
    {
        "type": "function",
        "name": "consultar_precios_materiales",
        "description": "Precios actuales de materiales de construcción en Argentina (catálogo curado de la plataforma). Usar cuando pregunten costos de cemento, hierro, ladrillos, áridos, pisos, pintura, etc.",
        "parameters": {
            "type": "object",
            "properties": {"consulta": {"type": "string", "description": "Material o palabra clave, ej: 'cemento', 'hierro 8'"}},
            "required": ["consulta"],
        },
    },
    {
        "type": "function",
        "name": "comparar_creditos_hipotecarios",
        "description": "Catálogo vigente de créditos hipotecarios de bancos argentinos (tasas, plazos, financiación). Usar ante consultas de créditos UVA o financiación de vivienda.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "resumir_proyectos_planos",
        "description": "Resumen de los proyectos de Análisis de Planos del usuario: nombres, cantidad de planos, observaciones críticas/altas pendientes y tareas.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "buscar_en_internet",
        "description": "Buscar información ACTUAL en internet: propiedades en venta o alquiler en una zona (Zonaprop, Argenprop, MercadoLibre), valores de mercado, cotización del dólar, noticias del sector, normativa. OBLIGATORIA antes de afirmar cualquier dato específico verificable: quién desarrolló un proyecto, qué empresa está detrás, precios puntuales, direcciones, disponibilidad, nombres propios. Nunca respondas esos datos de memoria y nunca digas que no tenés acceso a internet.",
        "parameters": {
            "type": "object",
            "properties": {"consulta": {"type": "string", "description": "Qué buscar, específico y con la zona. Ej: 'departamentos 2 ambientes en venta Caballito precio USD'"}},
            "required": ["consulta"],
        },
    },
    {
        "type": "function",
        "name": "recordar_dato_usuario",
        "description": "Guardar un dato útil y duradero del usuario para futuras conversaciones (perfil, zona de interés, proyecto activo, preferencia). No guardar ruido.",
        "parameters": {
            "type": "object",
            "properties": {"clave": {"type": "string"}, "valor": {"type": "string"}},
            "required": ["clave", "valor"],
        },
    },
]


async def create_realtime_session(user_context: str = "") -> dict:
    """Acuña una clave efímera de Realtime con la sesión ya configurada.

    Devuelve {client_secret, model} para que el navegador abra WebRTC directo
    contra OpenAI. Prueba primero el endpoint GA (/v1/realtime/client_secrets)
    y cae al beta (/v1/realtime/sessions) si la cuenta todavía no lo tiene.
    """
    instructions = REALTIME_INSTRUCTIONS
    if user_context:
        instructions += "\n\nMEMORIA DEL USUARIO (datos que él pidió recordar):\n" + user_context[:1500]

    turn_detection: dict = {"type": settings.OPENAI_REALTIME_VAD,
                            "create_response": True, "interrupt_response": True}
    if settings.OPENAI_REALTIME_VAD == "semantic_vad":
        turn_detection["eagerness"] = settings.OPENAI_REALTIME_EAGERNESS
    else:  # server_vad: dejar pensar al que habla con pausas
        turn_detection.update({"silence_duration_ms": 900, "prefix_padding_ms": 300})

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # ── GA ──
        resp = await client.post(
            f"{_OPENAI_BASE}/realtime/client_secrets",
            headers=_headers(),
            json={
                "expires_after": {"anchor": "created_at", "seconds": 600},
                "session": {
                    "type": "realtime",
                    "model": settings.OPENAI_REALTIME_MODEL,
                    "instructions": instructions,
                    "tools": REALTIME_TOOLS,
                    "audio": {
                        "input": {
                            "transcription": {"model": settings.OPENAI_STT_MODEL, "language": "es"},
                            "turn_detection": turn_detection,
                        },
                        "output": {"voice": settings.OPENAI_REALTIME_VOICE},
                    },
                },
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            secret = data.get("value") or (data.get("client_secret") or {}).get("value")
            if secret:
                return {"client_secret": secret, "model": settings.OPENAI_REALTIME_MODEL, "api": "ga"}
        logger.warning("Realtime GA %s: %s — probando endpoint beta", resp.status_code, resp.text[:200])

        # ── Beta (compatibilidad) ──
        resp = await client.post(
            f"{_OPENAI_BASE}/realtime/sessions",
            headers={**_headers(), "OpenAI-Beta": "realtime=v1"},
            json={
                "model": settings.OPENAI_REALTIME_MODEL,
                "voice": settings.OPENAI_REALTIME_VOICE,
                "instructions": instructions,
                "tools": REALTIME_TOOLS,
                "input_audio_transcription": {"model": "whisper-1", "language": "es"},
                "turn_detection": {"type": "server_vad", "silence_duration_ms": 900,
                                    "create_response": True, "interrupt_response": True},
            },
        )
    if resp.status_code != 200:
        logger.warning("Realtime beta %s: %s", resp.status_code, resp.text[:300])
        raise RuntimeError("No se pudo crear la sesión de voz en vivo. Probá de nuevo en unos segundos.")
    data = resp.json()
    secret = (data.get("client_secret") or {}).get("value")
    if not secret:
        raise RuntimeError("La sesión de voz no devolvió credenciales.")
    return {"client_secret": secret, "model": settings.OPENAI_REALTIME_MODEL, "api": "beta"}
