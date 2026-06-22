# Arquitectura — RE Expert

Visión general del sistema.

## Stack

| Capa | Tecnología | Hosting |
|---|---|---|
| **Frontend** | HTML + vanilla JS + CSS (dark premium) | Netlify |
| **Backend API** | Python 3.12 + FastAPI + uvicorn (Docker) | Railway |
| **Database** | PostgreSQL (Supabase) con Row Level Security | Supabase |
| **Auth** | Supabase Auth (email + password, JWT) | Supabase |
| **File storage** | Supabase Storage — bucket `knowledge` (archivos .md de conocimiento) | Supabase |
| **AI** | Anthropic Claude Sonnet 4.6 vía `anthropic` Python SDK | Anthropic API |
| **Migraciones DB** | Alembic (async) | Railway (preDeployCommand) |
| **CI/CD** | GitHub Actions (ruff + pytest) + auto-deploy vía integraciones | GitHub |

## Estructura del repo

```
chat-IA-REAL-STATE/
├── backend/                  # API FastAPI
│   ├── alembic/versions/     # Migraciones DB
│   ├── api/
│   │   ├── routes/           # Endpoints (auth, chat, knowledge, usage)
│   │   └── schemas/          # Pydantic request/response
│   ├── config/settings.py    # Settings via env vars
│   ├── core/                 # Auth (JWT), rate limiting (slowapi)
│   ├── models/               # SQLAlchemy 2.0 async
│   ├── services/             # Lógica de negocio (anthropic, knowledge, rate_limit, token_usage)
│   ├── tests/                # pytest + smoke tests
│   ├── main.py               # FastAPI app factory
│   ├── requirements.txt      # Production deps
│   └── requirements-dev.txt  # Dev deps (ruff, pytest)
├── frontend/                 # HTML estático + JS vanilla
│   ├── index.html            # App principal (chat UI, 155kb)
│   ├── login.html            # Página de login
│   ├── register.html         # Página de registro
│   ├── auth.css              # Dark theme premium para login/register
│   ├── auth.js               # Handlers de login/register + validaciones
│   ├── authService.js        # Gestión de sesión (tokens, refresh, interceptor)
│   ├── config.js             # Supabase URL + anon key (público)
│   └── supabase-client.js    # Wrapper del SDK de Supabase
├── knowledge/                # Archivos .md de base de conocimiento (se suben a Supabase Storage)
├── docs/                     # ESTA CARPETA
├── .github/workflows/ci.yml  # GitHub Actions pipeline
├── ruff.toml                 # Config de linter
└── package.json              # Scripts de desarrollo local
```

## Flujo principal: usuario envía un mensaje al chat

```
[Frontend index.html]
  usuario escribe → REAuthService.authFetch('POST /api/chat', {message, conversation_id?})
        │
        ▼  (Authorization: Bearer <JWT>)
[Backend /api/chat]
  1. core/auth.py          → verifica JWT de Supabase
  2. rate_limit_service    → chequea límite por plan (free: 5/h 20/d | pro: 50/h 200/d)
                             → si excede: 429 + Retry-After + X-RateLimit-* headers
  3. conversación          → get_or_create_conversation (si es nueva, title = primer msg)
  4. load_history          → últimos 20 msgs de la conversación
  5. persist user msg      → INSERT messages (role='user')
  6. context_router        → clasifica dominio del mensaje + selecciona archivos .md relevantes
  7. anthropic_service     → stream_chat(messages, system_prompt + knowledge)
        │
        │  async for delta in stream → SSE 'data: {type:delta, text}'
        │
  8. persist assistant msg → INSERT messages (role='assistant', tokens_used)
  9. log_token_usage       → INSERT token_usage (cost_usd calculado)
  10. SSE 'data: {type:done, tokens_used}'
```

## Modelos de datos (ver `backend/models/`)

### `profiles` (Supabase Auth trigger popula)
- `id` (UUID, PK, = auth.users.id)
- `email` (unique)
- `full_name`
- `plan` (`free` | `pro`, default `free`)
- `last_login`, `created_at`

### `conversations`
- `id` (UUID)
- `user_id` → `profiles.id`
- `title` (auto-derivado del primer mensaje)
- `created_at`, `updated_at`

### `messages`
- `id`, `conversation_id`, `role` (`user` | `assistant`), `content`, `tokens_used`, `created_at`

### `token_usage` (logging para billing/analytics)
- `id`, `user_id`, `conversation_id`, `message_id`
- `model`, `input_tokens`, `output_tokens`, `total_tokens`
- `cost_usd` (NUMERIC(10,6)) — calculado con tabla de pricing en `services/token_usage_service.py`
- `created_at`

## Endpoints backend

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| `GET` | `/health` | Health check (version) | ❌ |
| `POST` | `/api/chat` | Envía mensaje, devuelve SSE stream | ✅ |
| `GET` | `/api/usage` | Consumo agregado del usuario (24h/30d/all-time) | ✅ |
| `*` | `/api/auth/*` | Proxy a Supabase Auth (no se usa hoy, frontend va directo a Supabase) | — |
| `*` | `/api/knowledge/*` | Gestión de archivos de knowledge (admin) | ✅ |

### Formato SSE del chat

```
data: {"type":"start","conversation_id":"..."}
data: {"type":"delta","text":"chunk"}
data: {"type":"delta","text":"more"}
...
data: {"type":"done","tokens_used":1234}
```

En caso de error: `data: {"type":"error","message":"..."}`. Timeout duro a 60s.

## Rate limiting

Dos capas:
1. **IP-based (slowapi):** 20 req/min por IP sobre `/api/chat`. Previene abuso anónimo.
2. **Per-user (DB query):** según `plan` del usuario, cuenta mensajes en ventanas rolling 1h/24h.
   - Free: 5/h, 20/día
   - Pro: 50/h, 200/día
   - Response 429 incluye `Retry-After` (basado en el mensaje más viejo de la ventana) y headers `X-RateLimit-*`.

## Seguridad actual

- Passwords: Supabase Auth (bcrypt gestionado por ellos).
- Sesión: JWT de Supabase; access token en memoria (frontend), refresh token en Supabase localStorage.
- CORS: restringido a `localhost:8080`, `localhost:3000` (ampliar cuando deployemos frontend definitivo).
- Rate limiting: IP + per-user.
- Secrets: **nunca** hardcodeados; `.env` local + variables en Railway.
- DB: RLS activado en tablas de Supabase (cada usuario solo ve lo suyo).

Ver [`TRADE_OFFS.md`](TRADE_OFFS.md) para lo que queda pendiente de endurecer.
