# Fase 1 — Wire-ups playbook

> Activar features ya construidas pegando env vars en Railway +
> configurando 1-2 cosas en dashboards externos. **Cero código nuevo.**
> Estimación total: 1.5 horas reales.

**Estado del código:** ✅ Verificado code-ready. Cada feature se activa
sola al detectar la env var. Sin env var, queda en modo "disabled
gracefully" (no rompe nada).

---

## Orden recomendado de ejecución

| # | Wire-up | Tiempo | Quién | Desbloquea |
|---|---------|--------|-------|------------|
| 1 | **Gemini API key** (fallback gratis) | 5 min | Mati | Resilencia chat sin saldo Anthropic |
| 2 | **Resend API key + FROM** | 5 min | Mati | Emails reales de forgot-password |
| 3 | **UptimeRobot** anti-sleep | 5 min | Mati | Sin cold starts en prod |
| 4 | **Sentry project + DSNs** | 15 min | Mati o socio | Visibilidad errores prod |
| 5 | **Stripe checkout + webhook** | 20 min | Socio | Pro plan operativo |
| 6 | **(Opcional) Dominio Resend** | 30 min + DNS | Socio | FROM `hola@<dominio>` |

Total: ~50 min activos + 30 min propagación DNS (opcional).

---

## 1️⃣ Gemini API key (5 min) — fallback gratis

**Qué activa:** si Anthropic se queda sin saldo o tira 5xx, el chat
automáticamente usa Gemini 2.5 Flash (free tier: 15 RPM, 1M tok/día).

### Pasos
1. https://aistudio.google.com/apikey (login con la cuenta Google que quieras).
2. **Create API key** → seleccionar un proyecto Google Cloud (cualquiera, o "Sin proyecto").
3. **Copy** la key (`AIzaSy...`).

### En Railway
Variables tab → **Raw Editor** → agregar al final:

```env
GEMINI_API_KEY=AIzaSy....
LLM_PROVIDER=auto
```

### Smoke test
Esperá 1 min al redeploy de Railway, después:

```bash
# Forzar el chat con Gemini explícito vía override temporal:
# (Si LLM_PROVIDER=auto, usa Gemini si Anthropic falla)
# No hace falta cambiar nada — el primer error 400/429 de Anthropic
# dispara fallback automático.
```

Verificación pasiva: el chat sigue respondiendo aunque te quedes sin
créditos Anthropic.

---

## 2️⃣ Resend API key (5 min)

**Qué activa:** los emails de forgot-password se envían reales (Resend
free tier = 3000 emails/mes). Sin esto, el flow funciona pero el link
queda solo en los logs de Railway.

### Pasos
1. https://resend.com/api-keys (ya tenés cuenta).
2. **Create API Key** →
   - Name: `re-expert-prod`
   - Permission: **Sending access** (no Full access, por security)
   - Domain: **All domains** (cambiamos cuando verifiques uno custom)
3. **Add** → copiar la key (`re_xxxxxxxxxxxxxxx`) AHORA, Resend la muestra una sola vez.

### En Railway
Variables tab → Raw Editor → agregar:

```env
RESEND_API_KEY=re_xxxxxxxxxxxxxxx
RESEND_FROM=onboarding@resend.dev
```

> ⚠️ **`onboarding@resend.dev`** es el sandbox de Resend.
> **Limitación:** solo manda al email del OWNER de la cuenta Resend
> (matiasparola100@gmail.com). Suficiente para test interno.
> Para usuarios reales hace falta verificar un dominio (paso 6).

### Smoke test

```bash
# Disparar un forgot password con tu email:
curl -X POST https://re-expert.netlify.app/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"matiasparola100@gmail.com"}'
```

Revisar tu inbox de Gmail en 30s-2min. Debería llegar un email con
"Restablecé tu contraseña — RE Expert" + botón + link.

Si no llega:
- Resend dashboard → **Logs** → buscar el email.
- Si dice "sandbox limit": estás mandando a un email distinto del
  owner. Solución: verificar dominio (paso 6).
- Si dice "Invalid API key": revisar la key pegada en Railway.

---

## 3️⃣ UptimeRobot (5 min)

**Qué activa:** keepalive del backend Railway. Aunque pagaron Railway,
si hay 5-10 min de inactividad, el primer request del día tarda
30-60s. UptimeRobot pinguea cada 5 min y mantiene el servicio warm +
te avisa por email si /health se cae.

### Pasos
1. https://uptimerobot.com → **Sign up free** (no requiere tarjeta).
2. Dashboard → **+ Add New Monitor**.
3. Configurar:
   - Type: **HTTPS**
   - Friendly Name: `RE Expert API`
   - URL: `https://re-expert-production.up.railway.app/health`
   - Monitoring Interval: **5 minutes**
   - Alert Contacts: tu email
4. **Create Monitor**.

### Smoke test
Esperá ~6 min y revisar el monitor: debería mostrar "Up" en verde con
response time ~500-800ms.

---

## 4️⃣ Sentry (15 min)

**Qué activa:** error tracking en producción. Cualquier 5xx, exception
o JS error en el browser se loggea con stacktrace, breadcrumbs y user
context (sin PII gracias al filtro del `sentry.js`).

### Pasos
1. https://sentry.io → **Sign up free** (50k events/mes free).
2. Crear nueva organización (o usar la que ya tengas).
3. **Create Project** → backend:
   - Platform: **Python → FastAPI**
   - Project name: `re-expert-backend`
   - **Create Project**
   - Copiar el **DSN** (formato `https://xxxxx@xxxxx.ingest.sentry.io/yyyy`).
4. **Create Project** → frontend:
   - Platform: **JavaScript → Browser**
   - Project name: `re-expert-frontend`
   - Copiar el DSN.

### En Railway (backend DSN)
Raw Editor:

```env
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/yyyy
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

### En Netlify (frontend DSN)
Hay 2 opciones:

**A) Hardcodear en `frontend/config.js`** (más simple):
- Editar línea `SENTRY_DSN: ''` → `SENTRY_DSN: 'https://aaaaa@...ingest.sentry.io/bbbb'`
- Commit + push → Netlify redeploya solo.
- El DSN del frontend Sentry está pensado para ser público, no es secret.

**B) Build env var en Netlify** (más limpio, opcional):
- Netlify dashboard → site settings → **Environment variables** → agregar `VITE_SENTRY_DSN`.
- Modificar `config.js` para que lea de `import.meta.env.VITE_SENTRY_DSN` (requiere build step, hoy no tenés).

Opción A es la rápida.

### Smoke test
1. Forzar un error backend: `curl https://re-expert-production.up.railway.app/api/this-route-does-not-exist`
2. Forzar un error frontend: abrir DevTools en `re-expert.netlify.app/app.html` y ejecutar `throw new Error('test sentry')`.
3. En Sentry dashboard → **Issues** → debería aparecer un issue en ~30s.

---

## 5️⃣ Stripe (20 min)

**Qué activa:** checkout para Pro plan + portal de billing + webhooks
para activar/cancelar suscripciones automáticamente.

### Pasos (tu socio, porque tiene la cuenta Stripe)
1. https://dashboard.stripe.com → si está en test mode, OK para arrancar.
2. **API Keys** → copiar:
   - **Publishable key** (`pk_test_...` o `pk_live_...`) — para frontend
   - **Secret key** (`sk_test_...` o `sk_live_...`) — para backend
3. **Products** → **Add product**:
   - Name: `RE Expert Pro`
   - Price: USD 29/mes recurring
   - **Save** → copiar el **Price ID** (`price_xxx`)
4. **Developers → Webhooks** → **Add endpoint**:
   - URL: `https://re-expert-production.up.railway.app/api/stripe/webhook`
   - Events to listen:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.paid`
     - `invoice.payment_failed`
   - **Add endpoint** → copiar el **Signing secret** (`whsec_xxx`)

### En Railway
Raw Editor:

```env
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxx
STRIPE_PRICE_ID_PRO=price_xxxxxxxxxx
STRIPE_SUCCESS_URL=https://re-expert.netlify.app/success.html
STRIPE_CANCEL_URL=https://re-expert.netlify.app/pricing.html
```

### Smoke test
1. Login en `https://re-expert.netlify.app` con cualquier user.
2. Click "Upgrade" → debería abrir el checkout de Stripe.
3. Usar tarjeta de test `4242 4242 4242 4242` + cualquier CVV/fecha futura.
4. Después del pago: redirect a `/success.html`.
5. Volver a `/account.html` → debería mostrar `Plan: Pro`.

### Si algo falla
- `503 "Webhook no configurado"` → falta `STRIPE_WEBHOOK_SECRET` en Railway. **Esto es la protección crítica que metí: nunca acepta webhooks sin firma en prod.**
- Webhook delivery fails en Stripe dashboard → URL mal. Verificar
  que sea `https://re-expert-production.up.railway.app/api/stripe/webhook` (con `/api/stripe/`, no `/api/billing/`).

---

## 6️⃣ (Opcional) Verificar dominio en Resend (30 min + DNS)

**Cuándo:** cuando quieras mandar emails desde `hola@tudominio.com`
en lugar del sandbox `onboarding@resend.dev`. Requiere tener un
dominio comprado.

### Pasos
1. Resend dashboard → **Domains** → **Add Domain** → tu dominio.
2. Resend muestra 4-5 DNS records (TXT + MX + CNAMEs DKIM).
3. Ir al registrar (Cloudflare, Namecheap, NIC.ar) → pegar los records.
4. Volver a Resend → **Verify** (5-30 min después de DNS propagation).
5. Una vez verde, en Railway cambiar:
   ```env
   RESEND_FROM=RE Expert <hola@tudominio.com>
   ```

---

## Checklist final de Fase 1

Una vez completados los 5 wire-ups críticos:

- [ ] Chat sigue respondiendo aunque Anthropic falle (Gemini fallback)
- [ ] Forgot password manda email real al inbox del owner
- [ ] UptimeRobot muestra "Up" verde
- [ ] Sentry recibe un issue de prueba
- [ ] Pricing → Upgrade → tarjeta test 4242 → user pasa a Pro
- [ ] Account muestra plan Pro
- [ ] Webhook de Stripe registra eventos en `/dashboard/stripe/status`

---

## Después de Fase 1

Cuando todo esto esté ✅, avanzamos a:

- **Fase 3 (1 día):** optimizaciones de costo Anthropic (-80% costo/usuario)
- **Fase 2 (2.5 días):** Academia + Noticias + Project flow inicial
- **Fase 4 (3 días):** Quality + monitoring + tests E2E

Ver `docs/ROADMAP_POST_CHAT.md` para el roadmap completo.
