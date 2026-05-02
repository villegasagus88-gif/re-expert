# Manejo de Secrets — Tarea #47

Política de manejo de claves de API (Anthropic, Stripe, JWT, Supabase service-role).

## Reglas no negociables

1. **Las claves viven solo en el backend.** Nunca se incluyen en código de frontend, ni en bundles, ni en URLs, ni en logs, ni en mensajes de error que viajen al cliente.
2. **Solo entran al runtime vía variables de entorno** (`backend/.env` en local, Railway Variables en producción).
3. **Nunca se commitean al repositorio.** `.gitignore` cubre todas las variantes de `.env*` (excepto `.env.example`).
4. **Si una clave estuvo expuesta, se rota inmediatamente.** Ver flujo abajo.

## Auditoría actual del repo

Resultado de la auditoría manual + tests automáticos (al cierre de la tarea):

- Frontend: **0** referencias a `ANTHROPIC_API_KEY` o tokens equivalentes (`STRIPE_SECRET_KEY`, `JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`).
- Repo entero: **0** matches de `sk-ant-...` o `sk_(live|test)_...` en archivos commiteados.
- Backend: **0** llamadas que loggeen el objeto `settings` completo o un `settings.dict()` / `settings.model_dump()`.
- `.gitignore`: cubre `.env`, `.env.*`, `**/.env`, `**/.env.*`, exceptuando `.env.example`.

## Tests automáticos

`backend/tests/test_secret_hygiene.py` corre 5 guards en cada push:

| Test | Qué cubre |
|---|---|
| `test_no_secret_env_names_in_frontend` | El frontend no menciona nombres de env vars sensibles |
| `test_no_anthropic_key_committed_anywhere` | Regex `sk-ant-[A-Za-z0-9_-]{20,}` no aparece en ningún archivo |
| `test_no_stripe_key_committed_anywhere` | Regex `sk_(live\|test)_[A-Za-z0-9]{24,}` no aparece |
| `test_backend_does_not_log_settings_object` | AST scan: ningún `logger.X(settings)` o `print(settings)` o `settings.dict()/.model_dump()` en logs |
| `test_gitignore_protects_env_files` | `.gitignore` incluye `.env`, `.env.*`, `**/.env` |

## Dónde viven las claves

| Variable | Local | Producción | Usada en |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | `backend/.env` | Railway Variables | `services/anthropic_service.py` |
| `STRIPE_SECRET_KEY` | `backend/.env` | Railway Variables | `services/stripe_service.py` |
| `STRIPE_WEBHOOK_SECRET` | `backend/.env` | Railway Variables | `api/routes/stripe_routes.py` |
| `JWT_SECRET` | `backend/.env` | Railway Variables | `core/auth.py` |
| `SUPABASE_SERVICE_ROLE_KEY` | `backend/.env` | Railway Variables | `services/knowledge_storage.py` |
| `DATABASE_URL` | `backend/.env` | Railway Variables | `models/base.py` (asyncpg) |

## Flujo de rotación (clave expuesta)

Si una clave aparece en logs públicos, screenshots, commits, gists, etc.:

1. **Anthropic / Stripe / Supabase Console** → revocar la clave vieja.
2. Generar una clave nueva.
3. **Railway** → Project → Variables → editar el valor → **Deploy**.
4. Validar: `curl https://api.tu-dominio.app/health` (debe responder 200; si la app no levanta, la clave está mal).
5. Verificar uso: en Anthropic Console → "Usage" para confirmar que la nueva clave registra requests y la vieja no.
6. **Local**: cada dev actualiza su `backend/.env` desde el secret manager interno.
7. Si la clave estuvo en un commit público: `git rebase -i` no es suficiente (el blob queda en GitHub) → considerar `git filter-repo` o usar el endpoint de purga de GitHub support.

## Cómo agregar un nuevo secret

1. Agregarlo a `backend/.env.example` con valor placeholder claramente falso (`sk_test_...`, `your-secret-here`).
2. Agregarlo al modelo `Settings` en `backend/config/settings.py`.
3. Documentarlo en este archivo + en `docs/DEPLOYMENT.md`.
4. Si es sensible, agregarlo a la lista `FORBIDDEN_FRONTEND_TOKENS` en `tests/test_secret_hygiene.py`.

## Checklist (tarea #47)

- [x] Buscar refs ANTHROPIC en frontend → 0 matches
- [x] Verificar `.gitignore` incluye `.env` (y variantes)
- [x] Logs no imprimen la key (auditado + test AST)
- [x] Key solo en env vars del server (`services/anthropic_service.py:22`)
- [x] Rotar key si estuvo expuesta → flujo documentado arriba
- [x] Tests automáticos para prevenir regresiones
