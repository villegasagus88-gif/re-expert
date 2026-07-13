"""
Application settings loaded from environment variables.

Uses pydantic-settings (which wraps python-dotenv) to load values from
`backend/.env` locally, or directly from env vars in production (Railway).
Variables without defaults are REQUIRED - the app refuses to start if missing.
"""
from pathlib import Path

from core.cors import build_cors_origins
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ===== REQUIRED (min_length=1 enforces non-empty values) =====
    DATABASE_URL: str = Field(..., min_length=1)
    JWT_SECRET: str = Field(..., min_length=1)
    # ANTHROPIC_API_KEY es opcional: si está vacía, el agente cae a Gemini
    # (siempre que GEMINI_API_KEY esté seteada).
    ANTHROPIC_API_KEY: str = ""

    # ===== SUPABASE (optional — only needed for storage/realtime, not auth) =====
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ===== STRIPE (legacy — reemplazado por Mercado Pago para AR) =====
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_SUCCESS_URL: str = ""
    STRIPE_CANCEL_URL: str = ""

    # ===== MERCADO PAGO (billing en ARS) =====
    # Suscripciones (preapproval). Mientras MP_ACCESS_TOKEN + MP_PLAN_ID estén
    # vacíos, TODO el módulo de MP es inerte y el backend se comporta como antes.
    # Cargar en Railway cuando Agustín cree el plan en Mercado Pago.
    MP_ACCESS_TOKEN: str = ""          # access token privado (Bearer). SECRET.
    MP_PUBLIC_KEY: str = ""            # public key (para MP.js en el front, opcional).
    MP_WEBHOOK_SECRET: str = ""        # secreto para verificar la firma del webhook.
    MP_PLAN_ID: str = ""              # id del preapproval_plan (con trial de 7 días).
    MP_BACK_URL: str = ""             # URL de retorno post-checkout. Default: FRONTEND_URL/app.html

    # ===== OPTIONAL =====
    PORT: int = 8000

    # ===== APP METADATA =====
    APP_NAME: str = "RE Expert API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Cantidad de proxies confiables que appendan a X-Forwarded-For, contados
    # desde la derecha. En Railway el único hop confiable es el edge (1). La IP
    # del rate-limit se toma de esa posición (no forjable por el cliente).
    RATE_LIMIT_TRUSTED_PROXY_HOPS: int = 1

    # ===== AUTH / JWT =====
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===== ADMIN =====
    # Emails con acceso de administrador (gestión del knowledge base), separados
    # por coma. Ej: "mati@re-expert.app,agustin@re-expert.app". Vacío = nadie.
    ADMIN_EMAILS: str = ""

    # ===== DB POOL =====
    # Conexiones que mantenemos warm en el pool. Supabase Pooler en
    # transaction mode acepta hasta 15-30 conexiones por cliente.
    # Para 1 instancia Railway con tráfico moderado, 5 suele alcanzar.
    DB_POOL_SIZE: int = 5
    # Overflow temporal cuando hay picos. Total max = pool_size + max_overflow.
    DB_MAX_OVERFLOW: int = 5
    # Segundos antes de descartar una conexión idle.
    DB_POOL_RECYCLE: int = 1800  # 30 min
    # Timeout esperando una conexión libre del pool.
    DB_POOL_TIMEOUT: int = 10

    # ===== ANTHROPIC =====
    # Usamos el alias (sin fecha) que siempre apunta al último snapshot
    # estable. Override con env var ANTHROPIC_MODEL si querés pinear.
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    # Modelo más barato para queries simples (~75% más barato que Sonnet).
    # Se activa via heurística en services/model_selector.py.
    ANTHROPIC_MODEL_FAST: str = "claude-haiku-4-5"
    # Habilita el selector dinámico Haiku/Sonnet. Si está en False, todo
    # va a ANTHROPIC_MODEL (comportamiento legacy).
    SMART_MODEL_ROUTING: bool = True

    # ===== LLM PROVIDER (selector) =====
    # auto = usa Gemini si hay GEMINI_API_KEY, sino Anthropic.
    # gemini | anthropic = forzar uno específico.
    LLM_PROVIDER: str = "auto"

    # ===== GEMINI (free tier) =====
    # Crear key en https://aistudio.google.com/apikey
    GEMINI_API_KEY: str = ""
    # Modelos free disponibles: gemini-2.5-flash | gemini-2.0-flash | gemini-2.5-pro (con quota más chica)
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ===== AGENT / SCHEDULER =====
    # URL pública del backend — usada para construir links absolutos a PDFs
    # generados (los que se mandan por WhatsApp/Telegram tienen que ser
    # alcanzables desde el celular del destinatario). En prod, Railway URL;
    # en dev local, localhost:8000 (solo accesible desde la PC del user).
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

    # Habilita el poller que dispara recordatorios. Ponelo en False en tests.
    SCHEDULER_ENABLED: bool = True
    # Intervalo (segundos) entre polls. 30s = baja latencia y carga ínfima.
    SCHEDULER_POLL_INTERVAL_SECONDS: int = 30
    # Máximo de recordatorios procesados por tick (evita lock-and-flood).
    SCHEDULER_BATCH_SIZE: int = 50

    # ===== TELEGRAM (opcional) =====
    # Token del bot creado vía @BotFather. Si está vacío, el canal queda deshabilitado.
    TELEGRAM_BOT_TOKEN: str = ""
    # Username del bot SIN el @ (usado para construir deep links t.me/<username>?start=<token>)
    TELEGRAM_BOT_USERNAME: str = ""
    # URL pública del backend para registrar webhook del bot (ej. https://re-expert-production.up.railway.app)
    TELEGRAM_WEBHOOK_BASE_URL: str = ""
    # Secret arbitrario para validar requests del webhook (header X-Telegram-Bot-Api-Secret-Token)
    TELEGRAM_WEBHOOK_SECRET: str = ""
    # Agente SOL por mensaje libre de Telegram. APAGADO por defecto (decisión
    # 2026-07-04): el pairing y las notificaciones salientes funcionan igual;
    # el mensaje libre responde un texto fijo hasta prender este flag.
    TELEGRAM_AGENT_ENABLED: bool = False

    # ===== TWILIO / WHATSAPP (opcional) =====
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""  # ej. "whatsapp:+14155238886"

    # ===== EMAIL (opcional, vía Resend) =====
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = "RE Expert <hola@re-expert.app>"

    # ===== MAPS (opcional) =====
    GOOGLE_MAPS_API_KEY: str = ""

    # ===== TAVILY (web search para chat) =====
    # API key de https://tavily.com — habilita la tool `search_web` del chat.
    # Si está vacía, la tool queda deshabilitada y el modelo cae al
    # comportamiento anterior (citar fuentes pero no fetchear web abierta).
    # Free tier: 1000 búsquedas/mes.
    TAVILY_API_KEY: str = ""

    # ===== OPENAI (voz del Chat Experto: STT + TTS) =====
    # API key de https://platform.openai.com — habilita la voz premium
    # (transcripción Whisper + voz de respuesta). Si está vacía, la voz
    # cae automáticamente a las APIs nativas del navegador (gratis).
    # Configurá un límite de gasto en el dashboard de OpenAI.
    OPENAI_API_KEY: str = ""
    OPENAI_STT_MODEL: str = "gpt-4o-mini-transcribe"   # alternativa: whisper-1
    OPENAI_TTS_MODEL: str = "gpt-4o-mini-tts"          # alternativa: tts-1
    OPENAI_TTS_VOICE: str = "nova"

    # ===== CORS =====
    # Primary frontend URL — required in production (DEBUG=False).
    # e.g. https://re-expert.app  or  https://staging.re-expert.app
    FRONTEND_URL: str = ""
    # Extra origins to allow in addition to FRONTEND_URL (comma-aware JSON list).
    # Leave empty; used only for special cases like CDN preview URLs.
    CORS_ORIGINS: list[str] = []

    @property
    def cors_allowed_origins(self) -> list[str]:
        return build_cors_origins(
            debug=self.DEBUG,
            frontend_url=self.FRONTEND_URL,
            extra_origins=self.CORS_ORIGINS,
        )

    # ===== MONITORING (Sentry) =====
    # Sentry DSN — leave empty to disable Sentry entirely.
    # Get it from: https://sentry.io/settings/<org>/projects/<project>/keys/
    SENTRY_DSN: str = ""
    # Environment tag attached to every event (production / staging / dev).
    SENTRY_ENVIRONMENT: str = "production"
    # Performance traces sampling [0.0–1.0]. 0.0 disables performance, only errors.
    # Free tier of Sentry has 10k transactions/month; keep low and ramp up.
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0


try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(
        f"Missing or invalid environment variables. "
        f"Copy backend/.env.example to backend/.env and fill in the values.\n"
        f"Details: {e}"
    ) from e
