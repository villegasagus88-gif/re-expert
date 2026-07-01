# Plan de acción — Pagos: Suscripción Pro + Cursos de Academia (2026-07-01)

> Plan, no implementación. Auditado contra el código real de hoy (`main 287cb7e`).
> Dominio: **pagos/billing es nuestro** (Mati + Claude). Academia (contenido,
> catálogo, demanda) es de Agus — los puntos de contacto están marcados.

---

## 1) Estado actual (auditado)

### Suscripción Pro ($69.900/mes) — ~90% construida, INERTE por env
| Pieza | Estado |
|---|---|
| `services/mercadopago_service.py` | ✅ Completo: Preapproval (suscripción MP) — `create_subscription`, `start_subscription_checkout`, `verify_webhook_signature` (HMAC), `fetch_preapproval`, `cancel_subscription`, `handle_webhook` idempotente, `mp_enabled()` gate |
| `api/routes/billing.py` | ✅ `GET /status`, `POST /checkout`, `GET /mp/config`, `POST /mp/cancel`, `POST /mp/webhook` (firma, sin JWT) |
| `config/plans.py` + `core/plan_gate` | ✅ Modelo pago-only: `trial` (7d sin tarjeta) → `pro` → `inactive` (paywall 403) |
| Settings (env) | ✅ `MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`, `MP_WEBHOOK_SECRET`, `MP_PLAN_ID`, `MP_BACK_URL` — sin valores = MP apagado, la app funciona igual |
| Frontend | ✅ `pricing.html` → checkout; `account.html` → estado + baja; `app.html` → paywall + banner trial; `success.html` post-pago |
| Docs/tests | ✅ `docs/MODELO_PAGO.md`, `docs/BILLING_TESTS.md`, suites de billing/MP verdes |
| **Stripe legacy** | ⚠️ Convive código muerto (`stripe_service.py`, `stripe_routes.py`, `POST /billing/portal`, tests) — nunca activo en AR |

**Falta para cobrar suscripciones:** credenciales + plan en el panel de MP (Agus),
webhook apuntado, pruebas sandbox E2E, y hardening de operación (§4).

### Cursos de Academia — 0% de pagos (por diseño, se está midiendo demanda)
| Pieza | Estado |
|---|---|
| Catálogo | ✅ 5 catálogos / 30 cursos con `price_ars` ($220.000 típico) e `is_free`, proveedores (`provider`) |
| Demanda | ✅ `POST /academia/interest` + `GET /academia/demand` + `admin-academia.html` (migración 0022) — registra clicks de "lo quiero" |
| Compra real | ❌ No existe: ni checkout, ni modelo de compras, ni entitlements, ni webhook de pagos únicos (el handler actual solo procesa topic `preapproval`) |

---

## 2) Decisiones de arquitectura (propuestas)

1. **Un solo gateway: Mercado Pago** (ARS, mercado argentino).
   - Suscripción → **Preapproval** (ya construido).
   - Cursos → **Checkout Pro** (preference de pago único). Tarjeta/débito/dinero en cuenta; MP maneja cuotas.
2. **Retirar Stripe legacy** en la misma fase (menos superficie, menos confusión). Decisión reversible: se borra en un commit propio.
3. **Entitlements de cursos en DB propia**: tabla `course_purchases` (user_id, course_id, mp_payment_id, monto, estado, timestamps). La verdad del acceso vive en nuestra DB, MP solo es el medio de cobro.
4. **El webhook se divide por topic**: `preapproval` → suscripción (ya), `payment` → compras únicas (nuevo). Un solo endpoint, firma HMAC común, dispatch interno.
5. **Los cursos NO requieren suscripción activa para comprarse** (decisión a validar con Agus): un usuario `inactive` puede comprar un curso suelto → funnel de re-entrada. Alternativa: exigir plan activo (más simple, menos venta).

---

## 3) FASE 0 — Activación Mercado Pago (bloqueante, mayormente Agus)

> Nada de esto se hace desde el chat (regla del repo): son dashboards de Agus.
> Nosotros dejamos TODO documentado y el código listo para recibir los valores.

1. **Agus, en el panel de MP** (cuenta vendedor production-ready):
   - Crear la aplicación → obtener `MP_ACCESS_TOKEN` + `MP_PUBLIC_KEY` (primero sandbox/test, luego producción).
   - Crear el **plan de suscripción** ($69.900/mes, ARS) → `MP_PLAN_ID`.
   - Configurar webhook → `https://re-expert-production.up.railway.app/api/billing/mp/webhook` → obtener `MP_WEBHOOK_SECRET`.
2. **Agus, en Railway**: cargar las 5 env vars (primero las de TEST).
3. **Nosotros**: smoke con credenciales de test (`GET /api/billing/mp/config` pasa a enabled), y checklist de E2E sandbox (§4.1).
4. **Criterio de salida**: cuenta test cobra una suscripción sandbox de punta a punta.

**Esfuerzo**: Agus ~2-3 h de dashboards; nosotros ~1 h de smoke.

---

## 4) FASE 1 — Suscripción Pro en producción

### 4.1 Validación sandbox (nuestro, 0.5-1 día)
- E2E con usuario de prueba: registro → trial → `POST /billing/checkout` → pagar en sandbox → webhook llega → `plan=pro` → paywall desaparece → `account.html` muestra estado → `POST /mp/cancel` → `inactive` → paywall vuelve.
- Casos borde con tarjetas de test de MP: pago rechazado, preapproval `paused`, reintento aprobado.
- Verificar los redirects de `MP_BACK_URL` (success/failure/pending → `success.html` / `pricing.html`).

### 4.2 Gaps a cerrar antes de cobrar en serio (nuestro, 1-2 días)
1. **Grace period / dunning**: hoy `plan_for_status` corta el acceso al caer el preapproval. Definir: `paused`/pago caído → N días de gracia con banner "actualizá tu medio de pago" antes de `inactive` (MP reintenta solo; mapear sus estados a nuestra máquina trial/pro/grace/inactive).
2. **Historial mínimo de eventos de billing** (tabla `billing_events`: user, topic, estado, raw_id, ts) para soporte y conciliación — hoy el webhook aplica estado pero no deja rastro consultable.
3. **Emails transaccionales** (cuando Resend esté activo — hoy NO está): bienvenida a Pro, pago caído, baja confirmada. Hasta entonces: solo banners in-app (ya existen).
4. **Retirar Stripe legacy** (commit propio: rutas + service + tests).
5. **Página de precios**: revisar copy final con el flujo real (7 días gratis sin tarjeta → paywall → checkout MP).

### 4.3 Go-live (Agus + nosotros, 0.5 día)
- Swap de env test → producción en Railway.
- 1 compra real de humo (con tarjeta real, se puede reembolsar desde el panel).
- Monitoreo primera semana: webhook logs + `GET /demand` de soporte.

**Criterio de salida**: primer suscriptor real cobrado y con acceso; baja y reactivación probadas.

---

## 5) FASE 2 — Pagos de cursos (Academia)

> Precondición estratégica: **leer la medición de demanda** (`GET /academia/demand`)
> con Agus. Si un curso no tiene demanda, no construimos su checkout todavía.
> Precondición técnica: Fase 0 lista (mismas credenciales MP).

### 5.1 Modelo de datos (nuestro, migración nueva)
- Tabla `course_purchases`:
  `id, user_id (FK), course_id (string del catálogo), course_title, price_ars,
  mp_preference_id, mp_payment_id, status (pending|approved|rejected|refunded),
  created_at, updated_at` + índice único parcial `(user_id, course_id)` en
  `approved` (no comprar dos veces).
- **No** tocamos el catálogo de Agus (JSON) — solo referenciamos `course_id`.

### 5.2 Backend (nuestro, 1-2 días)
1. `POST /api/academia/checkout {course_id}` (auth):
   - Valida curso existente + `is_free=false` + no comprado.
   - Crea **preference** de Checkout Pro (título, precio del catálogo — el precio
     SIEMPRE sale del backend, nunca del cliente), `external_reference = purchase_id`.
   - Persiste `course_purchases(status=pending)` → devuelve `init_point` (URL de pago).
2. **Webhook**: extender `handle_webhook` con topic `payment`:
   - Fetch del payment real en MP (nunca confiar en el body), matchear por
     `external_reference`, aplicar `approved/rejected` idempotente.
3. `GET /api/academia/my-courses` (auth): cursos comprados del usuario (+ los free "inscriptos" si Agus quiere trackear enrollment).
4. Cursos `is_free=true`: enrollment directo sin MP (registro en la misma tabla con `price_ars=0, status=approved`).
5. Tests: preference con precio del catálogo, webhook approved/rejected/duplicado, no re-compra, free enrollment, curso inexistente.

### 5.3 Frontend (nuestro, 1 día)
- En la vista Academia: botón del curso pasa de "Me interesa" (demanda) a
  **"Comprar — $X"** / **"Empezar gratis"** cuando el checkout esté activo
  (flag por env/config → rollout gradual por catálogo si hace falta).
- Estados: comprado ("Ya es tuyo → Ir al curso"), pending (verificando pago), rechazado (reintentar).
- Redirect post-pago: `success.html` variante curso → vuelta a Academia.
- "Mis cursos" (sección o filtro) con lo comprado.

### 5.4 Punto de contacto con Agus (SU dominio — coordinar antes de construir)
- **Qué recibe el comprador**: hoy los cursos tienen `provider` (¿contenido propio?
  ¿cupo con proveedor externo? ¿link/acceso?). El fulfillment post-compra lo
  define Agus; nosotros entregamos el entitlement (`approved` en DB) y el hook
  visual "Ir al curso".
- Si hay **revenue share con proveedores**: registrar el split en `course_purchases`
  (campo `provider_share_pct`) para liquidar a mano al principio. Marketplace
  split automático de MP queda para más adelante (complejidad alta).

**Criterio de salida**: compra sandbox de un curso E2E; free enrollment; "mis cursos" consistente tras webhook.

---

## 6) FASE 3 — Operación y hardening (post-launch, continuo)

1. **Conciliación**: job/endpoint admin que compara `course_purchases` + estado de preapprovals contra la API de MP (detecta webhooks perdidos). Correr semanal al principio.
2. **Refunds**: política (¿7 días cursos?) + procedimiento (panel MP) + reflejar `refunded` en DB (webhook `payment.refunded` ya entraría por el mismo topic).
3. **Facturación / AFIP**: MP no factura por nosotros. Decisión de Agus/contador (facturador electrónico o servicio tipo TusFacturas). Fuera del alcance técnico inicial — dejar campo `invoice_ref` previsto.
4. **Monitoreo**: alerta Sentry en errores de webhook + log estructurado de eventos de billing; métrica semanal simple (altas, bajas, cursos vendidos) leída de la DB.
5. **Runbook** (`docs/RUNBOOK_PAGOS.md`): qué hacer ante "pagué y no tengo acceso" (buscar payment en MP → conciliar → aplicar a mano), webhook caído, cambio de precio (versionar el plan en MP, no editar).
6. **Seguridad**: ya hay firma HMAC + fetch-real-desde-MP + idempotencia; sumar rate-limit al webhook y al checkout de cursos.

---

## 7) División del trabajo

| Quién | Qué |
|---|---|
| **Agus** | Cuenta/panel MP (credenciales, plan, webhook, env en Railway), decisión de fulfillment de cursos, revenue share, facturación/AFIP, publicar Netlify |
| **Nosotros** | Todo el código (backend + frontend + tests + migraciones), sandbox E2E, hardening, runbook, conciliación |
| **Juntos** | Lectura de demanda para priorizar cursos, go-live, primera semana de monitoreo |

## 8) Riesgos y decisiones abiertas

1. **Fulfillment de cursos indefinido** (¿qué recibe el que paga $220.000?) — **bloqueante de Fase 2**, es LA decisión de negocio. La técnica está clara.
2. ¿Comprar cursos sin suscripción activa? (propuesta: sí — §2.5).
3. Facturación AFIP: no resuelta; riesgo impositivo si se vende sin facturar.
4. Grace period: definir días y comportamiento exacto (propuesta: 5 días con banner).
5. MP Preapproval + Checkout Pro en la misma cuenta: sin conflicto técnico, pero el webhook recibirá ambos topics — por eso el dispatch por topic es parte de Fase 2.
6. Precios de cursos viven en un JSON versionado (deploy para cambiar precio). Aceptable hoy; si Academia crece, mover a DB (ya hay admin-academia como semilla).

## 9) Secuencia y esfuerzo total

```
FASE 0  Activación MP (Agus)            ~2-3 h Agus + 1 h nuestro   ← bloqueante
FASE 1  Suscripción live                ~2-3 días nuestro           ← primer revenue
FASE 2  Cursos                          ~3-4 días nuestro           ← tras leer demanda + definir fulfillment
FASE 3  Operación                       ~1-2 días + continuo
```

**Camino crítico**: Fase 0 → Fase 1 (la suscripción ya está casi construida; es
la vía más corta a cobrar). Fase 2 arranca en paralelo apenas Agus defina el
fulfillment y la demanda diga qué cursos valen el checkout.
