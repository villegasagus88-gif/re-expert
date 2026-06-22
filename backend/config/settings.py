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

    # ===== STRIPE =====
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_SUCCESS_URL: str = ""
    STRIPE_CANCEL_URL: str = ""

    # ===== OPTIONAL =====
    PORT: int = 8000

    # ===== APP METADATA =====
    APP_NAME: str = "RE Expert API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ===== AUTH / JWT =====
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Vigencia del link de recuperación de contraseña (forgot-password).
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # ===== ANTHROPIC =====
    # Usamos el alias (sin fecha) que siempre apunta al último snapshot
    # estable. Override con env var ANTHROPIC_MODEL si querés pinear.
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

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

    # ===== TWILIO / WHATSAPP (opcional) =====
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""  # ej. "whatsapp:+14155238886"

    # ===== EMAIL (opcional, vía Resend) =====
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = "RE Expert <hola@re-expert.app>"

    # ===== MAPS (opcional) =====
    GOOGLE_MAPS_API_KEY: str = ""

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


try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(
        f"Missing or invalid environment variables. "
        f"Copy backend/.env.example to backend/.env and fill in the values.\n"
        f"Details: {e}"
    ) from e
