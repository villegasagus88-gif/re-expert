"""
Pytest configuration: set dummy env vars BEFORE any backend module imports,
so config.settings doesn't fail in CI where real secrets aren't available.
"""
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://user:pass@localhost:5432/test",
)
os.environ.setdefault("JWT_SECRET", "test-dummy-secret")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-dummy-service-role")
