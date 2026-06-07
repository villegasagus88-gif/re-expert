# Para Agustín — qué activar para terminar el launch

> Estado al 2026-06-06. Esta semana (Mati + Claude) dejamos en prod: modelo
> **pago-only** con trial de 7 días, gate de acceso, el **frontend** del modelo
> pago, mobile QA, fixes de seguridad, y **KB admin**. Todo el código está
> desplegado en `main`. Lo que falta para lanzar son **activaciones tuyas**
> (env vars + dashboards) y un par de cosas a coordinar. Ordenado por prioridad.

---

## 1. Activá YA (el código ya está en prod, solo faltan env vars)

Todo esto va en **Railway → Variables** (backend), salvo donde diga frontend.

| Prioridad | Variable | Para qué | Valor / cómo |
|---|---|---|---|
| 🔴 Alta | `ADMIN_EMAILS` | Habilita `/admin.html` (gestión del knowledge base). **Sin esto nadie es admin** (el KB queda protegido pero no podés gestionarlo desde la app). | Tu email + el de Mati, separados por coma. Ej: `agustin@...,mati@...` |
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

**Tu parte:**
1. Crear el plan de suscripción en Mercado Pago (`preapproval_plan`) con: monto
   $69.900 ARS, frecuencia mensual, **período de prueba 7 días**.
2. Pasarme las credenciales (irán a Railway): `MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`,
   `MP_WEBHOOK_SECRET`, y el id del plan.

**Mi parte (cuando tenga las credenciales):** integro `mercadopago_service` +
webhook + el checkout en el frontend, y lo probamos contra el sandbox de MP antes
de activar. Detalle del diseño: `docs/MODELO_PAGO.md`.

> ⏰ **Importante:** el trial de las cuentas actuales vence **2026-06-10**. Si para
> esa fecha MP no está activo, esas cuentas quedan bloqueadas sin poder pagar
> (corte seco). Conviene tener MP listo antes, o avisame y extiendo el trial.

---

## 3. Backups de Supabase 🟠

Hoy **no hay backup verificado** de la DB. Antes de meter usuarios reales:
- Confirmar el plan de Supabase. Si es Free → **no hay backups automáticos**;
  subir a Pro (daily) como mínimo.
- Hacer **una** prueba de restore a un proyecto de staging.
- Detalle y comandos (`pg_dump`/`pg_restore`): `docs/BACKUPS.md`.

---

## 4. Bugs en tu Capa 2 (calculator tools) 🟠

En la revisión de tu código nuevo encontramos 2 bugs P1 (la matemática del grueso
y el wiring están perfectos). Detalle con reproducción y fix sugerido en
**`docs/REVISION_CAPA2_2026-06-06.md`**:
1. `flujo_fondos_desarrollo` descarta costo de obra que cae fuera de los períodos
   → infla el resultado.
2. El system prompt de Transferencia dice "cedular 15%" pero la tool calcula
   $0 exento (marco 2026) → el bot puede dar info fiscal incorrecta.

Si querés los arreglamos nosotros y te los dejamos en una branch para que revises.

---

## 5. Más adelante (Fase 5, no bloquea el launch)

- **Custom domain + HSTS** (re-expert.app en vez de netlify.app). DNS en Netlify/Railway.
- **Telegram bot** (SOL por Telegram): el código está, falta `TELEGRAM_BOT_TOKEN` + webhook.

---

## Orden sugerido
1. `ADMIN_EMAILS` (2 min, desbloquea KB admin).
2. Crear el plan en Mercado Pago + pasarme credenciales (destraba el cobro).
3. Resend + Sentry + UptimeRobot (observabilidad / emails).
4. Backups Supabase.
5. Tus 2 bugs de Capa 2.

Cualquier cosa, hablamos. El estado completo del proyecto está en
`docs/HANDOFF_2026-06-03.md` + `docs/MODELO_PAGO.md`.
