# Tareas completadas

Changelog humano del proyecto. Cada entrada: qué se hizo, PR, archivos principales.
Ordenado del más reciente al más viejo.

---

## 2026-04 — MVP Backend + Frontend básico

### Tarea 10: Manejo de sesión en frontend — PR #11

JWT access token en memoria, auto-refresh ~60s antes de expirar, interceptor
`authFetch`, redirect a `/login` si falla, flag `re_authed` en `sessionStorage`.

- `frontend/authService.js` (nuevo)
- Refresh token queda en localStorage (manejado por Supabase SDK) — documentado en `TRADE_OFFS.md` § 1.

### Tarea 9: Pantalla de login/registro — PR #10

Páginas premium con dark theme, validaciones frontend, errores de API visibles,
toggle entre login/registro, link "¿Olvidaste password?", redirect a `/app` post-login.

- `frontend/login.html`, `register.html`, `auth.css`, `auth.js`

### Tarea 8: Persistir mensajes en DB + auto-title — PR #9

Persistencia ya existía (tareas 2 y 3). Se agregó `_derive_title()` que genera
el título de la conversación desde el primer mensaje del usuario (truncado a 60 chars).

- `backend/api/routes/chat.py`

### Tarea 7: Router de contexto — PR #8

Clasifica el dominio del mensaje (`costos`, `materiales`, `normativa`, `financiero`,
`proyecto`, `general`) por keywords, selecciona archivos `.md` relevantes, limita
contexto inyectado a ~4000 tokens.

- `backend/services/context_router.py` (nuevo)
- Tests con preguntas ejemplo.

### Tarea 6: Servicio Knowledge Base — PR #7

`KnowledgeBaseService` que lee archivos del bucket `knowledge` de Supabase Storage,
parsea `.md` como texto y `.csv` como tablas, búsqueda por keywords, cache con TTL 1h.

- `backend/services/knowledge_storage.py`

### Tarea 5: Logging de tokens + GET /api/usage — PR #6

Modelo `TokenUsage`, migración `0003`, `calculate_cost_usd()`, `log_token_usage()`,
endpoint que agrega consumo del usuario en ventanas `last_24h` / `last_30d` / `all_time`.

- `backend/models/token_usage.py`, `backend/services/token_usage_service.py`, `backend/api/routes/usage.py`

### Tarea 4: Rate limiting por usuario — PR #5

Límites por plan (free: 5/h, 20/día | pro: 50/h, 200/día). DB query con ventanas
rolling. Headers `X-RateLimit-*` + `Retry-After` basado en el mensaje más viejo
de la ventana. Respuesta 429 cuando excede.

- `backend/services/rate_limit_service.py`

### Tarea 3: Sistema SSE — PR #4

Formato `text/event-stream` con eventos `start`, `delta`, `done`, `error`.
Timeout duro de 60s. Testeado con `curl -N`.

- `backend/api/routes/chat.py` (refinamientos al endpoint)

### Tarea 2: Endpoint POST /api/chat — PR #3

Endpoint principal con streaming SSE, system prompt + knowledge context, persistencia
de mensajes user/assistant.

- `backend/api/routes/chat.py` (creación)
- `backend/services/anthropic_service.py`

### Tarea 1: CI/CD básico — PR #2

GitHub Actions con ruff (lint) + pytest (tests). Deploy staging on merge a `main`
(Railway auto-deploy).

- `.github/workflows/ci.yml`, `ruff.toml`, `backend/pytest.ini`, `backend/tests/conftest.py`

---

## Antes del changelog (pre-tarea 1)

Setup inicial: FastAPI + SQLAlchemy async + Alembic + Supabase integrado, modelos
básicos (`profiles`, `conversations`, `messages`), auth JWT contra Supabase,
rate limiting por IP (`slowapi`), Docker + Railway deploy.
