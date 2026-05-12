# Sync del Knowledge Base → Supabase Storage

Este documento explica cómo viaja un archivo desde `knowledge/` en el repo
hasta el bucket `knowledge` de Supabase, y cómo el chat lo consume.

## Flujo

```
knowledge/                       scripts/upload_knowledge.py        Supabase Storage
  XX-tema/*.md/.csv/.yaml   ─►   diff por MD5 vs ETag        ─►     bucket `knowledge`
                                  upload | update | skip | prune                │
                                                                                ▼
                                                       knowledge_storage.list_files(recursive=True)
                                                                                │
                                                                                ▼
                                                       services/context_router.py
                                                       (meta baseline + top-K por dominio)
                                                                                │
                                                                                ▼
                                                       services/anthropic_service.py
                                                       build_system_prompt(...)
                                                                                │
                                                                                ▼
                                                       Claude API (system prompt acotado)
```

## Comando de sync

```bash
# Modo seguro: muestra qué pasaría, sin tocar el bucket
python scripts/upload_knowledge.py --dry-run

# Sube lo nuevo + actualiza lo modificado (compara MD5 vs ETag remoto)
python scripts/upload_knowledge.py

# Además borra del bucket lo que ya no exista en el repo
python scripts/upload_knowledge.py --prune

# Fuerza re-upload aunque el hash coincida (cache busting)
python scripts/upload_knowledge.py --force
```

Variables requeridas: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.

## Extensiones soportadas

`.md`, `.csv`, `.txt`, `.json`, `.yaml`, `.yml`.

Para que un archivo entre al contexto del chat, además de subirlo debe ser
leído por `load_knowledge_context()` / `KnowledgeBaseService.load_all()`,
que filtran por extensión. Si agregás un nuevo tipo, actualizá esos filtros.

## Runtime

- `knowledge_storage.list_files()` recorre el bucket recursivamente vía BFS
  sobre el endpoint `POST /storage/v1/object/list/<bucket>` (Supabase no
  expone listado recursivo nativo).
- `KnowledgeBaseService` cachea documentos parseados con TTL de 1h
  (configurable). El cache se invalida automáticamente al expirar.
- `context_router.select_context_for_message()` clasifica la pregunta y
  arma el contexto en dos capas: meta baseline (`_meta/`) + top-K docs del
  dominio matcheado. Budget total: 14k tokens.

## Troubleshooting

- **Archivo no aparece en el chat**: confirmá con `--dry-run` que esté
  marcado UPLOAD/UPDATE. Si dice SKIP es que el hash ya coincide.
- **Sigo sin verlo**: limpiá el cache vía `DELETE /api/knowledge/cache` o
  esperá la expiración del TTL.
- **Lista vacía pero el bucket tiene archivos**: el bucket usa RLS; el
  servicio del backend usa `SUPABASE_SERVICE_ROLE_KEY` que bypassea RLS.
  Asegurate de tener esa env var seteada en el deploy.
