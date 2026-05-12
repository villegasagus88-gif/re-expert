#!/usr/bin/env python3
"""
verify_routing.py — verificación offline del pipeline de routing del chat.

Para cada query representativa:
  1. Corre classify_query / classify_query_multi (sin red).
  2. Resuelve a qué carpeta del repo `knowledge/` mapea.
  3. Confirma que la carpeta exista y tenga contenido.
  4. Reporta PASS si el dominio esperado matchea, FAIL en otro caso.

Uso:
    python scripts/verify_routing.py

No requiere Supabase ni JWT — solo dependencias estándar del backend.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

# Permitir import de services.* sin instalar el paquete.
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

# El backend usa sintaxis 3.10+ (list[str] | None) en config/core. Para correr
# este verificador con 3.9 local, stubeamos las deps que no necesita el router.
# El router solo usa knowledge_base._tokenize y knowledge_base (instancia) —
# y para classify_query/classify_query_multi alcanza con _tokenize.
_fake_settings = types.ModuleType("config.settings")
_fake_settings.settings = types.SimpleNamespace(  # type: ignore[attr-defined]
    SUPABASE_URL="", SUPABASE_SERVICE_ROLE_KEY=""
)
_fake_config = types.ModuleType("config")
sys.modules.setdefault("config", _fake_config)
sys.modules.setdefault("config.settings", _fake_settings)

_fake_storage_mod = types.ModuleType("services.knowledge_storage")
_fake_storage_mod.knowledge_storage = types.SimpleNamespace()  # type: ignore[attr-defined]
sys.modules.setdefault("services.knowledge_storage", _fake_storage_mod)

from services.context_router import (  # noqa: E402
    DOMAIN_TO_FOLDER,
    classify_query,
    classify_query_multi,
)

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"

# (query, dominio_esperado) — battery diseñada para cubrir todos los frentes
# del KB. El dominio esperado puede ser None si solo queremos ver dónde cae.
CASES: list[tuple[str, str | None]] = [
    ("¿Cuánto cuesta el m2 de construcción en CABA hoy?", "costos"),
    ("Quiero saber el precio del acero y el hormigón este mes", "arquitectura"),
    ("Qué dice el código urbanístico CABA sobre FOT y FOS", "normativa"),
    ("Cómo armo un waterfall para inversores del fideicomiso", "financiero"),
    ("Tasa del crédito hipotecario UVA en mayo 2026", "financiero"),
    ("Qué dice la Ley 27551 de alquileres", "normativa"),
    ("IVA en obra inmueble propio: cómo se computa", "impuestos"),
    ("Distrito Tecnológico CABA: qué beneficios da", "estrategia"),
    ("Cap rate promedio multifamiliar en Palermo", "mercado"),
    ("Net zero embodied carbon en obra nueva", "triple-impacto"),
    ("Cómo se hace una tasación previa al lanzamiento", "tasacion"),
    ("Riesgos UIF en blanqueo de capitales inmobiliario", "uif"),
    ("CNV oferta pública de fideicomisos financieros", "cnv-bcra"),
    ("Seguro de caución y todo riesgo construcción", "seguros"),
    ("Caso de estudio LEED en Argentina", "casos"),
    ("Customer journey postcompra: qué incluye", "comercial"),
    ("Qué hace un developer inmobiliario", "fundamentos"),
    ("Inflación, brecha y dólar MEP impacto en obra", "macro"),
    ("Aportes UOCRA y convenio colectivo", "laboral"),
    ("PropTech: qué stack usan los grandes en AR", "tecnologia"),
    ("Boleto de compraventa y escritura: qué prevalece", "suelo-dominio"),
    ("Hola, ¿cómo estás?", "general"),
]


def folder_files(folder: str) -> list[str]:
    """Lista archivos del repo (no del bucket) en una carpeta del KB."""
    if not folder:
        return []
    base = KNOWLEDGE_DIR / folder
    if not base.exists():
        return []
    return [
        p.name
        for p in base.rglob("*")
        if p.is_file() and p.suffix.lower() in {".md", ".csv", ".yaml", ".yml", ".txt"}
    ]


def main() -> int:
    print(f"KB dir: {KNOWLEDGE_DIR}")
    print(f"Casos: {len(CASES)}\n")
    print(f"{'#':>2}  {'EXP':<14} {'GOT':<14} {'MULTI':<32} {'FILES':>5}  STATUS  QUERY")
    print("-" * 130)

    passed = 0
    failed = 0
    empty_folders: set[str] = set()

    for i, (query, expected) in enumerate(CASES, 1):
        got = classify_query(query)
        multi = classify_query_multi(query, top_n=3)
        folder = DOMAIN_TO_FOLDER.get(got, "")
        files = folder_files(folder)
        if folder and not files:
            empty_folders.add(folder)

        is_pass = expected is None or got == expected or (expected in multi)
        status = "PASS" if is_pass else "FAIL"
        if is_pass:
            passed += 1
        else:
            failed += 1

        multi_str = ",".join(multi) if multi else "-"
        if len(multi_str) > 30:
            multi_str = multi_str[:29] + "…"
        print(
            f"{i:>2}  {expected or '-':<14} {got:<14} {multi_str:<32} {len(files):>5}  {status:<6}  {query[:60]}"
        )

    print("-" * 130)
    print(f"\nResultado: {passed} PASS / {failed} FAIL de {len(CASES)} casos.")

    if empty_folders:
        print("\n⚠  Carpetas matcheadas SIN archivos en el repo:")
        for f in sorted(empty_folders):
            print(f"   - {f}")

    # Sanity: meta tiene baseline
    meta_files = folder_files(DOMAIN_TO_FOLDER["meta"])
    print(f"\n_meta/ tiene {len(meta_files)} archivos: {', '.join(sorted(meta_files)) or '(vacío!)'}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
