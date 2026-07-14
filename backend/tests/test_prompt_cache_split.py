"""Split del system prompt del chat en bloques de cache (dominio Agus).

Garantiza que el particionado NO cambia lo que ve el modelo: la concatenación de
los bloques text es BYTE-IDÉNTICA al system original. Solo cambia el caching.
"""
import services.anthropic_service as a


def test_split_reconstruye_identico_y_estructura():
    base = a.BASE_SYSTEM_PROMPT
    extra = "\n\n## Sobre el usuario\n- rol: dev\n\n## Base de conocimiento\n\n" + "x" * 200
    system = base + extra

    out = a._system_with_cache(system)
    # Dos bloques, ambos con cache_control ephemeral; el 1º es el BASE estable.
    assert isinstance(out, list) and len(out) == 2
    assert out[0]["text"] == base
    assert out[0]["cache_control"] == {"type": "ephemeral"}
    assert out[1]["cache_control"] == {"type": "ephemeral"}
    # BYTE-IDÉNTICO: bloque1 + bloque2 == system original (sin separador extra).
    assert out[0]["text"] + out[1]["text"] == system


def test_system_chico_devuelve_string_sin_cache():
    # Debajo del umbral → string plano, comportamiento anterior.
    assert a._system_with_cache("hola corto") == "hola corto"


def test_system_largo_sin_base_es_un_solo_bloque():
    # Un prompt largo que NO arranca con BASE (ej: SOL) → un bloque, como antes.
    system = "PROMPT DISTINTO — SOL intake\n\n" + "y" * 5000
    out = a._system_with_cache(system)
    assert isinstance(out, list) and len(out) == 1
    assert out[0]["text"] == system
    assert out[0]["cache_control"] == {"type": "ephemeral"}
