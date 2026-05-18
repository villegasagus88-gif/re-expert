# Deploy en Render — backend RE Expert

Render reemplaza a Railway con free tier real (750h/mes, sin tarjeta).
La definición del servicio vive en [`render.yaml`](../render.yaml) en
la raíz del repo (Infrastructure-as-Code).

---

## Setup inicial (5 min, una sola vez)

### 1. Crear el servicio

1. Login en https://dashboard.render.com con GitHub.
2. **New +** → **Blueprint**.
3. Conectar el repo `villegasagus88-gif/re-expert`.
4. Render detecta `render.yaml` y muestra: "Create `re-expert-api` web service".
5. **Apply**.

### 2. Cargar secretos en el dashboard

En la página del servicio → **Environment** → completar todas las vars
marcadas como "Sync from blueprint" / "No value yet":

| Variable | De dónde sale |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys |
| `DATABASE_URL` | `postgresql+asyncpg://postgres.<proj>:<pass>@aws-X-<region>.pooler.supabase.com:6543/postgres` |
| `JWT_SECRET` | Supabase → Settings → API → JWT Secret (o `openssl rand -hex 32`) |
| `SUPABASE_URL` | `https://<proj>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → service_role |
| `FRONTEND_URL` | URL pública del frontend (Netlify) — necesario para CORS prod |
| `STRIPE_*` | Dejar vacías hasta que actives billing |
| `SENTRY_DSN` | Dejar vacío para deshabilitar |

3. **Save Changes** → Render redeploya automáticamente.

### 3. Verificar

```bash
# La URL pública la da Render en el header del servicio.
# Algo como: https://re-expert-api.onrender.com
curl https://re-expert-api.onrender.com/health
# Esperado: {"status":"ok","version":"0.1.0"}
```

### 4. Apuntar el frontend al nuevo backend

Editar `frontend/config.js` línea de `API_BASE`:

```js
API_BASE: 'https://re-expert-api.onrender.com'
```

Commit + push → Netlify redeploya el frontend solo.

### 5. Anti-sleep (opcional, 2 min)

Free tier de Render duerme el servicio después de 15 min de inactividad.
Primer request post-sleep tarda ~30s. Mitigación:

1. https://uptimerobot.com/ → cuenta free.
2. **+ Add New Monitor**:
   - Tipo: HTTP(s)
   - URL: `https://re-expert-api.onrender.com/health`
   - Interval: 5 minutos
3. Listo, el servicio nunca se duerme.

---

## Operación diaria

### Ver logs
Dashboard → servicio → **Logs**. Live tail.

### Forzar redeploy sin cambios
**Manual Deploy** → **Deploy latest commit**.

### Rollback
**Deploys** (tab) → en un deploy anterior → ⋯ → **Rollback to this deploy**.

### Migraciones Alembic
Se corren solas vía `preDeployCommand: alembic upgrade head` definido en
`render.yaml`. Si necesitás correr una manual, abrí el **Shell** del
servicio y ejecutá `alembic upgrade head`.

### Rotar un secret
Environment → editar el valor → **Save Changes**. Render redeploya.

---

## Diferencias vs Railway

| | Render free | Railway free |
|---|---|---|
| Costo | $0, sin tarjeta | $5/mes en créditos |
| Sleep | ✅ Sí, 15 min idle | ❌ No |
| GitHub auto-deploy | ✅ | ✅ |
| Build minutes/mes | 500 (free) | Ilimitados con créditos |
| Shell remoto | ✅ Web UI | ✅ Web UI |
| Logs live | ✅ | ✅ |
| Custom domains | ✅ HTTPS auto | ✅ HTTPS auto |
| `preDeployCommand` | ✅ | ✅ |

---

## Troubleshooting

### Deploy falla en pip install
Mirar logs en **Events** → expandir el deploy fallido. Causa típica:
versión de Python incompatible o dependencia rota. El Dockerfile usa
`python:3.12-slim` que está vigente.

### `/api/auth/login` devuelve 500
Probablemente faltan migraciones. Render corre `alembic upgrade head` en
pre-deploy pero si el pooler de Supabase está saturado puede fallar
silencioso. Correr en el Shell:
```
alembic current
alembic upgrade head
```

### `/api/chat` da error "credit balance is too low"
No es bug. La cuenta de Anthropic está sin créditos. Cargar en
https://console.anthropic.com/settings/billing.

### CORS bloquea el frontend
Verificar que `FRONTEND_URL` en Render env vars apunte a la URL real
del Netlify (sin trailing slash). Si tenés un dominio custom, agregalo
en `core/cors.py`.
