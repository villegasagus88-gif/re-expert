"""Tests for auto-title derivation from the first user message."""
from api.routes.chat import _derive_title


def test_derive_title_short_message_returned_as_is():
    assert _derive_title("Hola, qué tal?") == "Hola, qué tal?"


def test_derive_title_collapses_whitespace():
    assert _derive_title("  Hola   mundo  \n\n  ") == "Hola mundo"


def test_derive_title_empty_returns_default():
    assert _derive_title("") == "Nueva conversación"
    assert _derive_title("   \n  ") == "Nueva conversación"


def test_derive_title_truncates_long_message():
    long_msg = "a" * 100
    title = _derive_title(long_msg)
    assert title.endswith("…")
    # Prefijo de 60 + "…"
    assert len(title) == 61


def test_derive_title_respects_word_boundary_when_truncating():
    msg = (
        "Necesito un presupuesto detallado para construir una casa de tres dormitorios"
        " en un terreno de 300m2 en Pilar"
    )
    title = _derive_title(msg, max_len=40)
    assert title.endswith("…")
    # No debería cortar en mitad de palabra si hay un espacio disponible
    # después del midpoint.
    assert not title[:-1].endswith("c")  # e.g. no "constru…"
    assert " " not in title[-3:]  # sin espacio justo antes del …


def test_derive_title_honors_custom_max_len():
    assert _derive_title("abcdefghij", max_len=100) == "abcdefghij"
    out = _derive_title("abcdefghij", max_len=5)
    assert out == "abcde…"
