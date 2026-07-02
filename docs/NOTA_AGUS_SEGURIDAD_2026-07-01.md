# 🔴 Nota de seguridad para Agus — 2026-07-01

Hicimos una auditoría de seguridad completa (multi-agente, con verificación
adversarial de cada hallazgo). Parcheamos en código todo lo que era nuestro +
los dos SSRF de tu dominio. **Hay UNA acción crítica que solo podés hacer vos
(rotar credenciales) — es urgente.**

---

## 🔴 CRÍTICO — Rotar credenciales YA (solo Agus, es Owner de Supabase)

**La contraseña de la DB de producción estuvo hardcodeada** en `scripts/apply_pr_migration.py`
y `scripts/fix_payments_schema.py`, que están **commiteados en git / GitHub**
(commits `0f09485`, `15e0103`). Cualquiera con acceso al repo pudo/puede
conectarse directo a la DB por el pooler y leer/escribir TODO (profiles, pagos,
conversaciones, PII), **salteándose la app y toda la autorización**.

Ya limpiamos los scripts (ahora leen `DATABASE_URL` de env) y sumamos un test
que detecta connection-strings para que no vuelva a pasar. **PERO limpiar el
código NO borra el secreto del historial de git** → la credencial debe
considerarse comprometida.

**Acción tuya (dashboards, no se hace desde el chat):**
1. **Rotar la password de la DB** en Supabase (Database Settings → Reset password) y actualizar `DATABASE_URL` en **Railway** + tu `.env` local.
2. Por precaución (conviven en el mismo `.env`): rotar también **JWT_SECRET** (invalida todas las sesiones — aceptable), **SUPABASE_SERVICE_ROLE_KEY** y regenerar la **ANTHROPIC_API_KEY**.
3. Revisar en los logs de Supabase si hubo conexiones no reconocidas mientras estuvo expuesto.
4. (Opcional, coordinado) Purgar el secreto del historial con `git filter-repo`/BFG — requiere force-push, que por regla del repo lo hacés vos coordinando. Con rotar alcanza para cerrar el riesgo real.

---

## ✅ Ya parcheado por nosotros (en este commit)

- **[nuestro] Secreto en scripts** → leen `DATABASE_URL` de env. + test de higiene ahora detecta connection-strings de Postgres/Supabase (regex nueva).
- **[tu dominio, lo tocamos por seguridad] SSRF en `/api/news/digest`** (`services/news_live.py::_fetch_article_text`) y **`/api/opportunities/extract`** (`services/opportunity_scanner.py::_fetch_url`): un usuario autenticado podía hacer que el backend le pegara a IPs internas / metadata de la nube. Creamos un guard compartido **`core/safe_fetch.py`** (valida esquema http/https, resuelve el host y bloquea IPs privadas/loopback/link-local/reservadas/CGNAT v4+v6, y **revalida cada redirect**) y cableamos ambos fetchers a `safe_get`. Comportamiento para URLs públicas legítimas: sin cambios. Revisalo cuando puedas (es tu dominio) — lo dejamos andando + con tests.
- **[nuestro] XSS almacenado latente**: `esc()` (frontend) no escapaba comillas → vía cache del digest se podía inyectar un handler en atributo. Ahora `esc()` escapa `"` y `'`.
- **[nuestro] Info-disclosure menor**: `/health/storage` devolvía `str(e)` al cliente → ahora loguea server-side y responde genérico.
- **[nuestro] Robustez pagos**: `create_payment` con `project_id` ajeno/inexistente ahora devuelve 404 en vez de crear un pago huérfano.

## 🟢 Baja prioridad / higiene (no bloquean, para tener en cuenta)

- **`.env` bajo OneDrive**: el repo está en `C:\Users\...\OneDrive\...`, así que los secretos de prod del `.env` local se sincronizan a la nube de Microsoft. Recomendación: excluir la carpeta del proyecto de la sync de OneDrive, o usar credenciales de staging en el `.env` local.
- **Academia `record_interest`**: `course_id`/`course_title` no se validan contra el catálogo (data-hygiene de las métricas de demanda; sin XSS ni abuso — el panel ya escapa y hay límites de longitud). Opcional validar contra `cursos.json`.

## Verificado
Auditoría confirmó además que está BIEN: JWT HS256 con algoritmo explícito (sin alg=none) + token_version, webhook MP con firma HMAC fail-closed en prod, CORS sin wildcard, SQL 100% parametrizado (ORM), output del chat por DOMPurify, ownership por `user_id` consistente en todas las rutas de objeto (sin IDOR). Suite de seguridad verde + ruff limpio.
