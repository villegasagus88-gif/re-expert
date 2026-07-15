# Roadmap post-chat — qué falta y en qué orden

> El chat (`/api/chat` + KB en carpetas + multimodal) está completo y
> verificado en producción. Este doc cubre **todo lo demás** que falta
> para que las otras 7 secciones del sidebar y los flows accesorios
> queden 100% operativos.

**Última auditoría:** 2026-05-20.
**Branch base:** `merge/launch-mvp-into-main` (commit `0f3a52f`).

---

## Inventario actual por sección

| # | Sección sidebar | UI | Backend | Estado | Gap |
|---|-----------------|----|---------|--------|-----|
| 1 | 💬 Chat Experto | ✅ | ✅ | **COMPLETO** | — |
| 2 | 📐 Análisis de Planos | ✅ FileReader | ✅ multimodal | **COMPLETO (imgs)** | PDFs falta |
| 3 | 🧱 Cotización Materiales | ✅ cards+filtros | ✅ `/api/materials` (CSV) | **COMPLETO** | actualizar CSV mensual |
| 4 | 💵 Gestión de Pagos | ✅ CRUD | ✅ `/api/payments` | **COMPLETO** | — |
| 5 | 📊 Panel de Proyecto | ✅ dashboard | ✅ `/api/project` | **CASI completo** | flow de "crear proyecto inicial" |
| 6 | 📰 Noticias | ✅ 3 tabs | ✅ `/api/news` lee bucket | **HALF** | tabs "Destacadas" y "Opinión" siguen hardcoded; bucket vacío |
| 7 | ☀️ SOL Asistente | ✅ + Pro gate | ✅ agent + ingest + channels | **CASI completo** | Telegram bot wiring; emails opcional |
| 8 | 🎓 Academia | ✅ | ✅ implementado | **HECHO** | api/routes/academia.py + test_course_payments.py |

| Feature accesoria | Estado | Gap |
|-------------------|--------|-----|
| 🔐 Login / Register / Me / Refresh | **COMPLETO** | — |
| 🔑 Forgot / Reset password (con JWT bump) | **COMPLETO** código | falta `RESEND_API_KEY` en Railway |
| 🚀 Onboarding overlay | **COMPLETO** | — |
| 👤 Account page (perfil + plan + portal) | **COMPLETO** | — |
| 💳 Pricing + checkout | **COMPLETO** UI+API | faltan 4 env vars Stripe + webhook URL |
| 🌐 Landing pública (SEO) | **COMPLETO** | — |
| 📚 Knowledge Base | **COMPLETO** backend | falta UI admin (subir/borrar) — opcional |
| ⏱️ Rate limiting por plan | **COMPLETO** | — |

---

## Fase 1 — Wire-ups (1 día, sin código nuevo)

**Objetivo:** activar lo que ya está construido pegando env vars en Railway. Cada uno es independiente.

| # | Tarea | Tiempo | Quién | Bloquea |
|---|-------|--------|-------|---------|
| 1.1 | `RESEND_API_KEY` en Railway → emails de forgot-password reales | 5 min | Mati (ya tiene la key) | Onboarding de users nuevos |
| 1.2 | `RESEND_FROM` apuntar a `onboarding@resend.dev` mientras se verifica dominio custom | 1 min | Mati | Idem |
| 1.3 | `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `STRIPE_PRICE_ID_PRO` + `STRIPE_SUCCESS_URL` + `STRIPE_CANCEL_URL` en Railway | 15 min | Socio (cuenta Stripe) | Pricing/Upgrade a Pro |
| 1.4 | Webhook URL en Stripe Dashboard apuntando a `https://re-expert-production.up.railway.app/api/stripe/webhook` | 5 min | Socio | Stripe idempotency |
| 1.5 | `GEMINI_API_KEY` en Railway → fallback gratis si Anthropic sin saldo | 5 min | Mati | Resiliencia chat |
| 1.6 | `SENTRY_DSN` en Railway (browser + backend) → error tracking prod | 10 min | Socio o Mati | Visibilidad de errores |
| 1.7 | UptimeRobot pingueando `/health` cada 5 min → anti-sleep + monitoring básico | 5 min | Mati | UX (cold start) |
| 1.8 | Verificar dominio custom en Resend (DNS records) → mandar emails desde `hola@<dominio>` | 30 min + propagación DNS | Quien tenga dominio | Forgot password con FROM serio |

**Total fase 1:** ~1.5 horas reales + propagación DNS.
**Bloqueos:** principalmente acceso a dashboards de Stripe / Resend / Railway (vos y/o el socio).

---

## Fase 2 — Completar secciones half-baked (3-5 días)

**Objetivo:** que las 3 secciones que están al 70-90% queden al 100%.

### 2.A — Academia (1-2 días)

**Estado:** todo el contenido está hardcoded en `frontend/app.html` (cursos + rutas de aprendizaje). NO hay backend.

**Pasos:**

1. **Data source:** decidir entre:
   - **(A)** JSON estático en `knowledge/academia/cursos.json` + `rutas.json` (más simple, igual que materials.csv).
   - **(B)** Tabla `academia_courses` + `academia_paths` en Postgres (editable post-deploy).

   Recomendación: **A**. Es contenido curado low-churn (no se edita seguido), y mantiene el patrón de "knowledge as files". 30 min.

2. **Backend:** crear `backend/api/routes/academia.py` con dos endpoints:
   - `GET /api/academia/courses` → lista cursos con filtros (tab "Cursos").
   - `GET /api/academia/paths` → lista rutas de aprendizaje (tab "Rutas").

   Mismo patrón que `/api/materials`. 2-3 horas.

3. **Frontend:** reemplazar HTML hardcoded con `loadAcademia()` async + render desde data del backend. Tabs ya están construidos en la UI. 2-3 horas.

4. **Seeding:** mover los datos actuales del HTML a `cursos.json` para que el contenido se preserve. 1 hora.

**Total 2.A: 1 día.**

### 2.B — Noticias completar tabs "Destacadas" y "Opinión" (1 día)

**Estado:** la tab "Últimas" se nutre del bucket via `/api/news` ✅. Las tabs "Destacadas" y "Opinión" siguen con HTML estático.

**Pasos:**

1. Backend: extender `/api/news` con query param `?section=destacadas|ultimas|opinion`. El frontmatter de cada archivo `.md` en el bucket indica a qué tab pertenece.

2. Subir contenido curado al bucket `knowledge/noticias/`:
   - 5 noticias "Destacadas" (hero + cards): `2026-05-bcra-tasa.md`, etc.
   - 8-10 noticias "Últimas" (feed corto).
   - 3-4 "Opinión" con avatar + autor + role + quote.

3. Frontend: extender `loadNews()` para cargar las 3 tabs en paralelo y reemplazar el HTML estático.

**Total 2.B: 1 día (gran parte es curar contenido).**

### 2.C — Panel de Proyecto: flow inicial de "crear proyecto" (0.5 día)

**Estado:** `/api/project/dashboard` devuelve 404 hasta que el user crea un proyecto. Hoy no hay UI clara para crearlo (SOL lo hace via tools, pero un user que no es Pro no tiene acceso a SOL).

**Pasos:**

1. UI: form simple en `app.html` cuando la tab "Panel de Proyecto" detecta 404 → mostrar wizard: nombre, presupuesto base, fecha inicio, fecha entrega programada, meses totales.
2. Frontend: POST `/api/project` con los datos. Si no existe el endpoint, lo creamos.
3. Backend: revisar `routes/project.py`, agregar `POST /` si falta.

**Total 2.C: 4 horas.**

### 2.D — Planos: extraer texto de PDFs server-side (1 día, opcional)

**Estado:** hoy solo imágenes (PNG/JPG/GIF/WEBP). PDFs no se procesan.

**Pasos:**
1. Backend: agregar `services/pdf_extractor.py` usando `pypdf` (ya está en deps probablemente).
2. Frontend: cuando el user dropea un PDF, mandarlo a `/api/planos/extract` que devuelve texto + lista de páginas → ofrecer "Enviar texto a chat" o "Convertir páginas a imagen y enviar al chat".

**Total 2.D: 1 día.** Diferible a v1.1 — los planos reales suelen exportarse como imagen igual.

**Total Fase 2 sin Planos PDF: ~2.5 días.**

---

## Fase 3 — Optimización de costos Anthropic (1 día)

**Objetivo:** bajar 70-90% el costo por usuario antes de tener tráfico real.

| # | Optimización | Tiempo | Ahorro |
|---|--------------|--------|--------|
| 3.1 | **Prompt caching** de Anthropic (`cache_control: ephemeral` en system + KB) | 30 min | -70% en input tokens |
| 3.2 | **Modelo dual Haiku/Sonnet** — clasificador heurístico simple (keyword + longitud) | 1 hora | -50% en queries simples |
| 3.3 | **Resize de imágenes** en frontend antes de upload (cap 1568×1024) | 30 min | -50% en multimodal |
| 3.4 | **Cache de respuestas frecuentes** en DB con hash + TTL | 3-4 horas | -15-25% adicional |

**Total Fase 3:** ~1 día. Implementable ANTES de cualquier usuario real → ves el efecto en el primer dólar gastado.

---

## Fase 4 — Quality + Monitoring (2-3 días)

**Objetivo:** estar listo para escalar sin sorpresas.

| # | Tarea | Tiempo | Por qué |
|---|-------|--------|---------|
| 4.1 | Sentry wired (DSN en env vars) — ya está el SDK, falta DSN | 10 min | Visibilidad errores prod |
| 4.2 | Cleanup cron de `password_resets` expirados (en scheduler ya existente) | 30 min | Anti-bloat de DB |
| 4.3 | Mobile responsive QA + fixes (especialmente sidebar collapse + chat input en mobile) | 1 día | Mobile traffic = 60%+ |
| 4.4 | Tests E2E con Playwright (auth + chat + ingest + reset flow) | 1-2 días | Catch regressions pre-deploy |
| 4.5 | Documentar runbook de incidentes (chat caído / DB caída / Stripe webhook fallando) | 4 horas | Operación predecible |

**Total Fase 4:** ~3 días.

---

## Fase 5 — Growth features (post-MVP, v1.1+)

Ya hay base para todos, son features extra:

| Feature | Estimado | Estado base |
|---------|----------|-------------|
| **KB admin UI** (subir/borrar archivos desde la app) | 1 día | Backend completo, solo falta UI |
| **Telegram bot wiring** (canal de notificación SOL) | 1-2 días | Endpoints y models existen, falta env vars + webhook + flow de onboarding |
| **WhatsApp via Twilio** (idem) | 2-3 días | Idem Telegram, más complejo por costos Twilio |
| **Custom domain** (`re-expert.app` o `re-expert.com.ar`) | 1 hora + costo dominio | DNS docs ya escritos en `docs/DOMAIN.md` |
| **HSTS preload submit** una vez con dominio custom | 5 min | — |
| **Backup automático Supabase + plan de restore** | 0.5 día | Supabase auto-backup activo, falta documentar restore |
| **Onboarding más rico** (tour interactivo de cada sección post-signup) | 1-2 días | Overlay actual es básico |
| **Multilenguaje** (es-AR / es-MX / es-ES por región) | 3-5 días | Hoy hardcoded en es-AR |

---

## Camino crítico recomendado

### Semana 1 — terminar lo que está empezado

1. **Día 1:** Fase 1 wire-ups (env vars, dashboards) → emails reales + billing activo + monitoring básico.
2. **Día 2:** Fase 3 optimización costos (prompt caching + dual model + resize) — antes de tráfico.
3. **Día 3-4:** Academia (Fase 2.A) + Project initial flow (Fase 2.C).
4. **Día 5:** Noticias contenido + tabs completas (Fase 2.B).

### Semana 2 — calidad y validación

5. **Día 6-7:** Mobile responsive QA + fixes (Fase 4.3).
6. **Día 8:** Tests E2E mínimos (Fase 4.4 — auth + chat + ingest).
7. **Día 9:** Sentry + cleanup cron + runbook (Fase 4.1, 4.2, 4.5).
8. **Día 10:** Beta test con 3-5 usuarios reales → fix lo que surja.

### Post-launch (semana 3+)

9. Telegram bot.
10. KB admin UI.
11. Dominio custom + HSTS preload.

---

## Dependencias entre tareas

```
                 ┌─────────────────────┐
                 │   Fase 1 wire-ups   │
                 │  (env vars en RW)   │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │  Fase 2   │ │  Fase 3   │ │ Fase 4.1  │
       │ (UI gaps) │ │ (costos)  │ │  Sentry   │
       └─────┬─────┘ └───────────┘ └───────────┘
             │
             ▼
       ┌───────────┐
       │ Fase 4.3  │  Mobile QA en lo COMPLETADO
       │ (mobile)  │
       └─────┬─────┘
             │
             ▼
       ┌───────────┐
       │ Fase 4.4  │  E2E tests cubren features Fase 2
       │  (tests)  │
       └─────┬─────┘
             │
             ▼
       ┌───────────┐
       │ Beta users │  TODO arriba primero
       │   reales   │
       └─────┬─────┘
             │
             ▼
       ┌───────────┐
       │  Fase 5   │  Solo después de beta validado
       │ (growth)  │
       └───────────┘
```

---

## Métricas para evaluar progreso

Por cada fase, hay un check concreto:

- **Fase 1:** Login con un user nuevo recibe email real de "Bienvenido" (o reset funciona via mail). Stripe checkout completa exitoso.
- **Fase 2:** Las 8 secciones del sidebar tienen contenido dinámico (no hardcoded). `/api/project/dashboard` devuelve 200 sin pasos extra del user.
- **Fase 3:** Logging de `/api/usage` muestra costo promedio/query < 50% del baseline.
- **Fase 4:** 0 errores 5xx en Sentry durante 1 hora de uso normal. Tests E2E pasan en CI.
- **Fase 5:** SOL puede mandar un recordatorio por Telegram a tu celular real.

---

## Estimación total

| Fase | Tiempo | Costo $ |
|------|--------|---------|
| 1 — Wire-ups | 1.5 h | $0 (todo free tier) |
| 2 — Secciones | 2.5 días | $0 |
| 3 — Optimización | 1 día | $0 (ahorra después) |
| 4 — Quality | 3 días | $0 — Sentry free 10k tx/mes |
| **TOTAL al MVP completo** | **~7 días laborales** | **~$0** salvo Anthropic credits + dominio opcional |

---

## Notas

- **Knowledge base ya está completa** (240 archivos en `knowledge/`). NO tocamos esa estructura. El chat la usa via `services/context_router.py` y eso ya está optimizado.
- **El plan respeta el principio "el chat es el corazón"**: todas las otras secciones son features satélite que mejoran la UX pero el chat ya entrega valor solo.
- **Cada fase es independiente** — si vos avanzás con Fase 2 mientras el socio hace Fase 1, no se chocan.
