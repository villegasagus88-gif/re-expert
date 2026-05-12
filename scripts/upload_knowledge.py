"""
upload_knowledge.py — Sincroniza knowledge/ con el bucket Supabase Storage.

Recorre recursivamente knowledge/, preserva la estructura de carpetas
(00-fundamentos/foo.md → 00-fundamentos/foo.md en el bucket), y solo
sube archivos cuyo contenido cambió (chequeo por hash MD5 contra el
ETag del bucket).

Uso:
    cd "Chat experto en REAL STATE"
    python scripts/upload_knowledge.py              # sync normal
    python scripts/upload_knowledge.py --dry-run    # ver qué haría sin tocar
    python scripts/upload_knowledge.py --prune      # borra huérfanos del bucket
    python scripts/upload_knowledge.py --force      # re-sube todo aunque coincida hash

Requiere:
    - backend/.env con SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY
    - httpx y python-dotenv instalados (requirements.txt)
"""

from __future__ import annotations

import argparse
import hashlib
import mimetypes
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import httpx
except ImportError:
    sys.exit("ERROR: httpx no instalado. Corré: pip install httpx")

try:
    from dotenv import dotenv_values
except ImportError:
    sys.exit("ERROR: python-dotenv no instalado. Corré: pip install python-dotenv")


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
ENV_FILE = ROOT_DIR / "backend" / ".env"
BUCKET_NAME = "knowledge"

# Extensiones que el chat puede consumir como texto plano.
ALLOWED_EXTENSIONS = {".md", ".csv", ".txt", ".json", ".yaml", ".yml"}

# Carpetas/archivos que nunca se suben.
SKIP_NAMES = {".DS_Store", "Thumbs.db", ".gitkeep"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv"}


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------
@dataclass
class LocalFile:
    rel_path: str   # ej: "_meta/indice-rapido.md"
    abs_path: Path
    size: int
    md5: str


@dataclass
class RemoteFile:
    path: str
    size: int
    etag: str | None  # el ETag de Supabase Storage es el MD5 cuando es subida simple


# ---------------------------------------------------------------------------
# Carga de configuración
# ---------------------------------------------------------------------------
def load_config() -> dict:
    if not ENV_FILE.exists():
        sys.exit(f"ERROR: no encontré {ENV_FILE}")
    config = dotenv_values(ENV_FILE)
    url = (config.get("SUPABASE_URL") or "").strip()
    key = (config.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not url or url == "your-supabase-url":
        sys.exit("ERROR: SUPABASE_URL no está configurada en backend/.env")
    if not key or key == "your-service-role-key":
        sys.exit("ERROR: SUPABASE_SERVICE_ROLE_KEY no está configurada en backend/.env")
    return {"url": url.rstrip("/"), "key": key}


def make_headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "apikey": key}


# ---------------------------------------------------------------------------
# Lectura local
# ---------------------------------------------------------------------------
def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_local_files() -> list[LocalFile]:
    files: list[LocalFile] = []
    for path in KNOWLEDGE_DIR.rglob("*"):
        if not path.is_file():
            continue
        # Skip por directorio
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        # Skip por nombre
        if path.name in SKIP_NAMES:
            continue
        # Skip por extensión
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        rel = path.relative_to(KNOWLEDGE_DIR).as_posix()
        files.append(LocalFile(
            rel_path=rel,
            abs_path=path,
            size=path.stat().st_size,
            md5=md5_of(path),
        ))
    return files


# ---------------------------------------------------------------------------
# Lectura remota
# ---------------------------------------------------------------------------
def list_remote_one_level(
    client: httpx.Client, base_url: str, key: str, prefix: str
) -> list[dict]:
    resp = client.post(
        f"{base_url}/storage/v1/object/list/{BUCKET_NAME}",
        headers={**make_headers(key), "Content-Type": "application/json"},
        json={"prefix": prefix, "limit": 1000, "offset": 0,
              "sortBy": {"column": "name", "order": "asc"}},
        timeout=20.0,
    )
    if resp.status_code != 200:
        sys.exit(f"ERROR listando bucket: {resp.status_code} — {resp.text}")
    return resp.json()


def list_remote_recursive(
    client: httpx.Client, base_url: str, key: str
) -> list[RemoteFile]:
    """BFS por niveles. Supabase Storage no expone listado recursivo nativo."""
    results: list[RemoteFile] = []
    queue: list[str] = [""]
    visited: set[str] = set()

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        items = list_remote_one_level(client, base_url, key, current)
        for item in items:
            name = item.get("name", "")
            if not name:
                continue
            full = f"{current}/{name}".strip("/") if current else name
            if item.get("id") is None:
                # Subcarpeta
                queue.append(full)
                continue
            meta = item.get("metadata") or {}
            etag = (meta.get("eTag") or "").strip('"') or None
            results.append(RemoteFile(
                path=full,
                size=meta.get("size", 0),
                etag=etag,
            ))
    return results


# ---------------------------------------------------------------------------
# Upload / Delete
# ---------------------------------------------------------------------------
def upload_file(
    client: httpx.Client, base_url: str, key: str, lf: LocalFile
) -> tuple[bool, str]:
    """Sube un archivo con upsert. Devuelve (ok, mensaje_error_si_falla)."""
    mime, _ = mimetypes.guess_type(lf.abs_path.name)
    if mime is None:
        # Tratamos yaml como text/yaml para que el storage no lo marque binario
        if lf.abs_path.suffix.lower() in {".yaml", ".yml"}:
            mime = "text/yaml"
        else:
            mime = "text/plain"
    content = lf.abs_path.read_bytes()
    resp = client.post(
        f"{base_url}/storage/v1/object/{BUCKET_NAME}/{lf.rel_path}",
        headers={
            **make_headers(key),
            "Content-Type": mime,
            "x-upsert": "true",
        },
        content=content,
        timeout=30.0,
    )
    if resp.status_code in (200, 201):
        return True, ""
    return False, f"{resp.status_code}: {resp.text}"


def delete_file(
    client: httpx.Client, base_url: str, key: str, path: str
) -> tuple[bool, str]:
    resp = client.delete(
        f"{base_url}/storage/v1/object/{BUCKET_NAME}/{path}",
        headers=make_headers(key),
        timeout=20.0,
    )
    if resp.status_code in (200, 204):
        return True, ""
    return False, f"{resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Bucket (idempotente)
# ---------------------------------------------------------------------------
def ensure_bucket(client: httpx.Client, base_url: str, key: str) -> None:
    resp = client.post(
        f"{base_url}/storage/v1/bucket",
        headers={**make_headers(key), "Content-Type": "application/json"},
        json={"id": BUCKET_NAME, "name": BUCKET_NAME, "public": False},
        timeout=15.0,
    )
    if resp.status_code == 200:
        print(f"  Bucket '{BUCKET_NAME}' creado.")
    elif resp.status_code == 409 or "already exists" in resp.text.lower():
        pass  # existe, ok
    else:
        sys.exit(f"ERROR creando bucket: {resp.status_code} — {resp.text}")


# ---------------------------------------------------------------------------
# Plan de sync
# ---------------------------------------------------------------------------
@dataclass
class SyncPlan:
    to_upload: list[LocalFile]   # nuevos
    to_update: list[LocalFile]   # existen pero contenido cambió
    to_skip: list[LocalFile]     # idénticos por hash
    to_delete: list[str]         # remotos sin contraparte local (huérfanos)


def build_plan(
    local: list[LocalFile], remote: list[RemoteFile], force: bool
) -> SyncPlan:
    remote_by_path: dict[str, RemoteFile] = {r.path: r for r in remote}
    local_paths: set[str] = {lf.rel_path for lf in local}

    to_upload: list[LocalFile] = []
    to_update: list[LocalFile] = []
    to_skip: list[LocalFile] = []

    for lf in local:
        rf = remote_by_path.get(lf.rel_path)
        if rf is None:
            to_upload.append(lf)
        elif force:
            to_update.append(lf)
        elif rf.etag and rf.etag.lower() == lf.md5.lower():
            to_skip.append(lf)
        else:
            to_update.append(lf)

    to_delete = [rf.path for rf in remote if rf.path not in local_paths]
    return SyncPlan(to_upload, to_update, to_skip, to_delete)


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------
def print_plan(plan: SyncPlan, prune: bool) -> None:
    print(f"\n  Nuevos a subir: {len(plan.to_upload)}")
    for lf in plan.to_upload[:20]:
        print(f"    + {lf.rel_path}")
    if len(plan.to_upload) > 20:
        print(f"    ... ({len(plan.to_upload) - 20} más)")

    print(f"\n  A actualizar (contenido cambió): {len(plan.to_update)}")
    for lf in plan.to_update[:20]:
        print(f"    ~ {lf.rel_path}")
    if len(plan.to_update) > 20:
        print(f"    ... ({len(plan.to_update) - 20} más)")

    print(f"\n  Sin cambios (skip): {len(plan.to_skip)}")

    if plan.to_delete:
        if prune:
            print(f"\n  A BORRAR del bucket (huérfanos): {len(plan.to_delete)}")
            for p in plan.to_delete[:20]:
                print(f"    - {p}")
            if len(plan.to_delete) > 20:
                print(f"    ... ({len(plan.to_delete) - 20} más)")
        else:
            print(f"\n  Huérfanos en bucket (NO se borran sin --prune): {len(plan.to_delete)}")
            for p in plan.to_delete[:10]:
                print(f"    ! {p}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sincroniza knowledge/ con el bucket Supabase Storage.",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="No sube ni borra nada, solo muestra el plan.")
    parser.add_argument("--prune", action="store_true",
                        help="Borra archivos del bucket que no existen en el repo.")
    parser.add_argument("--force", action="store_true",
                        help="Re-sube todos los archivos aunque el hash coincida.")
    args = parser.parse_args()

    print("=" * 60)
    print("  RE Expert — Sync de Knowledge Base con Supabase Storage")
    print("=" * 60)

    config = load_config()
    print(f"\n  URL:    {config['url']}")
    print(f"  Bucket: {BUCKET_NAME}")
    print(f"  Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}"
          f"{' + PRUNE' if args.prune else ''}{' + FORCE' if args.force else ''}")

    print("\n  Escaneando archivos locales...")
    local = scan_local_files()
    print(f"  Locales encontrados: {len(local)}")
    if not local:
        sys.exit(f"  No hay archivos en {KNOWLEDGE_DIR}")

    with httpx.Client() as client:
        print("  Verificando bucket...")
        ensure_bucket(client, config["url"], config["key"])

        print("  Listando bucket actual (recursivo)...")
        remote = list_remote_recursive(client, config["url"], config["key"])
        print(f"  Remotos encontrados: {len(remote)}")

        plan = build_plan(local, remote, force=args.force)
        print_plan(plan, prune=args.prune)

        if args.dry_run:
            print("\n  DRY-RUN: no se aplica nada.")
            return

        print("\n  Aplicando cambios...")
        ok_up, fail_up = 0, 0
        for lf in plan.to_upload + plan.to_update:
            ok, err = upload_file(client, config["url"], config["key"], lf)
            if ok:
                ok_up += 1
            else:
                fail_up += 1
                print(f"    ✗ {lf.rel_path} — {err}")

        ok_del, fail_del = 0, 0
        if args.prune:
            for path in plan.to_delete:
                ok, err = delete_file(client, config["url"], config["key"], path)
                if ok:
                    ok_del += 1
                else:
                    fail_del += 1
                    print(f"    ✗ delete {path} — {err}")

    print("\n" + "=" * 60)
    print(f"  Resultado: subidos/actualizados OK={ok_up} FAIL={fail_up}")
    if args.prune:
        print(f"             borrados OK={ok_del} FAIL={fail_del}")
    print(f"             sin cambios={len(plan.to_skip)}")
    print("=" * 60)

    if fail_up > 0 or (args.prune and fail_del > 0):
        sys.exit(1)
    print("\n  Listo.")


if __name__ == "__main__":
    main()
