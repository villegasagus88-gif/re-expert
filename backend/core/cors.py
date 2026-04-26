"""
CORS origin resolution — environment-aware, wildcard-free in production.

Three environment modes:

  dev   (DEBUG=True, no FRONTEND_URL)
        → localhost/127.0.0.1 origins only

  staging (DEBUG=True OR False, FRONTEND_URL=https://staging.example.com)
        → FRONTEND_URL + localhost when DEBUG=True

  prod  (DEBUG=False, FRONTEND_URL=https://example.com)
        → FRONTEND_URL only; wildcard (*) is stripped unconditionally

Call build_cors_origins() to get the concrete list to pass to CORSMiddleware.
"""

_DEV_ORIGINS: list[str] = [
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:3000",
]


def build_cors_origins(
    debug: bool,
    frontend_url: str = "",
    extra_origins: list[str] | None = None,
) -> list[str]:
    """
    Return the deduplicated list of allowed CORS origins.

    Args:
        debug:          True in development / staging with local frontend.
        frontend_url:   Canonical frontend URL (e.g. https://re-expert.app).
                        Required in production; optional in dev.
        extra_origins:  Additional origins to allow (e.g. CDN preview URLs).

    Production guarantee: '*' is never returned when debug=False.
    """
    seen: set[str] = set()
    allowed: list[str] = []

    def _add(origin: str) -> None:
        o = origin.strip().rstrip("/")
        if o and o not in seen:
            seen.add(o)
            allowed.append(o)

    if frontend_url:
        _add(frontend_url)

    if debug:
        for o in _DEV_ORIGINS:
            _add(o)

    for o in (extra_origins or []):
        _add(o)

    # Hard safety: wildcard must never reach the CORS middleware in production.
    if not debug:
        allowed = [o for o in allowed if o != "*"]

    return allowed
