# Deployment — RE Expert

Cómo se deploya el sistema y qué variables necesita.

## Mapa de hosting

| Componente | Proveedor | Cómo deploya |
|---|---|---|
| Backend API | Railway | Auto-deploy desde `main` vía integración GitHub |
| Frontend | Netlify (pendiente conectar) | Auto-deploy desde `main` |
| DB + Auth + Storage | Supabase | Gestionado (no deployamos nada) |
| CI (lint + tests) | GitHub Actions | Corre en cada PR y en push a `main` |

## Flujo de un cambio

```
feat/mi-cambio  →  PR a main  →  GitHub Actions (ruff + pytest)
                                           │
                                    ✅ merge a main
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
                Railway redeploy backend            Netlify redeploy frontend
                   (corre Alembic                   (publica estáticos)
                    preDeployCommand)
```

## Variables de entorno requeridas (backend — Railway)

Ver `backend/.env.example`. Todas son obligatorias excepto las marcadas.

| Variable | Dónde se usa | De dónde sacarla |
|---|---|---|
| `ANTHROPIC_API_KEY` | `services/anthropic_service.py` | https://console.anthropic.com |
| `DATABASE_URL` | SQLAlchemy + Alembic | Supabase → Project Settings → Database → Connection string (pooler, transaction mode, URI con `+asyncpg`) |
| `JWT_SECRET` | `core/auth.py` (verifica JWT de Supabase) | Supabase → Project Settings → API → JWT Secret |
| `SUPABASE_URL` | `services/knowledge_storage.py` | Supabase → Project Settings → API → URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Ídem (backend-only, nunca al front) | Supabase → Project Settings → API → service_role key |
| `ANTHROPIC_MODEL` | Modelo a usar (default `claude-sonnet-4-6-20250514`) | Opcional |
| `CORS_ORIGINS` | CORS middleware | Opcional (default: localhost) |
| `STRIPE_KEY` | Pendiente integrar billing | Opcional |

> ⚠️ **La `service_role_key` salta RLS.** Nunca exponerla al frontend.

## Variables del frontend

El frontend solo necesita variables **públicas** (cualquiera puede verlas en el navegador):
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` — la clave `anon`, **no** `service_role`.

Están en `frontend/config.js`. Es seguro comitearlas porque la seguridad la da RLS en la DB.

## Migraciones Alembic

- Cada PR con cambios de modelo debe incluir una migración nueva en `backend/alembic/versions/`.
- Railway corre `alembic upgrade head` antes del deploy (configurado en `railway.json` → `preDeployCommand`).
- Si la migración falla, Railway aborta el deploy y deja la versión anterior corriendo.
- Para correr local: `cd backend && alembic upgrade head`.

## Rollback

- **Backend:** en Railway → Deployments → click en el deploy anterior → Redeploy.
- **DB:** `alembic downgrade -1` (solo si la migración es reversible — las que tocan datos **no** lo son).
- **Frontend:** redeploy del commit anterior desde Netlify.

## Healthchecks

- `GET /health` → `{"status":"ok","version":"x.y.z"}`. Railway lo usa para decidir si el deploy es saludable.

## Primer deploy desde cero (si hay que rearmar todo)

1. Crear proyecto en Supabase → copiar URL + anon key + service_role key + JWT secret + DB connection string.
2. Crear bucket `knowledge` en Supabase Storage (público NO, service_role lo accede).
3. Crear proyecto en Railway → conectar repo → apuntar a `backend/` → setear variables de entorno.
4. Primer deploy corre Alembic y crea las tablas.
5. Crear proyecto en Netlify → conectar repo → build command vacío, publish directory `frontend/`.
