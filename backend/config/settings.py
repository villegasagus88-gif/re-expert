"""
Application settings loaded from environment variables.

Uses pydantic-settings (which wraps python-dotenv) to load values from
`backend/.env` locally, or directly from env vars in production (Railway).
Variables without defaults are REQUIRED - the app refuses to start if missing.
"""
from pathlib import Path

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

    # ===== OPTIONAL =====
    STRIPE_KEY: str = ""
    PORT: int = 8000

    # ===== APP METADATA =====
    APP_NAME: str = "RE Expert API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ===== ANTHROPIC =====
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6-20250514"

    # ===== CORS =====
    CORS_ORIGINS: list[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
    ]


try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(
        f"Missing or invalid environment variables. "
        f"Copy backend/.env.example to backend/.env and fill in the values.\n"
        f"Details: {e}"
    ) from e
