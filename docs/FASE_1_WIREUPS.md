# Fase 1 — Configuración del backend (sin APIs externas)

> Lo que se puede configurar **antes** de contratar APIs externas. Todo
> esto se puede hacer ya y queda listo para que cuando las APIs se
> contraten (ver `docs/APIS_EXTERNAS_Y_COSTOS.md`), se activen con
> pegar la env var.

**Estado del backend:** ✅ Funcional en producción.
**Objetivo de esta fase:** dejar tuneada la operación del backend para
que escale bien y sea fácil de mantener antes de sumar usuarios.

---

## Subfases

### 1.1 — Health checks y observabilidad mínima (sin APIs)

**Estado actual:**
- `/health` devuelve 200 con `{"status":"ok","version":"0.1.0"}`. ✅
- Logs de Railway tienen toda la actividad (SQL queries, requests, errores).

**Qué falta:**
- [ ] Endpoint `/health/db` que también valide conexión DB (no solo proceso vivo).
- [ ] Endpoint `/health/ready` para readiness probe (separado de liveness).
- [ ] Logging estructurado JSON en prod (hoy texto humano legible).
- [ ] Métricas internas (cantidad de chats, tokens consumidos, errores)
      expuestos en `/metrics` para futuro Prometheus/Grafana.

**Tiempo:** 2-3 horas.

### 1.2 — Performance: timeouts y connection pooling

**Estado actual:**
- DB pool: configurado en `models/base.py` con `pool_pre_ping=True` y
  `statement_cache_size=0` (necesario por pgbouncer transaction mode).
- HTTP body limit: 10 MB en `_BodySizeLimitMiddleware`.
- Stream chat timeout: 180s (`STREAM_TIMEOUT_SECONDS`).
- Request body sin Content-Length: rechaza 411.

**Qué falta:**
- [ ] Configurar `pool_size` y `max_overflow` explícitos (hoy defaults).
- [ ] Timeout global de request HTTP (hoy infinito en uvicorn).
- [ ] Rate limiting global por IP (slowapi ya está, falta tunear plafones).
- [ ] Idle connection cleanup automático.

**Tiempo:** 2-3 horas.

### 1.3 — Hardening de seguridad ya implementado (validación)

**Estado actual:**
- ✅ HTTPS redirect en prod (exempt `/health` para Railway healthcheck)
- ✅ HSTS header
- ✅ CORS env-aware (no wildcard en prod)
- ✅ Body size limit 10MB
- ✅ Magic-bytes validation en attachments multimodal
- ✅ Stripe webhook signature obligatoria en prod (503 si falta)
- ✅ JWT con `tv` claim → invalidación post-reset
- ✅ Password reset tokens hashed en DB (SHA-256)
- ✅ Rate limiting per-user + per-IP
- ✅ Aislamiento de datos por user_id en todas las queries

**Qué falta validar:**
- [ ] Penetration test básico (OWASP top 10).
- [ ] Headers Cache-Control en respuestas autenticadas (evitar cache
      de respuestas sensibles en CDNs intermedios).
- [ ] Política de SameSite cookies si en algún momento usamos cookies
      en vez de localStorage.

**Tiempo:** 1 día (audit + fixes).

### 1.4 — Optimización de costos sin API key

**Estado actual:**
- Context router activo (selecciona KB relevante por keywords).
- Rate limit por plan (free vs pro).
- Token usage logging en DB.

**Qué se puede mejorar sin tocar API:**
- [ ] **Prompt caching** de Anthropic (requiere modificar cómo se manda
      el system_prompt + KB al provider — el cliente Python ya soporta).
      Requiere créditos Anthropic activos para testear, pero el código
      se puede preparar sin créditos.
- [ ] **Selector Haiku/Sonnet** por tipo de query (heurística de
      keywords/longitud) — todo lógica local.
- [ ] **Resize de imágenes** en frontend antes de upload (canvas API).
      0 dependencias externas.
- [ ] **Cache de respuestas frecuentes** en tabla `response_cache` con
      hash + TTL. Requiere migration nueva (0016).

**Tiempo:** 1 día.
**Ahorro:** -70% a -85% en costo Anthropic cuando se activen.

### 1.5 — Schema cleanup y prep para growth

**Estado actual:**
- 15 migrations linear hasta `0015_token_version`.
- Tablas: profiles, conversations, messages, materials, milestones,
  budgets, projects, payments, contacts, reminders, user_channels,
  token_usage, stripe_events, password_resets.

**Qué falta:**
- [ ] Cleanup job en scheduler: borrar `password_resets.expires_at < now()`
      cada día.
- [ ] Cleanup job: borrar `stripe_events` viejos (>30d).
- [ ] Index review: revisar que las queries más calientes tengan índices.
- [ ] Foreign keys: validar `ON DELETE CASCADE` en todas las relaciones
      user_id (hoy ya está, pero confirmar).

**Tiempo:** 4-6 horas.

### 1.6 — Documentación operacional

**Estado actual:**
- `docs/DEPLOY_RAILWAY.md` ✅
- `docs/SOCIO_DEPLOY_GUIDE.md` ✅
- `docs/RUNBOOK.md` ✅
- `docs/ROADMAP_POST_CHAT.md` ✅
- `docs/APIS_EXTERNAS_Y_COSTOS.md` ✅

**Qué falta:**
- [ ] `docs/RUNBOOK_INCIDENTS.md` — qué hacer si:
  - Backend caído (Railway down)
  - DB caída (Supabase down)
  - Chat respondiendo lento (>30s)
  - JWT_SECRET filtrado (rotar + logout global)
  - User reporta data leak (audit log)
- [ ] `docs/MIGRATIONS_PLAYBOOK.md` — cómo agregar/revertir migrations
      sin romper prod.
- [ ] `docs/ONCALL.md` — quién recibe alertas, escalation path.

**Tiempo:** 4-6 horas.

---

## Orden recomendado

Las 6 subfases son **independientes** entre sí. Sugiero este orden:

1. **1.3 Validar hardening** (1 día) — confirmar que lo que ya está,
   está bien.
2. **1.1 Health checks** (2-3h) — base para monitoring.
3. **1.5 Schema cleanup** (4-6h) — cleanup jobs en el scheduler.
4. **1.2 Performance** (2-3h) — tuning de pools y timeouts.
5. **1.4 Prep de optimizaciones Anthropic** (1d) — código listo para
   activar cuando haya saldo.
6. **1.6 Docs operacionales** (4-6h) — última prioridad, se hace
   mejor con incidentes reales en mano.

**Total Fase 1:** ~4 días laborales.

---

## Después de Fase 1

→ **Fase 2** (Roadmap): completar secciones half-baked (Academia,
   Noticias tabs, Project initial flow).

→ Cuando estés listo para activar APIs externas, ver
   `docs/APIS_EXTERNAS_Y_COSTOS.md` para costos + paso a paso.
