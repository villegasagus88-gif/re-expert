"""
upload_knowledge.py — Sube archivos de knowledge/ al bucket de Supabase Storage.

Uso:
    cd "ChatBotAi Real State"
    python scripts/upload_knowledge.py

Requiere:
    - backend/.env con SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY configurados
    - httpx y python-dotenv instalados (ya están en requirements.txt)
"""

import sys
import mimetypes
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependencias
# ---------------------------------------------------------------------------
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
ROOT_DIR    = Path(__file__).parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
ENV_FILE    = ROOT_DIR / "backend" / ".env"
BUCKET_NAME = "knowledge"

ALLOWED_EXTENSIONS = {".md", ".csv", ".txt", ".json", ".pdf", ".docx", ".xlsx"}

# ---------------------------------------------------------------------------
# Carga de variables de entorno
# ---------------------------------------------------------------------------
def load_config() -> dict:
    if not ENV_FILE.exists():
        sys.exit(f"ERROR: No encontré el archivo .env en {ENV_FILE}")

    config = dotenv_values(ENV_FILE)

    url = config.get("SUPABASE_URL", "").strip()
    key = config.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not url or url == "your-supabase-url":
        sys.exit("ERROR: SUPABASE_URL no está configurada en backend/.env")
    if not key or key == "your-service-role-key":
        sys.exit("ERROR: SUPABASE_SERVICE_ROLE_KEY no está configurada en backend/.env")

    return {"url": url.rstrip("/"), "key": key}


# ---------------------------------------------------------------------------
# Helpers de API
# ---------------------------------------------------------------------------
def make_headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "apikey": key,
    }


def create_bucket(client: httpx.Client, url: str, key: str) -> None:
    """Crea el bucket si no existe. Ignora el error si ya existe."""
    resp = client.post(
        f"{url}/storage/v1/bucket",
        headers={**make_headers(key), "Content-Type": "application/json"},
        json={"id": BUCKET_NAME, "name": BUCKET_NAME, "public": False},
    )
    if resp.status_code == 200:
        print(f"  ✓ Bucket '{BUCKET_NAME}' creado.")
    elif resp.status_code == 409 or "already exists" in resp.text.lower():
        print(f"  · Bucket '{BUCKET_NAME}' ya existe, continuando.")
    else:
        sys.exit(f"ERROR al crear bucket: {resp.status_code} — {resp.text}")


def upload_file(client: httpx.Client, url: str, key: str, file_path: Path) -> bool:
    """Sube un archivo. Retorna True si tuvo éxito."""
    content = file_path.read_bytes()
    mime_type, _ = mimetypes.guess_type(file_path.name)
    if mime_type is None:
        mime_type = "text/plain"

    # Intentamos upsert (update si existe, insert si no)
    upload_url = f"{url}/storage/v1/object/{BUCKET_NAME}/{file_path.name}"

    resp = client.post(
        upload_url,
        headers={
            **make_headers(key),
            "Content-Type": mime_type,
            "x-upsert": "true",          # sobrescribe si ya existe
        },
        content=content,
        timeout=30.0,
    )

    if resp.status_code in (200, 201):
        size_kb = len(content) / 1024
        print(f"  ✓ {file_path.name} ({size_kb:.1f} KB)")
        return True
    else:
        print(f"  ✗ {file_path.name} — Error {resp.status_code}: {resp.text}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 55)
    print("  RE Expert — Upload de Knowledge Base a Supabase")
    print("=" * 55)

    # Valida entorno
    config = load_config()
    print(f"\nURL: {config['url']}")
    print(f"Bucket: {BUCKET_NAME}\n")

    # Busca archivos
    files = [
        f for f in KNOWLEDGE_DIR.iterdir()
        if f.is_file() and f.suffix in ALLOWED_EXTENSIONS
    ]

    if not files:
        sys.exit(f"No encontré archivos en {KNOWLEDGE_DIR}")

    print(f"Archivos a subir: {len(files)}")
    for f in files:
        print(f"  - {f.name}")
    print()

    # Ejecuta
    with httpx.Client() as client:
        print("→ Verificando bucket...")
        create_bucket(client, config["url"], config["key"])

        print("\n→ Subiendo archivos...")
        ok = 0
        fail = 0
        for file_path in sorted(files):
            if upload_file(client, config["url"], config["key"], file_path):
                ok += 1
            else:
                fail += 1

    # Resumen
    print()
    print("=" * 55)
    print(f"  Resultado: {ok} OK  |  {fail} errores")
    print("=" * 55)

    if fail > 0:
        sys.exit(1)

    print("\n¡Listo! Los archivos están disponibles en Supabase Storage.")
    print(f"Verificá en: {config['url'].replace('https://', 'https://app.supabase.com/project/')}/storage/buckets")


if __name__ == "__main__":
    main()
