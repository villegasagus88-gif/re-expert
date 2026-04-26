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
    ANTHROPIC_API_KEY: str = Field(..., min_length=1)
    DATABASE_URL: str = Field(..., min_length=1)
    JWT_SECRET: str = Field(..., min_length=1)

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

    # ===== ANTHROPIC =====
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6-20250514"

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
