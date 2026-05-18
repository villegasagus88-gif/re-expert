# Deploy a producción — Railway (backend) + Netlify (frontend)

> Arquitectura: Netlify sirve el frontend y proxie `/api/*`,
> `/static/*` y `/health` al backend en Railway via rewrites. Una
> sola URL para el usuario, sin CORS, sin mixed-content.

---

## Archivos ya configurados en el repo

| Archivo | Qué hace |
|---------|----------|
| `backend/railway.json` | Build con Dockerfile, healthcheck `/health` (60s timeout), preDeployCommand `alembic upgrade head`, restart on failure x3, sleepApplication=false |
| `backend/Dockerfile` | Python 3.12 slim, uvicorn con `--proxy-headers` (lee X-Forwarded-Proto de Railway), expone `$PORT` |
| `netlify.toml` | Reverse proxy a `re-expert-production.up.railway.app`, pretty URLs, security headers |
| `frontend/config.js` | `API_BASE=''` (same-origin), todo va vía rewrites |

**Cero código que tocar.** Todo al día en `merge/launch-mvp-into-main`.

---

## Setup en Railway

### 1. Crear el servicio

Si el servicio anterior fue eliminado:

1. https://railway.com → New Project → **Deploy from GitHub repo**.
2. Seleccionar `villegasagus88-gif/re-expert`.
3. En **Settings** del nuevo servicio:
   - **Root Directory:** `backend`
   - **Build:** Railway detecta automáticamente `backend/railway.json` y el `Dockerfile`.
   - **Watch Paths:** `backend/**` (opcional, evita rebuilds en cambios de frontend/docs).

### 2. Configurar el dominio público

En **Settings → Networking**:
- Click **Generate Domain** → Railway asigna `re-expert-production.up.railway.app` (o `re-expert-<token>.up.railway.app` si está tomado).
- **Importante:** si el dominio asignado NO es exactamente `re-expert-production.up.railway.app`, editar `netlify.toml` con la URL real (3 líneas `to = "https://..."`) y commit.

### 3. Cargar env vars (Variables tab)

| Variable | Valor | Notas |
|----------|-------|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | Tu key actual |
| `DATABASE_URL` | `postgresql+asyncpg://postgres.uaiiqjouxlcvleiimokz:<DB_PASSWORD>@aws-1-us-east-1.pooler.supabase.com:6543/postgres` | **El `+asyncpg` es OBLIGATORIO** |
| `JWT_SECRET` | string ≥32 chars random | Reusá el de antes para no invalidar JWTs |
| `SUPABASE_URL` | `https://uaiiqjouxlcvleiimokz.supabase.co` | |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGci...` (el service_role JWT) | |
| `FRONTEND_URL` | `https://re-expert.netlify.app` | Para CORS prod + links en emails |
| `DEBUG` | `false` | Hardening prod (HTTPS redirect, HSTS) |
| `LLM_PROVIDER` | `auto` | Usa Gemini si hay key, sino Anthropic |
| `GEMINI_API_KEY` | (opcional) | Fallback gratis 15 RPM (https://aistudio.google.com/apikey) |
| `SCHEDULER_ENABLED` | `true` | Para que SOL dispare recordatorios |
| `SCHEDULER_POLL_INTERVAL_SECONDS` | `30` | |
| `BACKEND_PUBLIC_URL` | `https://re-expert-production.up.railway.app` | Para links de PDFs en WhatsApp/Telegram |
| `RESEND_API_KEY` | (opcional) | Para emails reales de forgot-password (free 3000/mes) |
| `SENTRY_DSN` | (opcional) | Vacío deshabilita Sentry |
| `STRIPE_*` (4 vars) | (opcional) | Vacías hasta que actives billing |

### 4. Deploy

Railway despliega automáticamente al detectar push a `main`. Cuando
mergues el PR a `main`:

1. Build (3-5 min).
2. `alembic upgrade head` corre antes de promover (preDeployCommand).
3. Servicio promovido. Healthcheck en `/health` confirma.
4. Netlify también auto-deploya el frontend (1-2 min).

### 5. Verificar

```bash
# Backend health (Railway directo):
curl https://re-expert-production.up.railway.app/health
# Esperado: {"status":"ok","version":"0.1.0"}

# Backend vía Netlify proxy (lo que ve el usuario):
curl https://re-expert.netlify.app/health
curl https://re-expert.netlify.app/api/auth/me   # 401 sin auth = OK

# Frontend en browser:
# https://re-expert.netlify.app  → landing pública
# https://re-expert.netlify.app/login.html  → form
# https://re-expert.netlify.app/app.html  → app (post-login)
```

---

## Operación diaria

### Ver logs
Railway → servicio → **Deployments** → click en el activo → **View Logs**.
Live tail con filtros por nivel.

### Forzar redeploy
**Deployments** → en el activo → **⋯** → **Redeploy**.

### Rollback
**Deployments** → buscar deploy anterior Success → **⋯** → **Redeploy**.

### Migraciones
Corren automáticamente vía `preDeployCommand`. Si necesitás correr
una manual: **Shell** del servicio → `alembic upgrade head` /
`alembic history` / `alembic current`.

### Rotar un secret
Variables → editar el valor → **Deploy**. Railway redeploya automáticamente.

---

## Troubleshooting

### Deploy falla con "Module not found"
Probablemente el **Root Directory** no está seteado a `backend`. En
Settings → General → verificar Root Directory = `backend`.

### `/api/auth/login` devuelve 500 con "password authentication failed"
La `DATABASE_URL` tiene la password vieja o mal formateada. Verificar:
- Empieza con `postgresql+asyncpg://` (NO `postgresql://`)
- La password está actualizada en Supabase
- El host termina en `.pooler.supabase.com:6543` (transaction pooler)

### Cold start lento (>10s)
Railway free tier puede dormir. Plan Hobby ($5/mes con $5 de créditos)
mantiene el servicio always-on. En Settings → confirmá que
`sleepApplication: false` (ya está en railway.json).

### El chat tira "Error generando respuesta"
- Si el mensaje es "Your credit balance is too low" → cargar créditos
  en https://console.anthropic.com/settings/billing.
- Si es otro error → ver logs del deploy.

### Netlify proxie 502 desde Railway
Railway está caído o tarda en responder >30s. Confirmar:
1. Railway dashboard muestra el servicio **Active**.
2. `curl https://re-expert-production.up.railway.app/health` directo
   devuelve 200.
3. Si todo OK pero proxy falla → URL en `netlify.toml` no coincide
   con la URL real del servicio.

---

## Fallback gratis: Render (si Railway sale caro o falla)

Está documentado en `docs/DEPLOY_RENDER_NETLIFY.md` y el blueprint
`render.yaml` está listo. La migración Railway → Render = cambiar
las 3 URLs en `netlify.toml` y crear el Blueprint en Render.
Cero código que tocar.
