# Stripe — Setup y operación

> Endpoints canónicos viven en `backend/api/routes/billing.py`. Los `/api/stripe/*` siguen activos como alias por compat con el frontend desplegado.

## Endpoints

| Método | Path                                | Auth | Descripción                                                  |
| ------ | ----------------------------------- | ---- | ------------------------------------------------------------ |
| POST   | `/api/billing/checkout`             | JWT  | Crea Checkout Session de Stripe — devuelve `{url, session_id}` |
| POST   | `/api/billing/portal`               | JWT  | Abre Billing Portal — devuelve `{url}`                       |
| GET    | `/api/billing/status`               | JWT  | Plan + suscripción + facturas (best-effort)                  |
| POST   | `/api/stripe/webhook`               | —    | Recibe eventos de Stripe (firma verificada)                  |
| POST   | `/api/stripe/create-checkout-session` | JWT | Alias legacy de `/api/billing/checkout`                      |
| POST   | `/api/stripe/portal`                | JWT  | Alias legacy de `/api/billing/portal`                        |
| GET    | `/api/stripe/status`                | JWT  | Versión liviana de status (solo plan + is_pro)               |

## Setup en Stripe Dashboard

1. **Crear cuenta** en https://dashboard.stripe.com (modo Test al principio).
2. **Crear producto:**
   - Nombre: `RE Expert Pro`
   - Descripción: `Suscripción mensual al plan Pro de RE Expert`
3. **Crear precio recurrente:**
   - Tipo: Recurring
   - Monto: `19 USD` / mes
   - Billing period: Monthly
   - Anotar el `price_id` (formato `price_...`) → va en `STRIPE_PRICE_ID_PRO`.
4. **Activar Customer Portal** en Settings → Billing → Customer portal:
   - Permitir cancelar suscripción.
   - Permitir actualizar método de pago.
   - Configurar política de cancelación (recomendado: end of billing period).
5. **Configurar webhook** en Developers → Webhooks → Add endpoint:
   - URL: `https://<tu-dominio>/api/stripe/webhook`
   - Eventos:
     - `checkout.session.completed` → activa plan Pro
     - `customer.subscription.deleted` → vuelve a free
     - `customer.subscription.paused` → vuelve a free
   - Anotar el `signing secret` (formato `whsec_...`) → va en `STRIPE_WEBHOOK_SECRET`.

## Variables de entorno

```ini
STRIPE_SECRET_KEY=sk_test_...           # secret key del modo Test (o Live en prod)
STRIPE_WEBHOOK_SECRET=whsec_...         # signing secret del webhook
STRIPE_PRICE_ID_PRO=price_...           # price del producto RE Expert Pro mensual
STRIPE_SUCCESS_URL=https://app.example.com/success.html
STRIPE_CANCEL_URL=https://app.example.com/pricing.html
```

Si `STRIPE_SECRET_KEY` está vacío, los endpoints `/api/billing/checkout` y `/api/billing/portal` devuelven `503` con mensaje "Stripe no configurado". `/api/billing/status` no falla — devuelve solo `plan` / `email`.

## Flujo de pago

```
[ Usuario logueado en Free ]
        │
        ▼  click "Suscribirse" en pricing.html
        │
        ▼  POST /api/billing/checkout  (Authorization: Bearer <jwt>)
        │
        ▼  responde { url: "https://checkout.stripe.com/..." }
        │
        ▼  redirect del browser a esa URL
        │
        ▼  paga en Stripe-hosted page → Stripe redirige a STRIPE_SUCCESS_URL
        │
        ▼  Stripe envía evento checkout.session.completed → POST /api/stripe/webhook
        │
        ▼  webhook actualiza user.plan = "pro" + user.stripe_customer_id
        │
        ▼  success.html muestra "¡Suscripción activada!"
```

## Test cards (modo Test)

| Card                        | Resultado                          |
| --------------------------- | ---------------------------------- |
| `4242 4242 4242 4242`       | Pago aprobado                      |
| `4000 0000 0000 9995`       | Fondos insuficientes               |
| `4000 0000 0000 0002`       | Card declined (genérico)           |
| `4000 0025 0000 3155`       | Requiere autenticación 3DS         |

CVC: cualquier 3 dígitos. Vencimiento: cualquier fecha futura. ZIP: cualquier código.

Más en: https://stripe.com/docs/testing

## Probar webhook localmente

```bash
# 1. Instalar Stripe CLI
brew install stripe/stripe-cli/stripe

# 2. Login
stripe login

# 3. Forward webhooks al backend local
stripe listen --forward-to http://localhost:8000/api/stripe/webhook
# → te imprime un signing secret efímero — pegalo en STRIPE_WEBHOOK_SECRET

# 4. Disparar evento de prueba
stripe trigger checkout.session.completed
```

## Manejo de errores

`services/stripe_service.py` traduce `stripe.error.StripeError` a `HTTPException(502)` con `detail = exc.user_message or str(exc)`. La frontend en `pricing.html` muestra el `detail` recibido (mensaje localizable por Stripe) o un mensaje genérico de fallback.

Casos cubiertos:
- `503` → Stripe no configurado / `STRIPE_PRICE_ID_PRO` ausente
- `400` → usuario ya tiene Pro / no tiene `stripe_customer_id` (al abrir portal)
- `401` → JWT inválido / faltante
- `502` → error en la llamada a Stripe (timeout, price inexistente, etc.)

## MercadoPago

Decisión: arrancamos con Stripe en USD. Razones:
- Cobro en USD ya soportado, no requiere conversión.
- Customer Portal robusto para autoservicio (cancelación, cambio de tarjeta).
- Mejor compatibilidad con tarjetas extranjeras (target inicial: PyMEs constructoras / arquitectos que ya operan en dólares).

MercadoPago se evaluará en una fase posterior si necesitamos cobrar en ARS o aceptar débito local.
