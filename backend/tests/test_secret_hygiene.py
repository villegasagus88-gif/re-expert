"""
Static guard tests for secret hygiene.

These tests scan the repo to ensure secrets never sneak into client-side
code or get logged. They run as part of the normal pytest suite and fail
the build the moment a leak is introduced.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "frontend"
BACKEND_DIR = REPO_ROOT / "backend"

# Anthropic key prefix per their docs.
ANTHROPIC_KEY_RE = re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")
# Stripe live/test keys
STRIPE_KEY_RE = re.compile(r"sk_(live|test)_[A-Za-z0-9]{24,}")

# Tokens that should not appear in any committed frontend asset.
FORBIDDEN_FRONTEND_TOKENS = (
    "ANTHROPIC_API_KEY",
    "anthropic_api_key",
    "STRIPE_SECRET_KEY",
    "JWT_SECRET",
    "SUPABASE_SERVICE_ROLE_KEY",
)

# Files we don't want to scan (binary or generated).
SKIP_DIR_NAMES = {".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache"}


def _is_local_dotenv(path: Path) -> bool:
    """True para `.env` / `.env.local` etc — secretos LOCALES gitignored.

    Estos archivos contienen las claves reales del dev y nunca se commitean
    (lo garantiza test_gitignore_protects_env_files). Escanearlos produce
    falsos positivos en la máquina del dev. `.env.example` (template commiteado)
    NO se saltea: ese sí debe estar libre de claves reales.
    """
    n = path.name
    return n == ".env" or (n.startswith(".env.") and n != ".env.example")


def _walk(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if _is_local_dotenv(path):
            continue
        yield path


# ----------------------------------------------------------------- frontend --

def test_no_secret_env_names_in_frontend():
    """Frontend must never reference backend env-var names."""
    if not FRONTEND_DIR.exists():
        pytest.skip("frontend dir not present")
    leaks: list[tuple[str, str]] = []
    for path in _walk(FRONTEND_DIR):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for token in FORBIDDEN_FRONTEND_TOKENS:
            if token in text:
                leaks.append((str(path.relative_to(REPO_ROOT)), token))
    assert not leaks, f"Forbidden secret tokens leaked into frontend: {leaks}"


# --------------------------------------------------------- repo-wide leaks --

def test_no_anthropic_key_committed_anywhere():
    """No real Anthropic key (sk-ant-...) should appear in any tracked file."""
    leaks: list[str] = []
    for path in _walk(REPO_ROOT):
        # Skip the test file itself (it contains the regex pattern).
        if path.name == "test_secret_hygiene.py":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in ANTHROPIC_KEY_RE.finditer(text):
            leaks.append(f"{path.relative_to(REPO_ROOT)}: {m.group(0)[:14]}…")
    assert not leaks, f"Anthropic API key found in committed files: {leaks}"


def test_no_stripe_key_committed_anywhere():
    """No Stripe sk_live_/sk_test_ key (with real-looking suffix) in repo."""
    leaks: list[str] = []
    for path in _walk(REPO_ROOT):
        if path.name == "test_secret_hygiene.py":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in STRIPE_KEY_RE.finditer(text):
            leaks.append(f"{path.relative_to(REPO_ROOT)}: {m.group(0)[:18]}…")
    assert not leaks, f"Stripe secret key found in committed files: {leaks}"


# ---------------------------------------------------------- backend logging --

def test_backend_does_not_log_settings_object():
    """No backend module passes the whole `settings` object into a log/print call.

    Uses AST to avoid false positives where the literal word "settings"
    appears inside a string. Allowed: `logger.info(settings.PORT)` (single
    field access). Blocked: `logger.info(settings)`, `print(settings.dict())`,
    `logger.info("env=%s", settings)`.
    """
    import ast

    leaks: list[tuple[str, int, str]] = []

    def is_bare_settings(node) -> bool:
        # `settings` (whole object)
        return isinstance(node, ast.Name) and node.id == "settings"

    def is_settings_dump(node) -> bool:
        # `settings.dict()` / `settings.model_dump()` / `repr(settings)`
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and is_bare_settings(f.value):
                if f.attr in {"dict", "model_dump", "json"}:
                    return True
            if isinstance(f, ast.Name) and f.id in {"repr", "vars", "str"}:
                return any(is_bare_settings(a) for a in node.args)
        return False

    def is_log_or_print(call: ast.Call) -> bool:
        f = call.func
        if isinstance(f, ast.Name) and f.id == "print":
            return True
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            if f.value.id == "logger" and f.attr in {
                "debug", "info", "warning", "error", "critical", "exception",
            }:
                return True
        return False

    for path in _walk(BACKEND_DIR):
        if path.suffix != ".py":
            continue
        if path.name == "test_secret_hygiene.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not is_log_or_print(node):
                continue
            for arg in [*node.args, *(kw.value for kw in node.keywords)]:
                if is_bare_settings(arg) or is_settings_dump(arg):
                    leaks.append(
                        (
                            str(path.relative_to(REPO_ROOT)),
                            node.lineno,
                            ast.unparse(node)[:120],
                        )
                    )
    assert not leaks, f"Code logs/prints whole settings object: {leaks}"


# -------------------------------------------------------------- gitignore --

def test_gitignore_protects_env_files():
    """`.env` (and common variants) must be in .gitignore."""
    gi = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    required_patterns = [".env", ".env.*", "**/.env"]
    missing = [p for p in required_patterns if p not in gi]
    assert not missing, f".gitignore is missing patterns: {missing}"
