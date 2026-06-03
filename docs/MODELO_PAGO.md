# Modelo pago-only con trial — Spec de diseño

> **Estado: PROPUESTA — EN REVISIÓN.** El trial queda a confirmar entre Mati y
> Agustín antes de implementar. Este doc es la base para esa conversación.
> NO hay código implementado todavía: define QUÉ se va a construir y deja las
> decisiones de negocio explícitas al final.
>
> Reemplaza el modelo freemium documentado en [PLANS.md](./PLANS.md) (que queda
> obsoleto cuando esto se apruebe).

---

## 1. Decisión

RE Expert deja de ser freemium. **No existe más el plan `free`** — se elimina del
código, del pricing y de los docs. El producto es de pago (un solo plan), con un
**trial de evaluación de 7 días** al registrarse.

## 2. Estados de plan

El campo `profiles.plan` pasa a tener estos valores (se elimina `free`):

| Estado | Significado | Acceso | Cómo se llega |
|--------|-------------|--------|---------------|
| `trial` | Período de evaluación de 7 días | ✅ completo, hasta `trial_ends_at` | Al registrarse |
| `pro` | Suscripción paga activa | ✅ completo | Webhook de Stripe al cobrar |
| `inactive` | Trial vencido o suscripción cancelada/caída | ❌ paywall | Trial expira, o webhook `subscription.deleted` / `payment_failed` |

- Se agrega la columna `profiles.trial_ends_at` (timestamptz, nullable).
- **Acceso** = `plan == "pro"` **o** (`plan == "trial"` y `now() < trial_ends_at`).
  El vencimiento del trial se evalúa al vuelo en cada request — **no hace falta
  un cron** que cambie el estado (aunque opcionalmente el scheduler diario puede
  marcar `trial`→`inactive` para reportes).

## 3. Gate de acceso (backend)

Nuevo helper y dependency en `core/plan_gate.py`:

```python
def has_access(user) -> bool:
    if user.plan == "pro":
        return True
    if user.plan == "trial" and user.trial_ends_at:
        return datetime.now(UTC) < user.trial_ends_at
    return False

def require_access(user = Depends(get_current_user)) -> User:
    if not has_access(user):
        raise HTTPException(403, detail={
            "message": "Tu período de prueba terminó. Suscribite para seguir usando RE Expert.",
            "reason": "trial_expired" | "no_subscription",
            "upgrade_url": "/pricing.html",
        })
    return user
```

Se aplica **a nivel router** en `main.py` a todo lo de producto:
`chat, conversations, workspaces, profile, project, payments, materials, news,
academia, sol/agent, contacts, reminders, channels, ingest, knowledge`.

**NO se gatea** (si no, nadie podría loguearse ni pagar): `auth`, `billing`,
`stripe`, `health`, y las páginas públicas. El `require_pro` actual de SOL se
reemplaza por `require_access` (el trial incluye SOL).

Esto cierra de paso el hallazgo de la auditoría: hoy `project`/`ingest`/`export`
no estaban gateados. Con el gate global, queda cubierto.

## 4. Rate limits y features (`config/plans.py`)

- `PLAN_LIMITS`: solo `pro` (50/h, 200/día). `trial` usa los mismos límites (no
  friccionar la evaluación). Se elimina `free`.
- `PLAN_FEATURES`: `trial` y `pro` = todas las features en `True`. Se elimina
  `free`. (Con gate de acceso binario, las flags por-feature pierden relevancia;
  se mantienen por compatibilidad del `/api/billing/status`.)
- `PLAN_PRICING`: un solo plan (`pro`, USD 19/mes). Se elimina `free`.
- `has_feature`/`limits_for`: el fallback de plan desconocido pasa de `free` a
  "sin acceso" (todo `False` / límite mínimo).

## 5. Migración (Alembic `0017`)

- `ADD COLUMN trial_ends_at timestamptz NULL` en `profiles`.
- Cambiar `server_default` de `plan` de `'free'` a `'trial'`.
- **Backfill de usuarios existentes** (pre-launch, son de test): `plan='free'` →
  `plan='trial'`, `trial_ends_at = now() + 7 días`. *(Decisión a confirmar — ver §8.)*
- `register_user` pasa a crear `plan="trial"`, `trial_ends_at = now() + 7 días`.

## 6. Frontend

- `pricing.html`: un solo plan (saco la comparativa free/pro). Copy: "7 días de
  prueba gratis, después USD 19/mes".
- `app.html`: banner "Te quedan N días de prueba" (de `trial_ends_at`); el handler
  de `403` con `reason: trial_expired/no_subscription` dispara el paywall
  (`showUpgradeModal`, que ya existe).
- `account.html`: estado de suscripción (trial con días restantes / pro / vencido).
- Quitar toda copy que mencione "gratis"/"free" como tier.

## 7. Dependencia de Stripe y transición

- El **trial funciona sin Stripe** (no requiere activación): da acceso 7 días.
- El **cobro** (pasar de `trial`/`inactive` → `pro`) requiere que Agustín active
  Stripe (`STRIPE_WEBHOOK_SECRET` + `STRIPE_PRICE_ID_PRO`). El checkout ya está
  cableado (`/api/billing/checkout`).
- **Transición:** mientras Stripe no esté activo, un trial vencido queda sin
  forma de pagar. Irrelevante pre-launch, pero es la razón por la que el trial
  (7 días) debe cubrir el período hasta que Stripe esté listo. **No desplegar el
  paywall a prod hasta que Stripe esté activo**, o nadie podrá pagar.

## 8. Decisiones abiertas — para conversar con el socio

1. **Duración del trial:** 7 días (propuesto por Mati). ¿Confirmás?
2. **¿Trial pide tarjeta upfront?** Sin tarjeta (más registros, más fricción al
   cobrar) vs. con tarjeta (menos registros, conversión automática). Afecta el
   flujo de Stripe Checkout (`trial_period_days` en la subscription).
3. **Usuarios existentes** en la migración: ¿trial nuevo de 7 días, `inactive`
   directo, o `pro` de cortesía? (Pre-launch hay pocos/ninguno real.)
4. **Período de gracia** tras vencer el trial (ej. 3 días de recordatorios antes
   de cortar) — ¿sí o corte seco?
5. **Precio:** USD 19/mes confirmado. ¿Plan anual con descuento?
6. **Orden de deploy:** el paywall a prod recién cuando Stripe esté activo (§7).

## 9. Plan de implementación (cuando se apruebe)

Orden, todo en `merge/launch-mvp-into-main`, sin tocar prod hasta el OK final:

1. `config/plans.py` — eliminar `free`, agregar `trial`, ajustar fallbacks.
2. `models/user.py` + migración `0017` — `trial_ends_at`, default `trial`, backfill.
3. `core/plan_gate.py` — `has_access` + `require_access`.
4. `main.py` — aplicar `require_access` a los routers de producto.
5. `services/auth_service.py` — `register_user` setea trial.
6. `services/stripe_service.py` — downgrade a `inactive` (no `free`).
7. `api/routes/chat.py` + `agent.py` — SOL `require_pro` → `require_access`.
8. `api/routes/billing.py` — `/status` refleja trial/pro/inactive + `trial_ends_at`.
9. Frontend — pricing, banner trial, paywall en 403, account.
10. Tests — `has_access`/`require_access`, registro crea trial, gate bloquea inactive.
11. Actualizar `PLANS.md` (o reemplazarlo por este doc) y `.env.example`.

Estimación: ~1 día de implementación + verificación. Reversible (un commit).
