"""
Smoke test contra PRODUCCIÓN — read-only. No crea datos ni gasta tokens.

Verifica que el deploy está sano y que la autenticación está enforced. Pensado
para correr post-deploy, a mano o en CI:

    python tests/smoke_prod.py

NO se colecta con pytest (el nombre no empieza con `test_`) a propósito: depende
de red y no debe romper la suite unitaria offline.

URLs override por env var:
  RE_BACKEND_URL   (default: Railway prod)
  RE_FRONTEND_URL  (default: Netlify prod)
"""
import json
import os
import sys
import urllib.error
import urllib.request

BACKEND = os.environ.get(
    "RE_BACKEND_URL", "https://re-expert-production.up.railway.app"
).rstrip("/")
FRONTEND = os.environ.get("RE_FRONTEND_URL", "https://re-expert.netlify.app").rstrip("/")
TIMEOUT = 30  # generoso: Railway puede estar en cold-start

_ok = 0
_fail = 0


def _get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "re-expert-smoke/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return -1, str(e)


def check(name: str, cond: bool, detail: str = "") -> None:
    global _ok, _fail
    if cond:
        _ok += 1
        print(f"  ok   {name}")
    else:
        _fail += 1
        print(f"  FAIL {name} {detail}")


def main() -> None:
    print(f"Backend:  {BACKEND}")
    print(f"Frontend: {FRONTEND}\n")

    # ── Health ──
    st, body = _get(f"{BACKEND}/health")
    check("/health 200", st == 200, f"(got {st})")
    try:
        check("/health status=ok", json.loads(body).get("status") == "ok")
    except Exception:
        check("/health status=ok", False, "(body no es JSON)")

    st, _ = _get(f"{BACKEND}/health/db")
    check("/health/db 200 (DB viva)", st == 200, f"(got {st})")
    st, _ = _get(f"{BACKEND}/health/ready")
    check("/health/ready 200", st == 200, f"(got {st})")

    # ── OpenAPI: endpoints clave registrados ──
    st, body = _get(f"{BACKEND}/openapi.json")
    check("/openapi.json 200", st == 200, f"(got {st})")
    try:
        paths = set(json.loads(body).get("paths", {}))
    except Exception:
        paths = set()
    for p in (
        "/api/chat",
        "/api/auth/login",
        "/api/workspaces",
        "/api/profile",
        "/api/payments",
        "/api/news",
        "/api/academia/courses",
    ):
        check(f"openapi expone {p}", p in paths)

    # ── Auth enforced: protegidos sin token → 401 ──
    for p in ("/api/workspaces", "/api/profile", "/api/conversations", "/api/usage"):
        st, _ = _get(f"{BACKEND}{p}")
        check(f"{p} sin token -> 401", st == 401, f"(got {st})")

    # ── Frontend sirviendo la build con las features nuevas ──
    st, body = _get(f"{FRONTEND}/app.html")
    check("frontend /app.html 200", st == 200, f"(got {st})")
    check("frontend trae loadNewsDestacadas (build al día)", "loadNewsDestacadas" in body)

    print(f"\n{_ok} ok, {_fail} fail")
    sys.exit(1 if _fail else 0)


if __name__ == "__main__":
    main()
