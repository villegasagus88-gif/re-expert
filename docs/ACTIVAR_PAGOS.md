# Activar pagos — datos que hay que cargar (2026-07-02)

> **TL;DR**: el código de pagos (suscripción Pro + cursos de Academia) está
> **construido, testeado y deployado**, pero **inerte**. Se prende solo cuando
> se cargan 4 variables de entorno en Railway. No hay que tocar código.

Toda la pasarela funciona **dentro de la app** con **redirect a Mercado Pago**
(Checkout Pro para cursos, Preapproval para la suscripción). Nunca manejamos
datos de tarjeta: MP cobra, y el acceso queda registrado en nuestra base.

---

## 1) Lo que hay que crear en el panel de Mercado Pago (Agus)

En https://www.mercadopago.com.ar/developers → tu aplicación:

1. **Credenciales de producción** → copiar el **Access Token** y la **Public Key**.
   (Primero se puede probar con las credenciales de **test/sandbox** — mismo
   procedimiento, la app las acepta igual.)
2. **Plan de suscripción** (preapproval_plan): $69.900/mes, moneda **ARS**,
   con período de prueba de 7 días → copiar el **plan_id**.
3. **Webhook / Notificaciones**: registrar esta URL
   ```
   https://re-expert-production.up.railway.app/api/billing/mp/webhook
   ```
   Suscribir los topics **payment** (cursos) y **subscription_preapproval**
   (suscripción). MP te da una **clave secreta de firma** → copiarla.

---

## 2) Variables a cargar en Railway (servicio del backend)

Railway → proyecto → Variables. Cargar estas 4 (las 2 opcionales solo si aplican):

| Variable | De dónde sale | Obligatoria |
|---|---|---|
| `MP_ACCESS_TOKEN` | Access Token del paso 1.1 (secreto) | **Sí** |
| `MP_PLAN_ID` | plan_id del paso 1.2 | **Sí** (para la suscripción) |
| `MP_WEBHOOK_SECRET` | clave de firma del webhook, paso 1.3 | **Sí** (en prod, si falta, el webhook rechaza con 503 — fail-closed a propósito) |
| `MP_PUBLIC_KEY` | Public Key del paso 1.1 | Opcional (no se usa en el flujo redirect) |
| `MP_BACK_URL` | URL de retorno post-pago | Opcional. Default = `FRONTEND_URL/app.html` |
| `FRONTEND_URL` | ya debería estar seteada (dominio del front) | Ya seteada |

> **Importante**: mientras `MP_ACCESS_TOKEN` **o** `MP_PLAN_ID` estén vacías,
> TODO el módulo de MP queda apagado y la app se comporta como hoy. Los cursos
> pagos caen al flujo de "registrar interés" y la suscripción usa el fallback
> legacy. **Cargar las variables es lo único que hace falta para prender los pagos.**

Al guardar variables, Railway redeploya solo. La migración de base
(`0023_course_purchases`, tabla de compras de cursos) ya corrió en el último
deploy.

---

## 3) Cómo verificar que quedó activo (nosotros, 5 min)

Con las credenciales de **test** primero:

1. `GET https://re-expert-production.up.railway.app/api/billing/mp/config`
   → debe devolver `{"enabled": true, ...}` (hoy da `enabled:false`).
2. En la app, **Academia → un curso pago → "Comprar · $X"** → debe redirigir a
   Mercado Pago. Pagar con una **tarjeta de prueba** de MP.
3. Al volver, la app muestra "¡Pago acreditado!" y el curso queda con el badge
   **"✓ Tenés este curso"** (lo aplica el webhook `payment`).
4. **Suscripción**: desde el paywall, "Suscribirme" → redirect a MP → pagar de
   prueba → al volver, el plan pasa a Pro (lo aplica el webhook `preapproval`).

Cuando el sandbox pase, repetir con credenciales de **producción**.

---

## 4) Lo que YA está construido (no hay que hacerlo)

- **Suscripción Pro**: servicio, checkout (redirect), webhook con verificación
  de firma HMAC (fail-closed en prod), cancelación, gate de acceso pago-only.
- **Cursos**: tabla `course_purchases` (entitlements), índice único parcial
  anti-doble-cobro, `POST /api/academia/checkout` (gratis → inscripción directa;
  pago → preference de Checkout Pro), `GET /api/academia/my-courses`, webhook
  `payment` idempotente, y la UI de compra en Academia (Comprar / Empezar gratis
  / Ya tenés el curso / Compra pendiente + toast de retorno de MP).
- **Seguridad**: el precio SIEMPRE sale del catálogo del backend (nunca del
  cliente); el acceso vive en nuestra DB; el webhook está firmado.

## 5) Decisión de negocio pendiente (Agus) — NO técnica

**¿Qué recibe quien paga un curso de $220.000?** El sistema cobra y marca el
curso como "comprado", pero el *fulfillment* (link al curso real, cupón, alta en
la institución, revenue share con el proveedor) es una decisión de negocio que
falta definir. Hasta definirla, conviene dejar activa **solo la suscripción** y
mantener los cursos pagos en "registrar interés" (que es el comportamiento por
defecto sin credenciales, o se puede afinar por curso).

Ver también: [PLAN_PAGOS_2026-07-01.md](PLAN_PAGOS_2026-07-01.md) y
[MODELO_PAGO.md](MODELO_PAGO.md).
