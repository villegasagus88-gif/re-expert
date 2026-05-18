# Tests de billing — Tarea #48

Cobertura de tests para el flujo completo de facturación: webhook de Stripe (eventos mock con firma + idempotencia) y gating de features por plan.

## Mapa checklist → test

| Checklist                              | Archivo                              | Test                                                         |
|----------------------------------------|--------------------------------------|--------------------------------------------------------------|
| Mock webhook Stripe                    | `tests/test_stripe_webhook.py`       | helpers `_make_user`, `_MockDB`, `_signed_body` montan eventos firmados sin red |
| Test checkout → plan pro               | `tests/test_stripe_webhook.py`       | `test_checkout_session_completed_activates_pro`              |
| Test payment failed                    | `tests/test_stripe_webhook.py`       | `test_invoice_payment_failed_downgrades_to_free`             |
| Test subscription deleted → free       | `tests/test_stripe_webhook.py`       | `test_subscription_deleted_downgrades_to_free`               |
| Test firma inválida → 400              | `tests/test_stripe_webhook.py`       | `test_webhook_400_on_bad_signature_when_secret_configured`   |
| Test gating features                   | `tests/test_plan_gating.py`          | 12 tests — ver detalle abajo                                 |

Casos extra ya cubiertos en `test_stripe_webhook.py` (defensa en profundidad):

- `test_webhook_does_not_require_jwt` — el endpoint no exige `Authorization`
- `test_webhook_503_when_stripe_not_configured` — falla limpia si falta `STRIPE_SECRET_KEY`
- `test_webhook_400_on_malformed_json` — body no-JSON ⇒ 400
- `test_webhook_400_on_event_without_id` — evento sin `id` ⇒ 400
- `test_unknown_event_type_is_ignored` — eventos no soportados no rompen
- `test_duplicate_event_is_skipped` — UNIQUE en `stripe_events.event_id` ⇒ idempotencia

Tests en `test_billing.py` cubren los endpoints `/api/billing/*`:

- 401 sin token (checkout / portal / status)
- 405 si checkout llega por GET
- 503 si Stripe no está configurado
- 400 si el usuario ya es Pro
- 503 si falta `STRIPE_PRICE_ID_PRO`
- happy-path: la sesión de Stripe devuelve `{url, session_id}`
- aliases legacy `/api/stripe/create-checkout-session` y `/api/stripe/portal`

## Detalle: gating (`test_plan_gating.py`)

| Test | Qué valida |
|---|---|
| `test_require_pro_passes_through_pro_user` | `require_pro` devuelve el user sin tocarlo si `plan == "pro"` |
| `test_require_pro_raises_403_for_free_user` | Free ⇒ `HTTPException(403)` |
| `test_require_pro_raises_403_for_unknown_plan` | Cualquier plan distinto de "pro" ⇒ 403 (no se eleva por error) |
| `test_require_pro_403_detail_is_structured_for_frontend` | El body 403 trae `message` / `plan_required` / `upgrade_url` para que el frontend pinte el upsell |
| `test_has_feature_pro_only_features_blocked_for_free` (×7) | Las 7 features Pro-only (`history_full`, `sol_assistant`, `project_dashboard`, `indicators_cpi_spi`, `data_ingest`, `export`, `priority_support`) están bloqueadas para free y abiertas para pro |
| `test_has_feature_shared_features_open_to_both` (×2) | `chat` y `knowledge_read` están abiertas en ambos planes |
| `test_has_feature_unknown_plan_falls_back_to_free` | Plan no listado ⇒ se trata como free (nunca como pro) |
| `test_has_feature_unknown_feature_returns_false` | Feature no listada ⇒ `False` para todos |
| `test_plan_features_table_has_both_plans` | `PLAN_FEATURES` declara ambos planes con el mismo set de keys (no hay gaps silenciosos) |
| `test_pro_only_route_returns_403_for_free_user` | Integración: ruta protegida por `require_pro` ⇒ 403 con detail estructurado |
| `test_pro_only_route_returns_200_for_pro_user` | Integración: misma ruta ⇒ 200 si el user es pro |

Las pruebas de integración usan un `FastAPI()` mínimo con un único endpoint `/pro-only` y `app.dependency_overrides[get_current_user]` para inyectar el user de test sin tocar la BD ni JWT.

## Estrategia general

- **Sin red**: todas las llamadas al SDK de Stripe se monkey-patchean (`patch("services.stripe_service.run_stripe", ...)`). Los webhooks construyen una firma HMAC-SHA256 válida usando el mismo `whsec_test_secret` con el que se patchea `settings.STRIPE_WEBHOOK_SECRET`.
- **Sin BD**: `models.base.get_db` se sustituye por `_MockDB`, una sesión async-stub que rastrea `add()` / `commit()` / `rollback()` y simula la UNIQUE constraint con `seen_event_ids: set[str]`.
- **Sin JWT real**: para los gating-tests se usa `app.dependency_overrides[get_current_user]` con un `MagicMock(spec=User)`.

## Cómo correrlos

```bash
cd backend
pytest tests/test_stripe_webhook.py tests/test_billing.py tests/test_plan_gating.py -v
```

En CI se ejecutan junto al resto de la suite (`pytest backend/tests`).

## Checklist (#48)

- [x] Mock webhook Stripe — helpers en `test_stripe_webhook.py`
- [x] Checkout completado activa Pro
- [x] Payment failed degrada a Free
- [x] Subscription deleted degrada a Free
- [x] Firma inválida ⇒ 400
- [x] Gating de features (require_pro + has_feature)
