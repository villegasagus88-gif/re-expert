# Trade-offs y deuda técnica conocida

Cosas simplificadas para llegar al MVP. Cada ítem dice **qué está dejado a medias**,
**por qué es aceptable hoy**, y **cuándo / cómo migrar**.

---

## 1. Refresh token no es httpOnly

- **Hoy:** Supabase guarda el refresh token en `localStorage`. Vulnerable a XSS.
- **Aceptable porque:** sin scripts de terceros, con CSP estricta el vector de XSS es chico para MVP.
- **Migración:** proxyar `login`, `refresh`, `logout` por el backend y setear cookies `HttpOnly; Secure; SameSite=Lax`.
  El SDK de Supabase no lo hace out-of-the-box — hay que implementar manual.
- **Disparador:** primer usuario pago, auditoría de seguridad, o si vendemos a empresas.

## 2. Rate limiting con query a DB (no Redis)

- **Hoy:** cada request hace 2 queries (`COUNT` en 1h y 24h) sobre `messages`.
- **Aceptable porque:** índice en `(conversation_id, created_at)` y traffic bajo.
- **Migración:** Redis con buckets + `INCR`/`EXPIRE`.
- **Disparador:** latencia del check >50ms p95 o >500 req/s sostenido.

## 3. Context router por keywords

- **Hoy:** regex sobre `message.lower()` para clasificar en 6 dominios.
- **Aceptable porque:** knowledge base chica y vocabulario separado.
- **Migración:** embeddings (pgvector en Supabase) o un classifier chico de Claude Haiku.
- **Disparador:** >50 archivos .md, o feedback de que no encuentra el contexto relevante.

## 4. Pricing de Anthropic hardcodeado

- **Hoy:** diccionario `PRICING` en `services/token_usage_service.py`.
- **Aceptable porque:** los precios cambian poco y un deploy para actualizarlos está bien.
- **Riesgo:** si Anthropic cambia precios y no actualizamos, cobramos mal / medimos mal el costo.
- **Migración:** tabla `pricing(model, effective_from, input_per_mtok, output_per_mtok)` + admin UI.

## 5. Frontend sin framework ni build step

- **Hoy:** HTML + JS vanilla, 3 pantallas, deploy estático.
- **Aceptable porque:** simplicidad brutal, sin `node_modules`, deploy instantáneo.
- **Migración:** Next.js / Vite + React cuando tengamos >5 pantallas o estado compartido complejo.
- **Señales de alarma:** `index.html` ya tiene 155kb. Si crece a >500kb o duplicamos lógica
  entre páginas, migrar.

## 6. No hay tests de integración ni E2E

- **Hoy:** solo smoke tests (`pytest`) que verifican rutas registradas y cálculos puros.
- **Aceptable porque:** MVP con mocks costaría más de lo que aporta.
- **Migración:** Playwright para E2E del flujo login→chat→logout. Pytest con DB de testing
  (Supabase local) para integración del backend.
- **Disparador:** primer bug en producción que tests unitarios no hubieran detectado.

## 7. Manejo de errores del chat en frontend es básico

- **Hoy:** si el stream falla, se muestra mensaje genérico.
- **Pendiente:** detectar 429 y mostrar el `Retry-After` friendly; distinguir network error vs API error;
  permitir reintentar la última pregunta.

## 8. No hay endpoint para **listar / renombrar / borrar conversaciones**

- **Hoy:** el frontend puede mandar `conversation_id` pero no hay UI para gestionarlas.
- **Pendiente:** `GET /api/conversations`, `PATCH /api/conversations/{id}` (title), `DELETE /api/conversations/{id}`.

## 9. Soft delete no existe — todo es `ON DELETE CASCADE`

- **Hoy:** borrar una conversación elimina sus mensajes físicamente.
- **Alternativa:** columna `deleted_at` + filtros en queries.
- **Cuándo:** si un usuario pide recuperar una conversación borrada o si necesitamos auditoría.

## 10. Secrets rotation manual

- **Hoy:** si se filtra un secret, hay que rotarlo a mano en Supabase/Anthropic/Railway.
- **Mitigación:** `RUNBOOK.md` documenta el paso a paso.
- **Ideal a futuro:** Vault / AWS Secrets Manager con rotación automática.

## 11. No hay observabilidad real

- **Hoy:** logs de `logging` de Python en stdout, los ve Railway.
- **Pendiente:** Sentry para errores + Logtail/Datadog para logs estructurados + métricas (latencia, tasa de 429, costo por usuario).
- **Disparador:** primer usuario pago o equipo de >2 personas.

## 12. CORS permisivo en producción (pendiente ajustar)

- **Hoy:** `CORS_ORIGINS` default incluye `localhost`. En prod hay que setearlo al dominio final de Netlify.
- **Acción:** cuando se conecte Netlify, agregar el dominio a `CORS_ORIGINS` en Railway.

## 13. No hay billing / Stripe

- **Hoy:** `STRIPE_KEY` existe en settings pero no se usa. `plan` del usuario se setea a mano.
- **Pendiente (tarea grande):** integración Stripe Checkout + webhook `checkout.session.completed` → upgrade a `pro`.
