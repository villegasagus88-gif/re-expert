# 🚀 Deploy Guide — para vos, Agustín

Esta es la **única** guía que necesitás leer para dejar todo
funcionando en producción. Todo el código ya está listo en la rama
`merge/launch-mvp-into-main`. Lo que falta son **clicks en
dashboards** que solo vos podés hacer porque sos owner de las cuentas.

**Tiempo total estimado:** 15-25 minutos.

---

## Resumen ejecutivo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Mergear el PR a main           [1 click GitHub]      ~30s │
│ 2. Resetear DB password Supabase  [1 click Supabase]    ~1min│
│ 3. Crear/reactivar servicio Railway + env vars         ~10min│
│ 4. Verificar Netlify auto-deploy                        ~2min│
│ 5. Smoke test E2E                                       ~3min│
└─────────────────────────────────────────────────────────────┘
```

---

## Paso 1 — Mergear el PR `merge/launch-mvp-into-main` a `main`

**Por qué:** Netlify auto-deploya desde `main`. Hasta que no se mergee,
el frontend sigue sirviendo la versión vieja (sin landing pública,
sin forgot-password, sin Planos multimodal, etc.).

1. Abrí: https://github.com/villegasagus88-gif/re-expert/pull/new/merge/launch-mvp-into-main
2. **Create pull request** (si no estaba creado).
3. Revisá el diff si querés (resumen abajo) — son ~25 commits.
4. **Squash and merge** o **Create a merge commit** (lo que prefieras).
5. Listo.

### Qué trae el merge (resumen)

| Área | Cambios |
|------|---------|
| **Frontend** | Landing pública nueva (`index.html`), app movida a `app.html`, forgot-password + reset-password páginas, redirect param post-login, Sentry SDK browser, security headers |
| **Backend** | Forgot/reset password endpoints, JWT invalidation post-reset (token_version), Resend integration, magic-bytes validation en attachments multimodal, Stripe webhook hardening, HTTPS+HSTS middlewares, body size limit 10MB, knowledge service degrada limpio sin Supabase Storage |
| **DB migrations** | 0013_stripe_events, 0014_password_resets, 0015_token_version (corren solas con `alembic upgrade head` en preDeploy) |
| **Deploy infra** | `netlify.toml` con reverse proxy a Railway, `railway.json` con healthcheck + preDeploy, `render.yaml` como fallback documentado |
| **Auditoría** | 13 hallazgos de seguridad resueltos (2 críticos, 5 altos, 3 medios, 3 bajos) |

---

## Paso 2 — Resetear la DB password de Supabase

**Por qué:** la password actual está rota (auth failed). Sin password
correcta el backend no puede conectarse a la DB.

1. Abrí: https://supabase.com/dashboard/project/uaiiqjouxlcvleiimokz/database/settings
2. Sección **Database password** → **Reset password**.
3. **COPIÁ la nueva password ANTES de cerrar el modal** (Supabase no
   la muestra de nuevo).
4. Guardala en un password manager. La necesitamos en el paso 3.

> ⚠️ Resetear la password **rompe** cualquier conexión activa. Como
> Railway está caído ahora, no rompe nada en prod. Si tu socia
> (Matias) tiene un backend local corriendo, le va a fallar hasta
> que actualice su `.env`.

---

## Paso 3 — Railway (10 min)

### 3.a. Verificar / Crear el servicio

Andá a: https://railway.com → tu proyecto **re-expert**.

**Si el servicio existe pero está caído:**
- Click en el servicio → **Settings** → **General**.
- Confirmá que **Root Directory** = `backend`.
- **Deployments** tab → último deploy → **⋯** → **Redeploy**.

**Si el servicio fue eliminado:**
- **New +** → **GitHub Repo** → seleccionar `villegasagus88-gif/re-expert`.
- En el servicio nuevo → **Settings → General**:
  - **Root Directory:** `backend`
  - **Watch Paths:** `backend/**`  *(opcional — evita rebuilds en cambios de docs/frontend)*
- Build = Railway detecta `backend/railway.json` y `Dockerfile` automáticamente.

### 3.b. Generar dominio público

**Settings → Networking → Public Networking → Generate Domain**.

- Idealmente Railway te asigna **`re-expert-production.up.railway.app`**
  (la que está hardcodeada en `netlify.toml`).
- Si te asigna OTRA URL (ej. `re-expert-x9k2.up.railway.app`), avisanos
  a Matias o a mí — hay que editar las 3 líneas `to = "..."` en
  `netlify.toml` y push. Es 1 minuto.

### 3.c. Cargar las env vars (Variables tab)

Click en **Variables → Raw Editor** y pegá ESTO, completando los
placeholders con los valores reales (Matias te los pasa por canal
privado — NO commiteamos secrets al repo):

```env
# === Secrets — pedir a Matias o sacar de Supabase ===
ANTHROPIC_API_KEY=<sk-ant-api03-... — pedir a Matias o crear en console.anthropic.com>
DATABASE_URL=postgresql+asyncpg://postgres.uaiiqjouxlcvleiimokz:<DB_PASSWORD_NUEVA>@aws-1-us-east-1.pooler.supabase.com:6543/postgres
JWT_SECRET=<secret de Supabase JWT Settings o `openssl rand -hex 32`>
SUPABASE_SERVICE_ROLE_KEY=<eyJhbGc... de Supabase API settings, service_role key>

# === Públicos / configurables ===
SUPABASE_URL=https://uaiiqjouxlcvleiimokz.supabase.co
FRONTEND_URL=https://re-expert.netlify.app
DEBUG=false
LLM_PROVIDER=auto
SCHEDULER_ENABLED=true
SCHEDULER_POLL_INTERVAL_SECONDS=30
BACKEND_PUBLIC_URL=https://re-expert-production.up.railway.app
```

**Cómo conseguir cada secret:**

| Variable | Dónde |
|----------|-------|
| `ANTHROPIC_API_KEY` | Matias te la pasa por DM. Si no, crear nueva en https://console.anthropic.com/settings/keys |
| `<DB_PASSWORD_NUEVA>` | La que reseteaste en el paso 2 |
| `JWT_SECRET` | Supabase Dashboard → Settings → API → **JWT Secret** (al lado de "JWT Settings"). Copiar tal cual |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard → Settings → API → **service_role** key (sección "Project API keys"). Click "Reveal" |

**Save**. Railway redeploya automáticamente.

### 3.d. (Opcional) Gemini como fallback gratis

Para que si Anthropic se queda sin créditos el chat siga andando:

1. https://aistudio.google.com/apikey → **Create API key**.
2. Agregar en Variables:
   ```
   GEMINI_API_KEY=<la key que te dieron>
   ```

Free tier: 15 RPM, 1M tokens/día.

### 3.e. Verificar build

**Deployments** tab → ver el último deploy en progreso.

Logs esperados (resumen):
```
=> Build (3-5 min)
=> Pre-deploy: alembic upgrade head
   INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002 ...
   INFO  [alembic.runtime.migration] Running upgrade 0014 -> 0015
=> Deploy
=> Healthcheck on /health → 200
=> Service Active
```

Si falla, los errores más comunes:
- **"Module not found"** → Root Directory NO está en `backend`.
- **"password authentication failed"** → revisar `DATABASE_URL` (¿está `+asyncpg`? ¿password correcta? ¿host con region correcta?).
- **Healthcheck timeout** → primer arranque tarda hasta 60s; ya está configurado timeout=60s. Si tarda más, ver logs.

---

## Paso 4 — Netlify (verificación)

**No deberías tener que tocar nada.** Netlify ya está conectado al
repo y auto-deploya desde `main`.

Cuando el PR se mergee (Paso 1), Netlify dispara un build automático.

Para verificarlo:
1. https://app.netlify.com → site `re-expert`.
2. **Deploys** tab → debería aparecer un deploy nuevo en progreso
   o "Published" recién.
3. Si no se gatilló → **Trigger deploy → Deploy site** (manual).

Tiempo de build: ~1-2 min.

---

## Paso 5 — Smoke test E2E (3 min)

Después de que **ambos** (Railway + Netlify) muestren "Active" /
"Published", verificar:

### 5.a. Backend directo
```bash
curl https://re-expert-production.up.railway.app/health
# Esperado: {"status":"ok","version":"0.1.0"}
```

### 5.b. Backend vía Netlify proxy (lo que ve el usuario)
```bash
curl https://re-expert.netlify.app/health
# Esperado: {"status":"ok","version":"0.1.0"}

curl https://re-expert.netlify.app/api/auth/me
# Esperado: {"detail":"Token de autenticacion requerido"} con HTTP 401
# (401 = OK; significa que el proxy funciona y el backend rechaza
#  porque no le mandamos token).
```

### 5.c. Frontend completo en browser

Abrir https://re-expert.netlify.app — checklist:

- [ ] **Landing pública** se ve (nuevo home con SEO, NO la app vieja).
- [ ] Click **"Empezar gratis"** → `/register.html` → form de signup.
- [ ] **Registrar** una cuenta con un email tuyo + password fuerte.
- [ ] Post-signup te lleva a `/app.html` con sidebar de 8 secciones.
- [ ] Click **Chat Experto** → mandá una pregunta → respuesta streaming.
  - Si dice "Error generando respuesta" → cargar créditos en
    https://console.anthropic.com/settings/billing.
- [ ] **Logout** (botón en el footer del sidebar) → volvés al login.
- [ ] **¿Olvidaste tu contraseña?** desde login → `/forgot-password.html`
  → pedir reset → revisar logs Railway, debería loggear el link al
  stdout (Resend no está wireado todavía).

### 5.d. Cuentas de prueba existentes (de testing local)

Si querés sin crear cuenta nueva, hay estas dos en la DB de Supabase:

```
demo_socio@test.com / Demo1234
matias_local@test.com / OtraPass456  (la password puede haber cambiado en local)
```

---

## Troubleshooting

### "Service unavailable" en Railway después del deploy
1. Logs muestran "password authentication failed for user postgres" →
   la `DATABASE_URL` está mal. Verificar la password.
2. Logs muestran "InvalidSQLStatementNameError: prepared statement
   does not exist" → falta `+asyncpg://` o falta el `statement_cache_size=0`.
   El código ya lo tiene, así que esto solo pasaría si se rolledback
   `backend/models/base.py`.

### El chat tira "Error generando respuesta"
- Si en logs ves "credit balance is too low" → cargar saldo Anthropic.
- Si ves otro error → ver `docs/DEPLOY_RAILWAY.md` § Troubleshooting.

### Netlify sigue sirviendo el deploy viejo
- Verificar que el merge a `main` se completó realmente.
- Forzar deploy: **Deploys → Trigger deploy → Clear cache and deploy site**.

### El `/api/*` tira 502 Bad Gateway desde Netlify
- Railway está caído o lento (>30s respondiendo).
- O la URL en `netlify.toml` no coincide con la real de Railway.
- Probar `curl https://re-expert-production.up.railway.app/health`
  directo. Si falla → problema en Railway. Si OK → editar `netlify.toml`.

### Subir noticias / archivos al knowledge base
- Supabase Dashboard → Storage → bucket `knowledge` → crear si no existe.
- Subir archivos .md / .csv / .yaml en las carpetas correspondientes.
- El backend los lee on-demand (cache 5min).

---

## Después de que todo esté UP

### Cargá créditos Anthropic
https://console.anthropic.com/settings/billing — $10 alcanza para
mucho testing. Sin esto, el chat IA no responde.

### (Opcional) Email real con Resend
1. https://resend.com → cuenta free → **API Keys → Create**.
2. Pegá `RESEND_API_KEY=re_...` en Railway Variables.
3. Verificar dominio en Resend si querés que el FROM sea
   `hola@re-expert.app`. Mientras tanto, el default `RESEND_FROM`
   usa el dominio onboarding de Resend (anda igual).

### (Opcional) Anti-sleep con UptimeRobot
Si el plan de Railway es free-with-credits y el servicio duerme:
1. https://uptimerobot.com → cuenta free.
2. **Add monitor → HTTP(s)** → URL: `https://re-expert-production.up.railway.app/health`.
3. **Interval: 5 minutes**.
Listo. Nunca duerme.

---

## Archivos de referencia que ya están en el repo

| Archivo | Para qué |
|---------|----------|
| `backend/.env.example` | Lista completa de env vars con descripción |
| `backend/railway.json` | Build config Railway |
| `netlify.toml` | Reverse proxy + pretty URLs + security headers |
| `docs/DEPLOY_RAILWAY.md` | Setup detallado de Railway |
| `docs/DEPLOY_RENDER_NETLIFY.md` | Fallback gratis con Render si Railway falla |
| `docs/RUNBOOK.md` | Operación diaria post-launch (logs, rollback, etc) |
| `docs/MVP_GAPS.md` | Qué falta para v1 (todo Critical ya cerrado) |
| `docs/TASKS_COMPLETED.md` | Changelog humano del proyecto |

---

## Si algo se rompe y necesitás revertir

**Rollback de Railway:**
- Deployments → buscar deploy anterior con status "Success" → **⋯ → Redeploy**.

**Rollback de Netlify:**
- Deploys → buscar deploy anterior verde → **Publish deploy**.

**Rollback de DB migration** (si una migration nueva rompió algo):
- Conectarse a Supabase SQL Editor.
- `UPDATE alembic_version SET version_num='<versión anterior>';`
- Manualmente revertir los cambios de schema si hicieron falta.

---

## TL;DR

1. **Merge PR** → https://github.com/villegasagus88-gif/re-expert/pull/new/merge/launch-mvp-into-main
2. **Reset Supabase password** → https://supabase.com/dashboard/project/uaiiqjouxlcvleiimokz/database/settings
3. **Railway** → recrear servicio con `Root Directory=backend` + pegar env vars (con la nueva DB password)
4. **Esperar** Netlify + Railway deploys (~5 min total)
5. **Verificar** `https://re-expert.netlify.app/health` devuelve `{"status":"ok"}`
6. **Cargar créditos Anthropic** cuando quieras que el chat funcione

Cualquier duda, mensaje a Matias o conmigo.
