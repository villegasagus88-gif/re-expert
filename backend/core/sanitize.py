"""
Input sanitization utilities — defence-in-depth for all user-supplied text.

Three transformation levels:

  strip_html(s)   – remove HTML/script tags (XSS prevention for stored fields)
  sanitize_str(v) – strip_html + whitespace trim + control-char removal
  clean_text(v)   – whitespace + control-char removal only (AI prompt fields
                    where HTML-like text is legitimate user input)

Pydantic annotated types derived from these are imported by all request
schemas so every incoming payload is sanitized automatically before any
business logic or DB write runs.
"""
import re
from typing import Annotated

from pydantic import BeforeValidator

# Matches anything that looks like an HTML/XML tag
_HTML_RE = re.compile(r"<[^>]*>", re.DOTALL)

# ASCII control chars except \t (0x09), \n (0x0A), \r (0x0D)
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip_html(text: str) -> str:
    """Remove all HTML/script tags from *text*."""
    return _HTML_RE.sub("", text)


def sanitize_str(v: object) -> object:
    """
    Full sanitization for labels / short text stored and displayed in UI:
      1. strip leading/trailing whitespace
      2. remove ASCII control characters (null bytes, etc.)
      3. strip HTML tags
    """
    if not isinstance(v, str):
        return v
    v = v.strip()
    v = _CTRL_RE.sub("", v)
    v = strip_html(v)
    return v


def clean_text(v: object) -> object:
    """
    Light sanitization for free-form text (AI chat messages, notes) where
    HTML-like strings are valid user input.  Strips whitespace and control
    characters but does NOT remove angle-bracket content.
    """
    if not isinstance(v, str):
        return v
    v = v.strip()
    v = _CTRL_RE.sub("", v)
    return v


def _opt_sanitize(v: object) -> object:
    return sanitize_str(v) if isinstance(v, str) else v


def _opt_clean(v: object) -> object:
    return clean_text(v) if isinstance(v, str) else v


# ── Pydantic annotated types ─────────────────────────────────────────────────

# For UI labels, names, addresses — any field rendered in HTML
SanitizedStr = Annotated[str, BeforeValidator(sanitize_str)]
SanitizedOptStr = Annotated[str | None, BeforeValidator(_opt_sanitize)]

# For chat/notes — preserves angle brackets, still blocks null bytes
CleanText = Annotated[str, BeforeValidator(clean_text)]
CleanOptText = Annotated[str | None, BeforeValidator(_opt_clean)]
