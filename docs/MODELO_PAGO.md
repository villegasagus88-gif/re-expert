# Modelo pago-only con trial + Mercado Pago — Spec de diseño

> **Estado: decisiones de producto tomadas (Mati, 2026-06-03).** Pendiente para
> implementar a fondo: credenciales de Mercado Pago (Agustín) y el precio final
> en pesos. Reemplaza el modelo freemium de [PLANS.md](./PLANS.md) (queda obsoleto).

---

## 1. Decisión

RE Expert deja de ser freemium. **El plan `free` se elimina del proyecto** (código,
pricing, docs). El producto es de pago, con un **trial de 7 días** al registrarse,
**con tarjeta upfront** (se pide medio de pago al empezar; al día 7 cobra solo).
Cobro vía **Mercado Pago** (pensado para pesos argentinos).

Decisiones confirmadas:
- Trial: **7 días** (configurable por env var, se puede cambiar).
- **Tarjeta upfront:** sí — el trial requiere cargar medio de pago al inicio.
- **Corte seco** al vencer (sin período de gracia).
- Pasarela: **Mercado Pago** (Stripe queda en el código, deshabilitado, para un
  eventual cobro internacional futuro).
- Precio: **a definir, probablemente en ARS** (Agustín lo configura en MP).

## 2. Estados de plan

`profiles.plan` (se elimina `free`):

| Estado | Significado | Acceso |
|--------|-------------|--------|
| `trial` | Evaluación 7 días (con tarjeta ya cargada en MP) | ✅ hasta `trial_ends_at` |
| `pro` | Suscripción paga activa | ✅ |
| `inactive` | Trial vencido / suscripción cancelada o caída | ❌ paywall |

- Nueva columna `profiles.trial_ends_at` (timestamptz, nullable).
- **Acceso** = `pro` **o** (`trial` y `now() < trial_ends_at`). Se evalúa al vuelo.

## 3. Gate de acceso (backend)

`core/plan_gate.py`: `has_access(user)` + dependency `require_access` (403 con
`{message, reason, upgrade_url}`). Se aplica **a nivel router** en `main.py` a todo
lo de producto (chat, conversations, workspaces, profile, project, payments,
materials, news, academia, sol/agent, contacts, reminders, channels, ingest,
knowledge). **No se gatea**: auth, billing/pagos, health. El `require_pro` de SOL
pasa a `require_access`. (Esto cierra el hallazgo de la auditoría: project/ingest/
export quedan gateados.)

## 4. Pasarela: Mercado Pago (suscripciones)

Reemplaza a Stripe como cobro principal. MP soporta suscripciones con `preapproval`
(débito recurrente) y período de prueba.

- **Servicio nuevo** `services/mercadopago_service.py` (SDK `mercadopago` o REST).
- **Flujo:** registro → `POST /api/mercadopago/subscribe` crea un `preapproval`
  (con `free_trial` de 7 días + medio de pago) → redirección al checkout de MP →
  el usuario carga la tarjeta → MP arranca el trial → al día 7 cobra automático.
- **Webhook** `POST /api/mercadopago/webhook`: MP notifica altas/cobros/bajas.
  Verificar la firma (`x-signature`), idempotencia por `id` de notificación
  (espejo de cómo está hecho hoy con Stripe). Mapear:
  - pago aprobado / suscripción activa → `plan = "pro"`.
  - suscripción cancelada / pago rechazado → `plan = "inactive"`.
- **Credenciales (Agustín, por env var — NO se activan desde el chat):**
  `MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`, `MP_WEBHOOK_SECRET`, y el `preapproval_plan`
  con el precio en ARS configurado en el panel de MP.
- **Stripe:** el código actual (`billing.py`, `stripe_routes.py`, `stripe_service.py`)
  queda pero deshabilitado (sin env vars). Se documenta como "futuro internacional".

> **Nota de la integración:** confirmar contra la doc oficial de MP el recurso
> exacto (`preapproval` vs `preapproval_plan`) y si el free-trial de MP encaja, o
> si conviene manejar el trial nosotros (estado `trial` local) y crear el
> `preapproval` para que el primer cobro caiga al día 7.

## 5. Rate limits y features (`config/plans.py`)

- `PLAN_LIMITS`: solo `pro` (50/h, 200/día); `trial` usa los mismos. Se elimina `free`.
- `PLAN_FEATURES`: `trial` y `pro` todo `True`. Se elimina `free`.
- `PLAN_PRICING`: un solo plan, monto en ARS (a definir). Se elimina `free`.
- Fallback de plan desconocido: sin acceso.

## 6. Migración (Alembic `0017`)

- `ADD COLUMN trial_ends_at timestamptz NULL`; `server_default` de `plan` → `trial`.
- **No hay usuarios reales** (solo Mati, Agustín y la cuenta demo) → el backfill es
  trivial: las cuentas existentes pasan a `trial` (o `pro` de cortesía para los
  dueños). `register_user` setea `plan="trial"` + `trial_ends_at = now()+7d`.

## 7. Frontend

- `pricing.html`: un solo plan en ARS (saco comparativa free/pro). Copy "7 días
  gratis, después $X/mes".
- Registro/onboarding: integrar el alta de suscripción de MP (tarjeta upfront).
- `app.html`: banner "Te quedan N días de prueba"; el `403` de `require_access`
  dispara el paywall (`showUpgradeModal`, ya existe).
- `account.html`: estado (trial con días / pro / vencido) + link al checkout MP.

## 8. Orden de deploy (recomendación — "lo mejor para nosotros")

1. Implementar TODO en `merge/launch-mvp-into-main` (modelo + MP + front + tests).
2. **No desplegar el paywall a prod hasta que MP esté activo y testeado** (si no,
   nadie podría completar el alta). Mientras tanto, Mati y Agustín usan la app con
   cuentas demo (sin paywall).
3. Cuando Agustín cargue las credenciales MP y se pruebe un alta+cobro de prueba
   (sandbox de MP), recién ahí merge a `main`.

## 9. Plan de implementación (cuando estén las credenciales MP)

1. `config/plans.py` — eliminar `free`, agregar `trial`, ARS.
2. `models/user.py` + migración `0017` — `trial_ends_at`, default `trial`.
3. `core/plan_gate.py` — `has_access` + `require_access`.
4. `main.py` — `require_access` en routers de producto.
5. `services/auth_service.py` — registro crea trial.
6. `services/mercadopago_service.py` + `api/routes/mercadopago.py` — subscribe + webhook.
7. `api/routes/chat.py` + `agent.py` — SOL → `require_access`.
8. Frontend — pricing ARS, alta MP, banner trial, paywall.
9. Tests — `has_access`, gate, registro-trial, webhook MP (idempotencia + firma).
10. Docs — reemplazar `PLANS.md`, actualizar `.env.example` con vars MP, `APIS_EXTERNAS_Y_COSTOS.md`.

Estimación: ~2 días (la integración MP + su webhook es el grueso). Reversible.

## 10. Pendiente de Agustín / definir

- Credenciales de Mercado Pago (`MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`, `MP_WEBHOOK_SECRET`).
- Crear el plan de suscripción en MP con el **precio en ARS**.
- Confirmar precio final.
