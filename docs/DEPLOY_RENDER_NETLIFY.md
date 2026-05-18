# Deploy a producción gratis — Render (backend) + Netlify (frontend)

> Arquitectura: Netlify sirve el frontend estático y proxie `/api/*`,
> `/static/*` y `/health` al backend en Render via rewrites. Esto evita
> CORS, mantiene una sola URL pública (`re-expert.netlify.app`), y deja
> el backend gratis 750h/mes en Render.

---

## Estado de los archivos (ya hechos por mí)

| Archivo | Qué hace |
|---------|----------|
| `render.yaml` | Blueprint: define el web service Docker con autodeploy desde main, healthcheck, preDeployCommand (alembic upgrade) y env vars |
| `netlify.toml` | Reverse proxy `/api/*` → `https://re-expert-api.onrender.com`, pretty URLs, security headers |
| `frontend/config.js` | `API_BASE=''` (same-origin), todo va vía rewrites de Netlify |
| `backend/Dockerfile` | Usa `$PORT` dinámico + `--proxy-headers` (compatible Render) |

**No hay que tocar nada de código.** Todo está al día en la rama
`merge/launch-mvp-into-main`.

---

## Setup en Render (≈ 10 minutos)

### 1. Crear cuenta + servicio

1. https://render.com → **Get Started for Free** → login con GitHub.
2. Dashboard → **New +** → **Blueprint**.
3. **Connect a repository** → seleccionar `villegasagus88-gif/re-expert`.
4. Render detecta `render.yaml` y propone crear el servicio
   `re-expert-api`. → **Apply**.

### 2. Cargar las env vars secretas

En la página del servicio → tab **Environment** → completar las
variables marcadas como "Sync from blueprint" (todas las `sync: false`):

| Variable | De dónde sale | Notas |
|----------|---------------|-------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys | requerida para chat |
| `DATABASE_URL` | Supabase Dashboard → Database → Connection string → URI (transaction pooler) | **Reemplazar `postgresql://` por `postgresql+asyncpg://`** |
| `JWT_SECRET` | Supabase → Settings → API → JWT Secret, o `openssl rand -hex 32` | cualquier string ≥ 32 chars |
| `SUPABASE_URL` | `https://uaiiqjouxlcvleiimokz.supabase.co` | ya conocida |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → service_role (secreto) | **NO compartir** |
| `FRONTEND_URL` | `https://re-expert.netlify.app` | para CORS + links en emails |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey (opcional pero recomendado) | fallback gratis si Anthropic se queda sin saldo |
| `STRIPE_*` (4 vars) | Dejar vacías hasta que actives billing | |
| `SENTRY_DSN` | Dejar vacío para deshabilitar | |

`BACKEND_PUBLIC_URL` se autocompleta a la URL que Render asigna.

→ **Save Changes**. Render redeploya automáticamente.

### 3. Esperar build (2-5 min) y verificar

```bash
# La URL pública la da Render en el header del servicio.
# Algo como: https://re-expert-api.onrender.com (o re-expert-api-XXX.onrender.com)

curl https://re-expert-api.onrender.com/health
# Esperado: {"status":"ok","version":"0.1.0"}
```

### 4. Ajustar `netlify.toml` si el hostname de Render es diferente

`netlify.toml` hardcodea `https://re-expert-api.onrender.com`. Si
Render te asigna otro hostname (ej. `re-expert-api-a1b2.onrender.com`),
editar las 3 líneas `to = "https://..."` en `netlify.toml` y commit a main.

Netlify rebuildea solo en cuanto detecta el push.

---

## Setup en Netlify (ya está, solo asegurar auto-deploy)

Netlify ya está conectado al repo. Después del merge del PR, Netlify
deploya solo. Confirmar en https://app.netlify.com → site `re-expert`
→ **Deploys** que apareció un nuevo deploy "Production".

Si por alguna razón no se gatilla:
- **Trigger deploy** → **Deploy site** (manual).

---

## Anti-sleep en Render (free tier duerme tras 15 min idle)

Cold start ~30s después de inactividad. Para evitarlo:

1. https://uptimerobot.com/ → cuenta free (no requiere tarjeta).
2. **+ Add New Monitor** → HTTP(s).
3. URL: `https://re-expert-api.onrender.com/health` (o el hostname que
   te dé Render).
4. Monitoring Interval: **5 minutos**.
5. **Create Monitor**. Listo — pinguea cada 5 min, el servicio no
   duerme y queda 100% gratis.

---

## Verificación final E2E

Una vez que Render + Netlify están arriba:

```bash
# Backend health vía Netlify proxy:
curl https://re-expert.netlify.app/health
# Esperado: {"status":"ok","version":"0.1.0"}

# Backend API vía Netlify proxy:
curl https://re-expert.netlify.app/api/auth/me
# Esperado: 401 (sin auth) — pero responde, lo cual significa que el
# proxy funciona end-to-end.

# Frontend:
# Abrir https://re-expert.netlify.app en el browser:
#   - Landing pública carga
#   - "Iniciar sesión" → /login.html → form
#   - Registrar cuenta → app.html con sidebar
```

---

## Rollback rápido

Si un deploy rompe prod:

**Render:** Deploys (tab) → Deploy anterior **Success** → **⋯** → **Rollback to this deploy**.

**Netlify:** Deploys → buscar el deploy anterior verde → **Publish deploy**.

---

## Lo que NO requiere acción tuya

- Migrations Alembic: corren solas en cada deploy de Render
  (`preDeployCommand: alembic upgrade head`).
- HTTPS en ambos: automático.
- CORS: ya está configurado y, con el reverse proxy de Netlify, ni se
  activa porque todo es same-origin.
- Security headers (X-Frame-Options, HSTS, etc): ya están en
  `netlify.toml`.
