# Para Agustín — qué activar para terminar el launch

> Estado al 2026-06-22. En `main` ya está: modelo **pago-only** con trial de
> 7 días, gate de acceso, **Mercado Pago completo en backend** (inerte hasta
> tener credenciales; incluye webhook firmado y **botón de baja**), frontend
> pago-only, KB admin, mobile QA y fixes de seguridad. Lo que falta para lanzar
> son **activaciones tuyas** (env vars + dashboards). Ordenado por prioridad.

---

## 0. NETLIFY — el frontend NO se está publicando 🔴 (URGENTE, 5 min)

El sitio `re-expert.netlify.app` está en **tu cuenta de Netlify** y hoy publica
por **Netlify Drop (subida manual)**. Los pushes a `main` llegan pero figuran
**"Skipped"** en Deploys → el frontend vivo quedó viejo (le faltan varios
deploys: UI del modelo pago, precio $69.900, app.css, UI de Mercado Pago).
El backend en Railway sí auto-deploya bien; la asimetría es solo Netlify.

**Fix definitivo (recomendado):** Netlify → proyecto `re-expert` →
*Site configuration → Build & deploy → Continuous deployment* → **Link
repository** al GitHub `re-expert`, branch **`main`**, base directory
**`frontend`**, publish directory **`.`**, build command **vacío**. Con eso
cada push a `main` publica solo (como Railway) y nunca más se sube a mano.

**Parche mientras tanto:** *Deploys → Trigger deploy → Clear cache and deploy
site* (o arrastrar la carpeta `frontend/` al Drop).

**Y de paso:** invitá a Mati al team (*Team → Members → Invite*) así puede
disparar deploys sin depender de vos.

---

## 1. Activá YA (el código ya está en prod, solo faltan env vars)

Todo esto va en **Railway → Variables** (backend), salvo donde diga frontend.

| Prioridad | Variable | Para qué | Valor / cómo |
|---|---|---|---|
| 🔴 Alta | `ADMIN_EMAILS` | (a) Habilita `/admin.html` (gestión del KB). (b) **Bypass del paywall**: los emails listados tienen acceso a la app aunque el trial venza — sin esto, **nuestras propias cuentas ya quedaron bloqueadas** (el trial venció y MP aún no cobra). Es lo más urgente. | Tu email + el de Mati, separados por coma. Ej: `agustin@...,mati@...` |
| 🟠 Media | `RESEND_API_KEY` + `RESEND_FROM` | Emails reales (recuperar contraseña). Hoy el link queda solo en logs. | Tu cuenta Resend. `RESEND_FROM=onboarding@resend.dev` para arrancar. |
| 🟠 Media | `SENTRY_DSN` (Railway) + `SENTRY_DSN` en `frontend/config.js` | Error tracking backend + frontend. Código ya wireado. | Crear 2 proyectos en sentry.io (backend FastAPI, frontend JS). Ver `docs/MONITORING.md`. |
| 🟡 Baja | `GEMINI_API_KEY` | Fallback gratis si Anthropic falla/sin saldo. | Tu cuenta Google AI Studio. |
| 🔴 Alta | Verificar **saldo `ANTHROPIC_API_KEY`** | Es el costo principal (~USD 3-5/usuario/mes uso medio). | Anthropic Console → Billing. |

**UptimeRobot** (5 min, anti cold-start de Railway): monitor HTTP a
`https://re-expert-production.up.railway.app/health` cada 5 min. Ver `docs/MONITORING.md`.

---

## 2. Mercado Pago — coordinemos (es lo que destraba el cobro) 🔴

El modelo es pago-only con **trial de 7 días con tarjeta upfront**, cobro en ARS
vía **Mercado Pago** (reemplaza a Stripe para Argentina). El precio definido es
**$69.900 ARS/mes** (~USD 45).

**La integración YA ESTÁ HECHA en backend** (`services/mercadopago_service.py`):
checkout (preapproval), webhook con verificación de firma HMAC, mapeo de estados
→ plan, y **botón de baja** (cancelación online, Ley 24.240) con su UI en
`account.html`. Todo **inerte** hasta que cargues las env vars — cuando las
pongas, se enciende solo (el registro pasa a tarjeta-upfront automáticamente).

**Tu parte (todo en el panel de MP + Railway):**
1. Crear el plan de suscripción (`preapproval_plan`): monto **$69.900 ARS**,
   frecuencia mensual, **período de prueba 7 días**.
2. Configurar el webhook en MP (Panel → Webhooks → eventos de suscripciones):
   **`https://re-expert-production.up.railway.app/api/billing/mp/webhook`**
   y copiar el secreto de firma.
3. Cargar en Railway → Variables: `MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`,
   `MP_WEBHOOK_SECRET`, `MP_PLAN_ID` (los nombres exactos están en
   `backend/.env.example`).

**Después de eso:** probamos juntos contra el sandbox de MP antes de anunciar
(checkout → webhook → acceso → baja). Detalle del diseño: `docs/MODELO_PAGO.md`.

> ⏰ **Importante:** el trial de las cuentas actuales **ya venció** (corte seco).
> Hasta que MP esté activo, la única vía de acceso es el bypass de `ADMIN_EMAILS`
> (punto 1) — cargalo primero.

---

## 3. Backups de Supabase 🟠

Hoy **no hay backup verificado** de la DB. Antes de meter usuarios reales:
- Confirmar el plan de Supabase. Si es Free → **no hay backups automáticos**;
  subir a Pro (daily) como mínimo.
- Hacer **una** prueba de restore a un proyecto de staging.
- Detalle y comandos (`pg_dump`/`pg_restore`): `docs/BACKUPS.md`.

---

## 4. Bugs de tu Capa 2 — estado 🟢/🔵

De los 2 bugs P1 de la revisión (**`docs/REVISION_CAPA2_2026-06-06.md`**):
1. ✅ **Bug 1 (cálculo) YA MERGEADO a `main`** (commit `df7f7e7`): `_spread`
   descartaba en silencio el costo de obra que caía fuera del horizonte de
   períodos e inflaba margen/TIR. Ahora conserva el total y avisa en `notas`.
   Con tests de regresión (`tests/test_capa2_fixes.py`); tus tests siguen verdes.
2. 🔵 **Bug 2 (prompt Transferencia) te quedó en la branch
   `fix/capa2-calculadora`** para tu revisión: tus últimos commits ya lo
   mitigan (el "disparador de tool" prohíbe el cedular 15% de memoria), pero
   las 2 líneas puntuales del prompt (descripción de la tool + regla 3 de
   Transferencia) siguen diciendo "desde 2018 → cedular 15%". El fix alinea
   eso con `exento_2026`. Mergealo si te cierra (PR listo en GitHub).

---

## 5. Más adelante (Fase 5, no bloquea el launch)

- **Custom domain + HSTS** (re-expert.app en vez de netlify.app). DNS en Netlify/Railway.
- **Telegram bot** (SOL por Telegram): el código está, falta `TELEGRAM_BOT_TOKEN` + webhook.

---

## Orden sugerido
1. **Netlify**: conectar el repo (o trigger deploy) — el front vivo está viejo.
2. `ADMIN_EMAILS` (2 min): desbloquea KB admin **y nuestras cuentas** (trial vence hoy).
3. Mercado Pago: plan + webhook + env vars (destraba el cobro; el código ya está).
4. Resend + Sentry + UptimeRobot (observabilidad / emails).
5. Backups Supabase.
6. Revisar/mergear `fix/capa2-calculadora` (Bug 2, prompt de Transferencia).

Cualquier cosa, hablamos. El estado completo del proyecto está en
`docs/HANDOFF_2026-06-03.md` + `docs/MODELO_PAGO.md`.
