# Test E2E — Flujo completo de usuario — Tarea #49

Guion manual paso a paso para validar el camino feliz end-to-end de RE Expert: registro → login → chat → SOL carga un pago → verificación → upgrade Pro vía Stripe test → features Pro habilitadas.

Este test lo corre una persona (no automatizado) antes de cada release. Cualquier desviación se documenta como bug en GitHub Issues con el template del final.

---

## Pre-requisitos

| Item | Valor |
|---|---|
| URL frontend | `https://re-expert.app` (prod) o `http://localhost:5173` (dev) |
| URL backend | `https://api.re-expert.app/health` debe responder `{"status":"ok"}` |
| Stripe modo | **Test mode** (claves `sk_test_...`, productos en test) |
| Tarjeta de prueba | `4242 4242 4242 4242` · cualquier CVC · cualquier fecha futura |
| Email de test | usar alias tipo `e2e+<fecha>@tu-dominio.com` para no chocar con cuentas previas |
| Browser | Chrome/Firefox actualizado, DevTools abierta (Network + Console) |

Antes de empezar, abrir DevTools → Application → Storage → **Clear site data** para arrancar sin sesión previa.

---

## Paso 1 — Registro

1. Ir a `https://re-expert.app/register.html`.
2. Completar:
   - Nombre completo: `E2E Tester`
   - Email: `e2e+<YYYYMMDD-HHMM>@tu-dominio.com`
   - Password: mínimo 8 caracteres con mayúscula, minúscula y número (ej: `Test1234`)
3. Click **Registrarme**.

**Esperado:**
- POST `/api/auth/register` → `201 Created`.
- Respuesta JSON con `access_token`, `refresh_token`, `user.plan === "free"`, `user.id` (UUID).
- localStorage guarda `re_access_token` y `re_refresh_token`.
- Redirect automático a `/index.html`.

**Bug si:**
- 422 con password fuerte → revisar validación de `RegisterRequest`.
- 409 con email nuevo → colisión de seed o email ya registrado.
- Tokens no persisten → revisar `authService.js` STORAGE_ACCESS/REFRESH.

---

## Paso 2 — Logout y Login

1. En `/index.html`, abrir el menú de tres puntos del topbar → **Cerrar sesión**.
2. Verificar que se redirige a `/login.html` y que `localStorage` quedó sin `re_access_token`.
3. Loguearse con el mismo email/password del paso 1.

**Esperado:**
- POST `/api/auth/login` → `200 OK` con tokens nuevos.
- `user.plan === "free"`.
- Redirect a `/index.html`, sidebar visible con secciones: Chat, Materiales, Noticias, Pagos, Proyecto, Cuenta.

**Bug si:**
- 401 con credenciales correctas → revisar bcrypt/argon2 verify en `auth_service.login_user`.

---

## Paso 3 — Chat: crear conversación, enviar mensaje, recibir respuesta

1. En el sidebar, sección **Chat**, click **Nueva conversación**.
2. Escribir el mensaje:
   > ¿Cuáles son los tres principales indicadores que se usan para evaluar la rentabilidad de un proyecto inmobiliario en Argentina?
3. Enviar (Enter o botón ▶).

**Esperado:**
- POST `/api/conversations` → `201` con `conversation_id`.
- POST `/api/chat/message` (o equivalente) → `200`, response con texto generado por Claude.
- La conversación aparece en el listado lateral con un título auto-generado (no genérico tipo "Nueva conversación").
- El mensaje del usuario y la respuesta del asistente quedan persistidos: refrescar la página y la conversación sigue ahí.
- Indicador de uso (`/api/usage`) se incrementa en 1 request del día.

**Bug si:**
- Timeout > 30s → revisar timeout del cliente Anthropic.
- Respuesta vacía o `"Lo siento, hubo un error..."` → revisar logs de `anthropic_service`.
- Conversación no persiste tras refresh → revisar commit en `conversations.py`.

---

## Paso 4 — SOL carga un pago

SOL es el asistente que ingesta datos vía `/api/data/ingest`. En plan **free** este endpoint debería estar gateado, pero el usuario puede crear pagos manualmente vía la UI de Pagos (mientras tanto, validamos el camino feliz manual).

### 4a. Crear pago manualmente desde la UI

1. Ir a la sección **Pagos** del sidebar.
2. Click **Cargar pago**. Completar:
   - Concepto: `Anticipo proveedor — hierro estructural`
   - Monto: `1500000`
   - Moneda: `ARS`
   - Estado: `pendiente`
   - Fecha: hoy
3. Guardar.

**Esperado:**
- POST `/api/payments` → `201` con el `Payment` creado y `id` UUID.
- La fila aparece en la tabla con formato `$1.500.000 ARS · pendiente`.
- El total pendiente del header se incrementa.

### 4b. Marcar como pagado

1. En la fila recién creada, click **Editar** (o el ícono ✏).
2. Cambiar estado a `pagado`.
3. Guardar.

**Esperado:**
- PATCH `/api/payments/{id}` → `200`.
- El monto se mueve del bucket "pendiente" al bucket "pagado" en el resumen.
- La fila refleja el nuevo estado sin recargar la página (optimistic update).

**Bug si:**
- 403 al guardar → falta de auth header o token expirado.
- El total no se actualiza sin refrescar → bug de re-render.
- Decimales se truncan o vienen con coma en lugar de punto → revisar `Decimal` ↔ JSON.

---

## Paso 5 — Verificar pago en sección

1. Hacer **doble click** en el título "Pagos" del topbar (acción `reloadCurrentSection` de la tarea #45).
2. La sección se recarga (loader visible brevemente).
3. El pago creado en el paso 4 sigue ahí con estado `pagado`.

**Esperado:**
- GET `/api/payments` → `200` devuelve lista con el pago + `summary` calculado.
- El `total_pagado` incluye los $1.500.000.
- `count_pagado` aumentó en 1.

---

## Paso 6 — Upgrade a Pro vía Stripe (test mode)

1. Ir a `/pricing.html` (link desde sidebar o footer).
2. Click **Pasar a Pro** (botón del card del plan Pro).
3. Browser redirige a `https://checkout.stripe.com/c/pay/cs_test_...`.
4. En Stripe Checkout, completar:
   - Email: el mismo del registro
   - Tarjeta: `4242 4242 4242 4242`
   - CVC: `123`
   - Fecha: cualquier mes/año futuro
   - Nombre: `E2E Tester`
   - País: Argentina
5. Click **Pay** / **Subscribe**.

**Esperado durante el flujo:**
- POST `/api/billing/checkout` → `200` con `{url, session_id}`.
- Stripe procesa el pago en ~2-3s.
- Redirect a `/success.html?session_id=cs_test_...`.

**Esperado después del webhook (segundos a minutos):**
- Stripe envía POST `/api/stripe/webhook` con `checkout.session.completed` (firma válida).
- Backend actualiza `user.plan = "pro"`, `user.stripe_customer_id = cus_test_...`.
- En el dashboard de Stripe Test → **Events**, el evento aparece con `200 OK`.
- En la BD: `users.plan = 'pro'` para ese email.
- En la BD: `stripe_events` tiene una fila nueva con el `event.id` (idempotencia).

**Verificación en la app:**
1. Volver a `/index.html`.
2. Ir a **Cuenta** → debería decir "Plan: Pro" + fecha de renovación.
3. GET `/api/billing/status` → `is_pro: true`, `subscription.status: "active"`, lista de invoices con 1 entrada.

**Bug si:**
- Plan no cambia tras 1 minuto → revisar `STRIPE_WEBHOOK_SECRET` y logs del webhook (¿firma rechazada?).
- 308/redirect del webhook → falta `--proxy-headers` en uvicorn (tarea #46).
- `stripe_events` tiene duplicados con mismo `event_id` → falla la UNIQUE constraint (#40).

---

## Paso 7 — Verificar features Pro habilitadas

Ya como usuario Pro, validar que las features gateadas se desbloquearon.

| Feature | Cómo verificar | Esperado free | Esperado pro |
|---|---|---|---|
| `history_full` | Crear 4 conversaciones y refrescar | solo se ven las últimas 3 | se ven las 4 |
| `sol_assistant` | Abrir SOL desde la sección Proyecto | banner "Requiere Pro" | el chat de SOL responde |
| `project_dashboard` | Ir a sección Proyecto | empty state con upsell | dashboard con presupuesto / hitos / materiales |
| `indicators_cpi_spi` | Dentro del dashboard | "Pro" lock | tarjetas CPI/SPI con números |
| `data_ingest` | POST `/api/data/ingest` desde DevTools | 403 con `plan_required: "pro"` | 200 con el ítem ingestado |
| `export` | Botón **Exportar CSV** en Pagos | botón deshabilitado o con lock | descarga el CSV |
| `priority_support` | Footer / sección Cuenta | link "Soporte estándar" | link "Soporte prioritario" |

Rate limits (definidos en `config/plans.py`): `pro` permite 50 req/hora vs `free` 5/hora. Hacer >5 mensajes de chat en una hora y verificar que **NO** se dispara el `429` que sí salta en free.

**Bug si:**
- Alguna feature sigue gateada estando ya en Pro → revisar `has_feature(user.plan, ...)` o `require_pro` en la ruta.
- Rate-limit sigue en 5/h → revisar `rate_limit_service.py` lee `PLAN_LIMITS[user.plan]`.

---

## Paso 8 — Cancelar suscripción (limpieza opcional)

Para dejar el ambiente listo para el próximo run:

1. Ir a **Cuenta** → **Administrar suscripción**.
2. POST `/api/billing/portal` → redirige al Billing Portal de Stripe.
3. **Cancel plan** → confirmar.
4. Stripe envía `customer.subscription.deleted` al webhook.
5. Verificar que `user.plan` vuelve a `"free"` (puede tardar hasta el próximo ciclo según el modo de cancelación; en test mode con `cancel_at_period_end=false` es inmediato).

---

## Reporte de bugs en GitHub

Si algún paso falla, abrir un issue en el repo siguiendo este template:

````markdown
**Título:** [E2E] Paso N — descripción corta del fallo

**Paso del guion:** Paso 6 — Upgrade a Pro vía Stripe

**Esperado:**
Plan del usuario cambia a "pro" tras 30s del checkout.

**Observado:**
Tras 5 minutos `user.plan` sigue en "free". `/api/billing/status` devuelve `is_pro: false`.

**Reproducción:**
1. Login con email `e2e+20260501-1430@...`
2. Pricing → Pasar a Pro → checkout con 4242...
3. Volver a /index.html → plan free.

**Logs / Network:**
- Stripe Dashboard → Events → `checkout.session.completed` → 502 al webhook.
- Backend logs: `stripe webhook signature verification failed`.

**Hipótesis:**
`STRIPE_WEBHOOK_SECRET` en Railway no coincide con el del endpoint registrado en Stripe.

**Severidad:** P0 (bloquea monetización)

**Entorno:** prod / Chrome 124 / commit `<sha>`
````

Etiquetas sugeridas: `e2e`, `bug`, prioridad (`p0`/`p1`/`p2`), área (`auth`/`chat`/`billing`/`payments`/`webhook`).

---

## Checklist (tarea #49)

- [x] Guion E2E paso a paso (8 pasos + pre-requisitos + cleanup)
- [x] Registro → login → chat (pasos 1, 2, 3)
- [x] Crear conversación → mensaje → respuesta (paso 3)
- [x] SOL / cargar pago (paso 4)
- [x] Verificar pago en sección (paso 5)
- [x] Upgrade Pro vía Stripe test (paso 6)
- [x] Verificar features Pro (paso 7 con tabla por feature)
- [x] Template de bug para GitHub Issues (sección final)

---

## Próxima evolución (no parte de #49)

Cuando se quiera automatizar este guion, candidatos:

- **Playwright** para los pasos 1–5 y 7 (UI determinista).
- **Stripe CLI** (`stripe listen --forward-to localhost:8000/api/stripe/webhook` + `stripe trigger checkout.session.completed`) para el paso 6 sin un browser real.
- Correr el set automatizado en CI nightly contra un staging dedicado con DB efímera.
