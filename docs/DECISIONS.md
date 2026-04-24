# Decisiones técnicas (ADRs)

Registro breve de **por qué** se tomó cada decisión importante, con alternativas
descartadas. Formato: problema → decisión → razón → consecuencias.

---

## ADR-001: Supabase como BaaS (Auth + DB + Storage)

- **Problema:** necesitamos auth, DB y storage para MVP sin armar infra.
- **Decisión:** usar Supabase (Auth + Postgres + Storage).
- **Alternativas:** Auth0 + RDS + S3 (más caro y más setup), Firebase (no es SQL).
- **Consecuencias:**
  - ✅ Setup en un día, RLS gratis, precio $0 en tier free.
  - ⚠️ Quedamos atados a su API. Migrar a Postgres vanilla + Keycloak es posible pero costoso.

## ADR-002: FastAPI + SQLAlchemy async + Alembic

- **Problema:** lenguaje y framework para el backend.
- **Decisión:** Python 3.12 + FastAPI + SQLAlchemy 2.0 async + Alembic.
- **Alternativas:** Node/Express, Django (sync).
- **Razón:** SDK oficial de Anthropic en Python es el más maduro; async + SSE natural; typing fuerte con Pydantic.

## ADR-003: SSE en vez de WebSockets para streaming de respuestas

- **Decisión:** usar Server-Sent Events (`text/event-stream`) con `StreamingResponse`.
- **Razón:** flujo unidireccional (server→cliente), reconexión automática del navegador,
  pasa por proxies HTTP sin config especial. WebSockets serían overkill.
- **Consecuencia:** si en el futuro necesitamos bidireccional (p.ej. cancelar stream desde cliente),
  habrá que migrar a WebSockets o usar un endpoint paralelo de cancelación.

## ADR-004: Rate limiting en DB (sin Redis) para MVP

- **Problema:** limitar mensajes por usuario según plan.
- **Decisión:** query a tabla `messages` con ventanas rolling de 1h/24h.
- **Alternativa:** Redis con buckets fijos (más rápido, caché dedicada).
- **Razón:** evitar infra extra para MVP; la tabla ya existe y los índices alcanzan.
- **Cuándo migrar:** cuando veamos >1000 req/s o la query de rate limit supere los 50ms (medir).

## ADR-005: Pricing hardcodeado en código (no en DB)

- **Decisión:** tabla `PRICING` en `services/token_usage_service.py`.
- **Razón:** los precios de Anthropic cambian vía nuevas versiones del modelo, no como dato runtime.
  Un deploy para actualizar precios es aceptable.
- **Revisitar:** si introducimos planes con markups dinámicos o descuentos por volumen.

## ADR-006: Frontend estático en vanilla JS (sin framework)

- **Decisión:** HTML + vanilla JS para login/register/app.
- **Alternativa:** React/Vue/Svelte.
- **Razón:**
  - MVP: 3 pantallas, no justifica el overhead de un framework ni el pipeline de build.
  - Deploy como archivos estáticos en Netlify — zero config.
- **Cuándo migrar:** cuando tengamos >5 pantallas con estado compartido o componentes repetidos
  (probable después de tener 100+ usuarios).

## ADR-007: Access token en memoria, refresh delegado a Supabase SDK

- **Decisión:** JWT access en closure de `authService.js`, refresh token manejado por Supabase (localStorage).
- **Alternativa ideal:** refresh token en httpOnly cookie (inmune a XSS).
- **Razón pragmática:** el SDK de Supabase lee el refresh desde JS para renovar la sesión.
  Migrar a httpOnly exige proxyar login/refresh/logout por el backend.
- **Mitigación actual:** CSP estricta + no cargar scripts externos en páginas de auth.
- **Ver:** `TRADE_OFFS.md` § "Refresh token no es httpOnly".

## ADR-008: Conversation title auto-derivado del primer mensaje

- **Decisión:** al crear una conversación, derivar título del primer mensaje del usuario (truncado a ~60 chars).
- **Alternativa:** pedir a Claude que resuma los primeros 3 mensajes.
- **Razón:** gratis, instantáneo, suficientemente útil. El usuario puede renombrar después (pendiente UI).

## ADR-009: Context router por keywords (sin embeddings)

- **Decisión:** clasificar dominio de la pregunta por keywords hardcoded (costos, materiales, normativa, etc.)
  y seleccionar archivos .md del dominio.
- **Alternativa:** embeddings + vector search (pgvector / Supabase Vector).
- **Razón:** keywords alcanzan para ~6 dominios con vocabulario bien distinto; embeddings
  agregan latencia y costo sin ganancia clara en este tamaño de base.
- **Cuándo migrar:** cuando la base de knowledge supere los ~50 archivos o las preguntas sean
  muy abiertas y keywords empiecen a fallar.

## ADR-010: Docker + Railway en vez de serverless para el backend

- **Decisión:** contenedor Docker con uvicorn, deploy a Railway.
- **Alternativa:** Lambda / Cloud Run / Vercel Functions.
- **Razón:** SSE requiere conexiones largas; serverless típicamente tiene timeout de 30s o cobra por segundo.
  Railway nos deja conexiones de 60s sin sobresaltos y predicibilidad de costo.
