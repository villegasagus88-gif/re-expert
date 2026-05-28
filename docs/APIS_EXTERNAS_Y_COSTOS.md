# APIs externas — costos, propósito y setup

> Toda integración del sistema RE Expert con servicios de terceros vive
> en este doc. Mirá acá para saber **qué tenés que pagar, cuándo lo
> tenés que pagar y cómo lo activás**. Cada API se conecta al backend
> via env vars; si la env var está vacía, la feature queda **disabled
> gracefully** sin romper nada.

**Última actualización:** 2026-05-28.
**Total estimado mes 0 (sin usuarios pagos):** ~USD 10-30/mes.
**Total estimado a 100 usuarios activos:** ~USD 80-150/mes.

---

## Tabla resumen rápido

| API | Para qué | Free tier | Cuándo pagar | Costo a 100 users | Crítica |
|-----|----------|-----------|--------------|-------------------|---------|
| **Anthropic Claude** | Chat IA principal | $5 prueba | Inmediato (sin créditos no anda chat) | $30-80/mes con caching | 🔴 SÍ |
| **Railway** | Backend hosting | $5 créditos/mes | Plan Hobby $5/mes | $5-15/mes | 🔴 SÍ |
| **Supabase** | DB + Storage + Auth | 500MB DB / 1GB Storage | Cuando crezcas | $0 → $25/mes Pro | 🔴 SÍ |
| **Netlify** | Frontend hosting | 100GB BW/mes | Improbable corto plazo | $0 | 🟡 Importante |
| **Resend** | Emails (forgot pw, notifs) | 3.000 emails/mes | >100 emails/día | $0 → $20/mes | 🟡 Importante |
| **Gemini API** | Fallback chat (si Anthropic falla) | 15 req/min, 1M tok/día | Casi nunca free dura | $0 | 🟢 Opcional |
| **Sentry** | Error tracking | 5K errores/mes | Cuando crezcas | $0 → $26/mes | 🟢 Opcional |
| **Stripe** | Billing (Pro plan) | No tiene tier fijo | Por transacción 2.9% + $0.30 | Depende ingresos | 🟢 Si cobrás Pro |
| **UptimeRobot** | Uptime monitoring | 50 monitores | Improbable | $0 | 🟢 Opcional |
| **Google Maps** | Rutas optimizadas SOL | $200/mes en créditos | Solo si excede | $0 → variable | 🟢 Opcional v1.1 |
| **Twilio WhatsApp** | Notificaciones SOL via WhatsApp | $0 sandbox / $1 USD aprobación | Por mensaje | $5-15/mes | 🟢 Opcional v1.1 |
| **Telegram Bot** | Notificaciones SOL via Telegram | **Gratis siempre** | Nunca | $0 | 🟢 Opcional v1.1 |

---

## 🔴 APIs críticas (sin estas no funciona el MVP)

### 1. Anthropic Claude API — chat IA

**Para qué sirve:** es el motor del chat. Sin saldo en Anthropic, el
chat tira "Error generando respuesta". Todas las demás features de la
app funcionan, pero el producto pierde su core.

**Costo real:**
- Sin optimización: ~USD 0.05/query (Sonnet 4.6, 6.5K tokens promedio)
- Con prompt caching activo (Fase 3 del roadmap): ~USD 0.012/query (-77%)
- Con caching + Haiku para queries simples: ~USD 0.008/query (-84%)

**Proyección 100 users × 10 queries/día × 30 días:**
- Sin optimizar: USD 1.500/mes
- Optimizado (Fase 3): **USD 240/mes**
- Optimizado + Haiku selectivo: **USD 80-150/mes**

**Free tier:** USD 5 de créditos de prueba al crear cuenta.

**Setup paso a paso:**
1. Ir a https://console.anthropic.com
2. Login con email (Google OAuth disponible).
3. **Settings → Billing → Add Credits**.
4. Cargar USD 10-20 para empezar (rinde miles de queries con caching).
5. **Settings → API Keys → Create Key**.
6. Nombre: `re-expert-prod`. **Copiar la key (`sk-ant-api03-...`)**.
7. Pegarla en Railway → Variables → `ANTHROPIC_API_KEY`.

**Riesgo:** sin saldo el chat deja de andar. Auto-recharge en Anthropic
es opcional (recomendado activar con threshold low).

---

### 2. Railway — hosting backend (YA PAGADO)

**Para qué sirve:** corre el container del backend FastAPI 24/7.

**Plan actual:** Hobby (pagado por el socio).

**Costo:**
- Hobby: USD 5/mes (cubre uso bajo-medio).
- Pro: USD 20/mes (si excedés Hobby).
- Servicio actual: probablemente USD 5-10/mes.

**Setup:** ya está configurado. Doc completo en `docs/DEPLOY_RAILWAY.md`.

---

### 3. Supabase — DB + Storage + Auth

**Para qué sirve:** base de datos PostgreSQL + bucket de Storage para
archivos del knowledge base + (NO usamos su Auth, hicimos auth custom
con JWT propio).

**Free tier:**
- 500 MB de DB
- 1 GB de Storage
- 50.000 monthly active users
- Sin tarjeta requerida

**Cuándo pagar:** cuando excedas free tier. A 100-500 usuarios, free
tier alcanza.

**Costo Pro:** USD 25/mes — incluye 8GB DB, 100GB Storage, daily backups.

**Setup:** ya está configurado, owner es tu socio Agustín. Para
operación diaria ver `docs/SOCIO_DEPLOY_GUIDE.md`.

---

## 🟡 APIs importantes (no críticas pero mejoran mucho el producto)

### 4. Netlify — hosting frontend

**Para qué sirve:** sirve los archivos estáticos del frontend (HTML +
JS + CSS).

**Free tier:**
- 100 GB bandwidth/mes (≈ 100K page views)
- Builds ilimitados
- HTTPS automático
- Sin tarjeta

**Cuándo pagar:** probablemente nunca para el volumen previsto.

**Setup:** ya configurado.

---

### 5. Resend — envío de emails

**Para qué sirve:** mandar emails reales del flow "olvidé mi contraseña"
y futuros emails transaccionales (welcome, recibos Stripe, etc.).

**Estado actual:** sin esta API, el link de reset queda en los logs de
Railway. Funcional pero no usable para usuarios reales.

**Free tier:**
- 3.000 emails/mes
- 100 emails/día
- Sin tarjeta requerida
- Sandbox: solo manda a la cuenta dueña

**Cuándo pagar:** si superás 100 emails/día (≈ 100 users haciendo reset
en simultáneo, escenario raro). Plan **Pro USD 20/mes** = 50K emails.

**Setup paso a paso:**
1. Ir a https://resend.com → Sign up.
2. **API Keys → Create**:
   - Name: `re-expert-prod`
   - Permission: **Sending access**
   - Domain: All domains
3. Copiar key (`re_xxxxxxxx`).
4. Pegar en Railway → `RESEND_API_KEY=re_...`.
5. **(MVP simple)** Pegar también `RESEND_FROM=onboarding@resend.dev`.
6. **(Para usuarios reales)** Verificar un dominio propio:
   - Necesitás un dominio comprado (`tudominio.com`).
   - Resend → Domains → Add Domain → seguir DNS records (TXT + DKIM).
   - Después: `RESEND_FROM=RE Expert <hola@tudominio.com>`.

**Riesgo:** sandbox de Resend solo manda al email del owner. Para mandar
a cualquier usuario, hay que verificar dominio propio.

---

## 🟢 APIs opcionales (mejoras de calidad/visibilidad)

### 6. Gemini API — fallback gratis del chat

**Para qué sirve:** si Anthropic se queda sin saldo o tira 5xx, el chat
automáticamente usa Google Gemini 2.5 Flash.

**Free tier:**
- 15 requests/min
- 1.500.000 tokens/día
- Sin tarjeta requerida

**Cuándo pagar:** rara vez; el free tier alcanza para emergencias y
testing.

**Setup paso a paso:**
1. Ir a https://aistudio.google.com/apikey.
2. Login con cuenta Google.
3. **Crear clave de API** → seleccionar proyecto (crear nuevo
   "re-expert" recomendado).
4. Copiar key (`AIzaSy...`).
5. Pegar en Railway → `GEMINI_API_KEY=AIzaSy...`.
6. Setear `LLM_PROVIDER=auto` (ya está).

**Limitación:** Gemini no soporta multimodal idéntico a Anthropic, pero
para queries texto-only funciona.

---

### 7. Sentry — error tracking

**Para qué sirve:** captura excepciones del backend y errores JS del
frontend con stack trace, breadcrumbs y user context. Sin esto, los
bugs en prod son invisibles hasta que un user reporta.

**Free tier:**
- 5.000 errores/mes
- 1 user/team
- 30 días retención
- Sin tarjeta

**Cuándo pagar:** USD 26/mes (Developer) si excedés 5K errores o querés
más retención.

**Setup paso a paso:**
1. https://sentry.io → Sign up.
2. **Create Project → Python → FastAPI** → name: `re-expert-backend`.
3. Copiar DSN (`https://xxx@xxx.ingest.sentry.io/yyy`).
4. **Create otro Project → JavaScript → Browser** → `re-expert-frontend`.
5. Copiar DSN.
6. Pegar backend DSN en Railway → `SENTRY_DSN`.
7. Pegar frontend DSN en `frontend/config.js` línea de `SENTRY_DSN`.

---

### 8. Stripe — billing (Pro plan)

**Para qué sirve:** cobrar suscripciones USD 29/mes del plan Pro.

**Costo:**
- No tiene fee mensual fijo.
- Comisión por transacción: **2.9% + USD 0.30** por cobro exitoso.
- Ejemplo: 100 usuarios Pro × USD 29 = USD 2.900 ingresos brutos → USD 84 + USD 30 = **USD 114 fee Stripe** (4% del ingreso).

**Setup paso a paso (tu socio):**
1. https://dashboard.stripe.com → si está test mode, OK para arrancar.
2. **API Keys** → copiar `pk_test_...` y `sk_test_...`.
3. **Products → Add product** → `RE Expert Pro` USD 29/mes recurring → copiar Price ID.
4. **Developers → Webhooks → Add endpoint**:
   - URL: `https://re-expert-production.up.railway.app/api/stripe/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.*`, `invoice.paid`, `invoice.payment_failed`.
   - Copiar Signing secret (`whsec_xxx`).
5. Pegar en Railway:
   ```
   STRIPE_SECRET_KEY=sk_test_xxx
   STRIPE_WEBHOOK_SECRET=whsec_xxx
   STRIPE_PRICE_ID_PRO=price_xxx
   STRIPE_SUCCESS_URL=https://re-expert.netlify.app/success.html
   STRIPE_CANCEL_URL=https://re-expert.netlify.app/pricing.html
   ```

**Riesgo:** sin `STRIPE_WEBHOOK_SECRET` el endpoint rechaza con 503 en
prod (protección crítica para evitar que atacantes forjen pagos).

---

### 9. UptimeRobot — monitoring uptime

**Para qué sirve:** pinguear `/health` cada 5 min para detectar caídas
y notificarte por email. También evita cold starts en free tier.

**Free tier:** 50 monitores HTTP, intervalos 5 min, sin tarjeta.

**Costo:** USD 5-10/mes si querés intervalos de 1 min o monitoreo de SSL.

**Setup paso a paso:**
1. https://uptimerobot.com → Sign up free.
2. **+ Add New Monitor** → HTTPS.
3. URL: `https://re-expert-production.up.railway.app/health`
4. Interval: 5 minutes.
5. Alert: tu email.
6. Listo.

---

### 10. Google Maps API — rutas optimizadas SOL (v1.1)

**Para qué sirve:** el agente SOL puede armar rutas de visita a
inmuebles optimizando tiempo + distancia.

**Free tier:** USD 200/mes en créditos (cubre ~28K llamadas a
Directions API). Sin tarjeta NO se puede activar — requiere setup
de billing aunque no llegues al threshold.

**Costo:** USD 5-20/mes a uso medio.

**Setup:** ver `docs/SOL_INTEGRATIONS.md` cuando lo agregués (TODO).

---

### 11. Twilio WhatsApp — canal SOL via WhatsApp (v1.1)

**Para qué sirve:** SOL manda recordatorios y reportes al WhatsApp del usuario.

**Costo:**
- Sandbox dev: gratis (limitado a usuarios que opt-in).
- Production:
  - USD 1 por aprobación de cuenta (one-time).
  - USD 0.005-0.05 por mensaje según país.
  - WhatsApp también cobra: USD 0.01-0.10/conversación según categoría.

**Setup:** ver `docs/SOL_INTEGRATIONS.md` cuando lo agregués.

---

### 12. Telegram Bot — canal SOL via Telegram (v1.1)

**Para qué sirve:** idem WhatsApp pero por Telegram. **Gratis ilimitado.**

**Costo:** $0 siempre.

**Setup paso a paso:**
1. En Telegram: buscar **@BotFather** → `/newbot` → seguir prompts.
2. BotFather te da el token (`123456789:ABCDEF...`).
3. Pegar en Railway:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCDEF...
   TELEGRAM_BOT_USERNAME=re_expert_bot
   TELEGRAM_WEBHOOK_BASE_URL=https://re-expert-production.up.railway.app
   TELEGRAM_WEBHOOK_SECRET=<openssl rand -hex 32>
   ```
4. El bot queda esperando a que un usuario haga `/start <token>` desde
   la app.

---

## Proyección de costos por escenario

### Escenario A: MVP testing (0-20 usuarios, sin Pro)
| Servicio | Mes 0 | Mes 1 |
|----------|-------|-------|
| Anthropic | USD 10 | USD 15 |
| Railway | USD 5 | USD 5 |
| Supabase | USD 0 | USD 0 |
| Netlify | USD 0 | USD 0 |
| Resend | USD 0 | USD 0 |
| Sentry | USD 0 | USD 0 |
| **Total** | **USD 15** | **USD 20** |

### Escenario B: 100 usuarios activos (sin Pro paid)
| Servicio | Costo |
|----------|-------|
| Anthropic (con Fase 3 optimizaciones) | USD 80 |
| Railway | USD 5-10 |
| Supabase | USD 0 |
| Resend | USD 0 |
| Sentry | USD 0 |
| **Total** | **~USD 90/mes** |

### Escenario C: 100 usuarios + 20 Pro (USD 29/mes)
| Servicio | Costo |
|----------|-------|
| Anthropic | USD 100 (Pro usa más) |
| Railway | USD 10 |
| Supabase | USD 25 (cerca del límite free) |
| Resend | USD 20 (300+ emails/día) |
| Stripe (4% de USD 580 ingresos) | USD 23 |
| Sentry | USD 26 |
| **Total costos** | **~USD 204/mes** |
| **Ingresos Pro** | **USD 580/mes** |
| **Margen** | **USD 376/mes** |

---

## Orden recomendado de contratación

Cuando estés listo para pagar, en este orden:

1. **Anthropic** (USD 10 prueba) — sin esto el chat no anda.
2. **Resend** (gratis al principio) — para emails reales de reset.
3. **Sentry** (gratis) — para ver errores cuando los users empiecen a usar.
4. **UptimeRobot** (gratis) — opcional.
5. **Stripe** (sin fee mensual) — cuando tengas users dispuestos a pagar Pro.
6. **Gemini** (gratis) — opcional como red de seguridad.
7. **Telegram bot** (gratis) — si ves que SOL despierta interés.
8. **Twilio/Google Maps** — solo si los usuarios lo piden.

---

## Caja blindada — qué hacer si te quedás sin saldo

| Si se cae | El sistema |
|-----------|-----------|
| **Anthropic** sin créditos | Chat tira error "Sin créditos". Resto de la app sigue OK. Si `GEMINI_API_KEY` está seteado, salta a Gemini automático. |
| **Resend** sin saldo | Forgot password loggea el link al stdout en lugar de mandar email. Logs visibles en Railway. |
| **Sentry** lleno | Tracking se silencia, app sigue OK. |
| **Stripe** falla | Checkout devuelve error al usuario, account page sigue OK. |
| **Railway** caído | App entera offline. Crítico. |
| **Supabase** caído | App entera offline. Crítico. |
| **Netlify** caído | Frontend caído. Backend sigue por API directa, no usable. |
| **Telegram/WhatsApp/Maps** caídos | Solo SOL deja de mandar mensajes. Resto sigue. |

---

## Notas para el desarrollo

- **NO hardcodear ninguna key en código** ni en commits. Todas viajan
  via env vars en Railway/Netlify. El `.env.example` lista cada una con
  formato esperado.
- **Cada API se valida en startup:** si la var está vacía la feature
  queda disabled. Si está malformada (ej. URL inválida), el backend tira
  RuntimeError al iniciar.
- **Sin saldo no es bug** — la app discrimina entre "sin saldo" (error
  legítimo) y "bug" (excepción inesperada). Ver `services/anthropic_service.py`.
