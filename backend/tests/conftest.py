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
# Secreto fuerte de test (≥32 chars, variado, no-placeholder): pasa el validator
# de robustez de settings incluso con DEBUG=False (los tests corren en modo prod).
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-prod-9f3a71c2e8b45d60a")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-dummy-service-role")
