from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "RE Expert API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6-20250514"

    CORS_ORIGINS: list[str] = ["http://localhost:8080", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
