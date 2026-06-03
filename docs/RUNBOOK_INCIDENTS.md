# Runbook de incidentes — RE Expert

Qué hacer cuando **algo se cae en producción**. Orientado a síntoma → detección →
diagnóstico → mitigación → escalamiento. Pensado para resolver bajo presión sin
depender de memoria.

- Tareas operativas de rutina (ver logs, redeploy, rollback, rotar secrets,
  migraciones): [RUNBOOK.md](./RUNBOOK.md).
- Setup de monitoreo y alertas (Sentry, UptimeRobot): [MONITORING.md](./MONITORING.md).
- Activación de APIs externas y costos: [APIS_EXTERNAS_Y_COSTOS.md](./APIS_EXTERNAS_Y_COSTOS.md).

---

## 0. Lo primero (30 segundos)

```bash
# Un solo comando te dice si backend / DB / auth / frontend están sanos:
python backend/tests/smoke_prod.py        # o:  npm run test:smoke
```

`18 ok, 0 fail` → la plataforma responde y la auth está enforced; el problema es
acotado (una feature puntual o un proveedor externo). Cualquier `FAIL` apunta
directo a la sección de abajo que corresponde.

**Dónde mirar:**

| Señal | Dónde |
|---|---|
| Errores backend (stacktraces) | Sentry → proyecto `re-expert-backend` → Issues |
| Errores frontend (JS del browser) | Sentry → proyecto `re-expert-frontend` → Issues |
| App caída (uptime) | UptimeRobot → monitores `/health` y `/` |
| Logs crudos del backend | Railway → servicio backend → Deployments → View Logs |
| ¿Es un proveedor? | status.anthropic.com · status.supabase.com · status.stripe.com · railway statuspage · netlifystatus.com |

---

## Severidades

| Sev | Definición | Ejemplos | Respuesta |
|---|---|---|---|
| **SEV1** | Plataforma caída o pérdida/exposición de datos | backend 5xx total, DB caída, secret filtrado, leak entre usuarios | Atender YA, avisar a Agustín, todo lo demás espera |
| **SEV2** | Una feature core rota, el resto anda | chat no responde, login roto, billing no actualiza plan | Atender en el día, mitigar o feature-flag |
| **SEV3** | Degradación parcial o cosmético | una sección lenta, un endpoint secundario 500 | Backlog priorizado |

---

## Triage rápido — síntoma → sección

| Síntoma | Sección |
|---|---|
| Sitio entero caído / UptimeRobot "down" / 5xx | [§1 Backend caído](#1-backend-caído) |
| Login falla, 401 masivos, todos deslogueados | [§2 Auth caído](#2-auth-caído--401-masivos) |
| El chat no responde / timeout / se corta | [§3 Chat caído](#3-chat-caído--timeouts) |
| `/health` ok pero `/health/db` 503 / datos no cargan | [§4 DB caída](#4-db-caída) |
| Pagué Pro y sigo en free / webhook 5xx | [§5 Billing / Stripe](#5-billing--stripe-webhook) |
| Pico de errores en Sentry tras un deploy | [§6 Mal deploy](#6-mal-deploy--pico-de-errores) |
| Una API key se filtró (repo, logs, screenshot) | [§7 Secret filtrado](#7-secret-filtrado) |

---

## 1. Backend caído

**Detección:** UptimeRobot avisa `RE Expert API down`; `smoke_prod.py` falla en
`/health`; el front muestra errores de red en todo.

**Diagnóstico:**
1. `curl -s -o /dev/null -w "%{http_code}\n" https://re-expert-production.up.railway.app/health`
   - Sin respuesta / timeout → el servicio no está corriendo o Railway tiene problema.
   - `5xx` → el proceso arranca pero crashea en requests → ver Sentry + Railway logs.
2. Railway → servicio backend → Deployments. ¿El deploy activo está **Success** o **Crashed**?
3. ¿Healthcheck rojo? Railway reinicia el container si `/health` no responde en 60s.
4. ¿Es Railway y no nosotros? → revisar el statuspage de Railway.

**Mitigación:**
- **Crash tras un deploy reciente** → rollback (RUNBOOK.md → "Rollback del backend"):
  Railway → Deployments → último **Success** → ⋯ → Redeploy. Es lo más rápido.
- **Cold start** (Railway durmió el container) → el primer request lo despierta;
  tarda ~5-10s. Si pasa seguido, activar UptimeRobot pinger `/health` cada 5 min
  (ver MONITORING.md y APIS_EXTERNAS).
- **OOM / CPU al palo** → Railway → Metrics. Si es saturación real, escalar el
  plan del servicio (consultar a Agustín — es cuenta paga).

**Escalamiento:** SEV1. Avisar a Agustín (owner Railway). Si fue un deploy malo,
rollback primero y diagnosticar después.

---

## 2. Auth caído / 401 masivos

**Detección:** muchos usuarios no pueden entrar; `smoke_prod.py` muestra los
protegidos devolviendo algo distinto de 401 (o login devuelve 401 con credenciales
buenas).

**Diagnóstico:**
1. ¿Cambió `JWT_SECRET` en Railway? Rotarlo **invalida todas las sesiones** →
   todos quedan deslogueados (es el efecto esperado de una rotación, ver §7).
2. ¿`/api/auth/login` con credenciales buenas da 401? → ver logs: puede ser
   `bcrypt/argon2 verify` fallando o la DB caída (§4).
3. ¿Todos los requests dan 401 pero el login anda? → el frontend no está mandando
   el header `Authorization`, o el token expiró y el refresh falla (ver
   `authService.js` → `/api/auth/refresh`).
4. Detalle del flujo de login y casos: [RUNBOOK.md](./RUNBOOK.md) → "user can't log in".

**Mitigación:**
- Rotación de `JWT_SECRET` no intencional → restaurar el valor anterior en Railway
  si se conoce; si no, comunicar "tenés que volver a iniciar sesión".
- DB caída → ir a §4.

**Escalamiento:** SEV1 si es total. `JWT_SECRET` lo maneja el equipo — no rotarlo
sin coordinar (ver nota en RUNBOOK.md).

---

## 3. Chat caído / timeouts

**Detección:** el chat tira "Error generando respuesta" o corta el stream; el
resto de la app anda (login, secciones).

**Diagnóstico:**
1. ¿Anthropic está caído o lento? → status.anthropic.com. Es la causa #1.
2. Railway logs durante el fallo: buscar `Stream timeout after 180s` o errores de
   `anthropic_service`. El stream tiene hard-cap de 180s.
3. ¿`ANTHROPIC_API_KEY` con saldo? Sin saldo → 4xx de Anthropic → el handler
   devuelve "Error generando respuesta" (en prod no expone el detalle a propósito).
4. ¿Timeout solo en queries largas? → contexto inyectado por `context_router`
   demasiado grande, o Sonnet razonando de más.

**Mitigación:**
- **Anthropic caído** → si `GEMINI_API_KEY` está cargada, el fallback gratis cubre
  (ver APIS_EXTERNAS). Si no, comunicar degradación; el chat vuelve cuando Anthropic
  se recupera. El resto de la app sigue usable.
- **Sin saldo Anthropic** → recargar (Agustín, cuenta paga). SEV1 para el chat.
- **Timeouts puntuales** → SEV3, monitorear; el cap de 180s evita que cuelgue.

**Escalamiento:** SEV2 (una feature core). SEV1 si es por falta de saldo y es la
propuesta de valor principal.

---

## 4. DB caída

**Detección:** `/health` ok pero `/health/db` (alias `/health/ready`) devuelve
**503** `db_unreachable`; las secciones cargan vacías o con error; logs con errores
de conexión asyncpg.

**Diagnóstico:**
1. `curl -s https://re-expert-production.up.railway.app/health/db` → 503 confirma.
2. status.supabase.com → ¿incidente del proveedor?
3. Supabase → Database → ¿pausado por inactividad (free tier) o por exceder
   límites de conexiones?
4. ¿Cambió `DATABASE_URL`? Tiene que ser el **pooler transaction mode** (`:6543`,
   `statement_cache_size=0`). La string directa (`:5432`) no aguanta carga
   (ver RUNBOOK.md → "Renombrar/mover DATABASE_URL").

**Mitigación:**
- Supabase pausado → reactivar desde el dashboard (Agustín, owner).
- Pool agotado → bajar concurrencia / revisar conexiones colgadas; reiniciar el
  servicio backend en Railway libera el pool.
- `preDeployCommand` (`alembic upgrade head`) fallando y abortando el deploy → ver
  RUNBOOK.md → "Correr una migración manual" para diagnosticar.

**Escalamiento:** SEV1. Owner de Supabase es Agustín. No tocar schema/RLS desde el
chat de Claude (constraint del proyecto).

---

## 5. Billing / Stripe webhook

**Detección:** usuario pagó y sigue en `free`; Stripe Dashboard → Events muestra
el webhook con 4xx/5xx; `/api/stripe/webhook` en logs con firma rechazada.

**Diagnóstico:**
1. Stripe Dashboard (test o live) → Developers → Events → buscar
   `checkout.session.completed`. ¿Llegó? ¿Qué status devolvió nuestro endpoint?
2. `503` del webhook sin más → falta `STRIPE_WEBHOOK_SECRET` en Railway (es la
   protección anti-forge: sin secret rechaza todo). Es el caso más común.
3. `signature verification failed` → el `STRIPE_WEBHOOK_SECRET` no coincide con el
   del endpoint registrado en Stripe.
4. Redirect 307/308 del webhook → falta `--proxy-headers` en uvicorn.

**Mitigación:**
- Cargar/corregir `STRIPE_WEBHOOK_SECRET` en Railway (Agustín). Stripe permite
  **reenviar** el evento desde Events → Resend, así el usuario queda en `pro` sin
  re-pagar.
- Verificar idempotencia: la tabla `stripe_events` no debe tener duplicados del
  mismo `event_id`.

**Escalamiento:** SEV2 (bloquea monetización, no la app). Billing es de Agustín.
Detalle de testing: [BILLING_TESTS.md](./BILLING_TESTS.md), [STRIPE.md](./STRIPE.md).

---

## 6. Mal deploy / pico de errores

**Detección:** Sentry dispara alerta de issue nuevo o "+10 usuarios en 1h" justo
después de un merge a `main`; errores que no estaban antes.

**Diagnóstico:**
1. Sentry → ordenar por "first seen". ¿El error aparece a partir del último deploy?
   El `release` en Sentry (= `settings.VERSION`) ayuda a ubicar la regresión.
2. `git log --oneline origin/main -5` → ¿qué entró recién?

**Mitigación:**
- **Rollback primero, diagnosticar después** (RUNBOOK.md → "Rollback del backend").
  Railway → último deploy Success previo → Redeploy.
- Frontend (Netlify): Deploys → deploy anterior → "Publish deploy".
- Arreglar en una branch, pasar por `merge/launch-mvp-into-main`, re-deploy.

**Escalamiento:** SEV depende del blast radius. Si rompió algo core, SEV1/2 hasta
el rollback.

---

## 7. Secret filtrado

**Detección:** una API key / secret aparece en el repo, en logs, en un screenshot,
en un mensaje. GitHub Push Protection puede haberlo bloqueado en el push.

**Acción inmediata (SEV1, en orden):**
1. **Rotar la key** en el dashboard del proveedor (Anthropic / Resend / Stripe /
   Supabase / Tavily). Ver RUNBOOK.md → "Rotar un secret".
2. Cargar la nueva en Railway/Netlify Variables → Deploy.
3. Revocar la vieja en el proveedor.
4. Si lo filtrado fue `JWT_SECRET` → rotarlo además **invalida todos los tokens**
   (logout global forzado). Es el comportamiento correcto ante compromiso.
5. Si la key quedó en el historial de git: rotar es lo que importa (la key vieja ya
   no sirve). No reescribir historia de `main` (constraint del proyecto).
6. Documentar como incident note en [TASKS_COMPLETED.md](./TASKS_COMPLETED.md).

**Recordatorio:** los secrets viajan **solo** por env vars; nunca en código.
`.env.example` lista el formato de cada uno. Ver [SECRETS.md](./SECRETS.md).

---

## Comunicación

- **Quién toca qué:** Mati → código, deploys, APIs propias (Resend, Gemini,
  UptimeRobot, Sentry). Agustín → owner de Supabase, Railway y Stripe; activación
  de billing y cuentas pagas.
- **SEV1/2:** avisar al otro apenas se detecta, aunque ya lo estés mitigando.
- Si afecta usuarios y hay Status Page de UptimeRobot, actualizarla.

## Post-incidente (postmortem liviano)

Tras resolver un SEV1/SEV2, dejar 5 líneas en [TASKS_COMPLETED.md](./TASKS_COMPLETED.md):
qué pasó, impacto (usuarios/tiempo), causa raíz, cómo se mitigó, y la acción para
que no se repita. Sin culpas — el foco es el sistema, no la persona.
