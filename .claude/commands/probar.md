---
description: Levanta el app en local (backend :8000 + frontend :8080), lo abre en el navegador y te da un checklist de qué probar en cada sección
---

Levantá RE Expert en local y dejá al usuario listo para **probar funcionalidades a mano**.
Argumento opcional: `$ARGUMENTS` = nombre de una sección para enfocarte solo en esa
(`chat`, `sol`, `planos`, `panel`/`pagos`, `billing`, `materiales`, `creditos`,
`deal`/`scanner`, `noticias`, `academia`, `workspaces`, `admin`). Vacío = checklist completo.

> Es el hermano de `/dev`: `/dev` solo levanta y verifica HTTP; `/probar` además
> abre la app, explica cómo entrar y te da el mapa de qué tocar.

## Contexto fijo
- **Backend**: FastAPI en `backend/`, uvicorn puerto **8000**. Python 3.14 global
  (`python` o `python3`, ambos resuelven). Necesita `backend/.env` (ya existe;
  NUNCA leer ni imprimir su contenido).
- **Frontend**: estático en `frontend/`, puerto **8080**. `config.js` autodetecta
  localhost y apunta a la API en `:8000`, así que login y app andan completos.
- **Login**: NO hay usuario demo/seed. Se entra por el modal de auth de `app.html`.

## Pasos

1. **Chequeo de puertos** (no duplicar procesos):
   - `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health` — si da 200, backend ya está arriba; no lo relances.
   - Ídem `http://localhost:8080/app.html`.

2. **Levantar lo que falte**:
   - Backend (si no responde): Bash en background (`run_in_background: true`):
     `cd backend && python -m uvicorn main:app --reload --port 8000`.
     Si falla por deps (`ModuleNotFoundError`): `cd backend && pip install -r requirements.txt -r requirements-dev.txt` y reintentá.
     Si no existe `backend/.env`: NO inventes valores — decile al usuario que lo cree desde `backend/.env.example` (mínimo `DATABASE_URL`, `JWT_SECRET`, y `ANTHROPIC_API_KEY`/`GEMINI_API_KEY` para el chat/SOL).
   - Frontend (si no responde): `preview_start` con nombre `"RE Expert - Chat Real Estate"` (config en `.claude/launch.json`). Si el preview falla, fallback Bash background: `cd frontend && python -m http.server 8080`.

3. **Verificar** (obligatorio antes de decir "listo"): mostrá los HTTP codes reales.
   - `curl -s http://localhost:8000/health` → 200 (reintentá hasta ~30s; uvicorn tarda unos segundos).
   - `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/app.html` → 200.

4. **Abrir la app**: navegá el preview a `http://localhost:8080/app.html` y sacá un
   `preview_screenshot` para confirmar que carga el modal de login. Reportá las URLs:
   - App: http://localhost:8080/app.html · Landing: http://localhost:8080/index.html · API docs: http://localhost:8000/docs

5. **Cómo entrar** (explicáselo al usuario, no lo hagas por él — el modal pide credenciales):
   - **Cuenta nueva**: en el modal, toggle *"Crear cuenta"* → nombre + email + password.
     En local (sin Mercado Pago configurado) el registro cae en **trial de 7 días con
     acceso completo, sin tarjeta**. Si aparece el overlay de onboarding, completalo.
   - **Cuenta existente**: modo *"Iniciar sesión"* (default) → email + password.
   - **Ser admin** (para probar KB admin / `/admin.html`): agregar tu email a
     `ADMIN_EMAILS` en el `.env` del backend y reiniciar uvicorn. Admin además saltea el paywall.

6. **Presentá el checklist** (el de abajo). Si `$ARGUMENTS` nombra una sección, mostrá
   solo esa y ofrecé el resto. Marcá siempre lo que **no** se puede probar sin key externa.

---

## ⚠️ Antes de tocar nada
El `backend/.env` apunta la `DATABASE_URL` a **Supabase de producción**. Todo lo que
registres/edites/borres probando **impacta la base real**. Para probar aislado hay que
apuntar `DATABASE_URL` a una DB de prueba (Supabase NO se toca desde el chat — regla del repo).

## Qué necesita cada cosa
- **Funciona 100% sin keys externas**: login/registro, Panel de obra + pagos, CRUD de
  planos + upload, Materiales (precios), catálogo de Créditos, Deal Scanner (motor
  `use_llm=false`), Workspaces/Memoria/Perfil + export, Contactos, ingesta, usage, landing.
- 🔴 **`ANTHROPIC_API_KEY` o `GEMINI_API_KEY`**: Chat, SOL, análisis de planos con IA,
  pronóstico de materiales, digest de noticias, deal analyze con IA, monitor de créditos.
- 🔴 **`TAVILY_API_KEY`**: web search del chat, noticias `/live`.
- 🔴 **`MP_ACCESS_TOKEN` + `MP_PLAN_ID`**: checkout/baja, cursos pagos, webhooks MP.
- 🔴 **`TELEGRAM_BOT_TOKEN` + `_USERNAME`** (+ `_WEBHOOK_SECRET` en prod): SOL/recordatorios por Telegram, pairing.
- 🔴 **Resend/email**: forgot/reset de password. **Supabase Storage**: KB admin persistente, noticias "Últimas".

---

## CHECKLIST (de lo más central a lo secundario)

### 0. Login / Cuenta — [Nuestro] · base de todo
- **Registro (trial)**: modal → "Crear cuenta". → 201, entra directo, `plan=trial` (7 días), acceso completo. ⚠️ escribe en prod.
- **Login**: modal default → email + password. → destapa la UI, carga workspaces/perfil/conversaciones.
- **Perfil / password**: `PUT /api/auth/me`. → persiste; cambiar password invalida tokens viejos.
- **Rate limits**: register 5/h, login 10/min → 429 al pasarse.

### 1. Chat Experto — [Agus] · núcleo del producto  🔴 LLM
- **Enviar + streaming**: vista Chat (default) → welcome-card o escribir. → respuesta SSE, conversación en Historial con título.
- **Tools**: pedir cálculo de rentabilidad / algo del KB / un documento exportable (PDF/Excel + link WhatsApp).
- **Adjuntar plano/imagen**: respuesta multimodal one-shot. · Web search → 🔴 Tavily.

### 2. SOL — Asistente — [Nuestro] · copiloto agente  🔴 LLM
- **Acción por lenguaje natural**: sidebar → "SOL" → "cargá un pago de X" o "Resumen ejecutivo". → dispara tools, responde SSE.
- **Confirmación de acciones**: pedir algo que muta datos. → **pide confirmación**; verificá que **sin confirmar NO escribe**, y que recién confirma en el turno siguiente.
- **Recordatorios / Exportar PDF-DOCX**: toolbar. · Telegram → 🔴 bot token.

### 3. Panel de Proyecto + Pagos — [Nuestro] · billing/obra  (sin key)
- **Panel + tabs**: sidebar → "Panel de Proyecto" → Resumen/Pagos/Costos/Cronograma. → indicadores EVM (CPI, SPI, EAC, desvío).
- **Registrar pago → recálculo**: tab Pagos → cargar pago. → "pagado" alimenta el costo real; Resumen recalcula. Verificá que solo ves pagos propios.
- **Hitos**: CRUD con estados/fechas → se refleja en Cronograma.

### 4. Billing / Suscripción — [Nuestro]
- **Estado**: `GET /api/billing/status` (fuera del gate). → plan, has_access, trial_ends_at.
- **Paywall**: con trial vencido, entrar a una feature → 403 estructurado + `upgrade_url=/pricing.html`.
- 🔴 **Checkout/baja MP**: `/pricing.html` → requiere `MP_ACCESS_TOKEN` + `MP_PLAN_ID`.

### 5. Análisis de Planos — [Compartido]
- **Crear proyecto + subir plano** (sin key): "+ Nuevo proyecto" → arrastrar PDF/PNG/JPG/WEBP (máx 8MB) → aparece en el visor.
- 🔴 **Clasificar / Analizar / Integral / Comparar** (LLM): summary, alertas con pins, checklist, diff de versiones.
- **Tareas / pins manuales / biblioteca / dashboard** (sin key): tabs Tareas e Historial.

### 6. Cotización de Materiales — [Compartido]
- **Precios actuales** (sin key): filtros + "Recargar precios". · 🔴 **Pronósticos IA**: "Análisis profundo".

### 7. Créditos (asesor hipotecario) — [Nuestro]  (catálogo sin key)
- **Analizar situación**: "Créditos" → completar "Tu situación" → "Analizar". → mejores opciones, ordenar, detalle en modal.
- 🔴 **Admin créditos**: `/admin-creditos.html` (admin + LLM).

### 8. Deal Room / Opportunity Scanner — [Compartido]
- **Nuevo análisis (motor, sin key)**: cargar oportunidad → analizar. → score, escenarios, riesgos, recomendación.
- **Deal Room**: la oportunidad queda listada; mover shortlist/descartada. · 🔴 **Analizar con IA / Extraer de URL**.

### 9. Noticias & Análisis — [Compartido]
- 🔴 **Feed en vivo** (Tavily) · **Destacadas/Opinión** (sin key) · 🔴 **Digest IA** al abrir una nota.

### 10. Academia / Cursos — [Compartido] (billing = Nuestro)
- **Catálogo + rutas + detalle** (sin key) · **Inscripción gratis** directa · 🔴 **Carrito + Pagar MP**.

### 11. Workspaces + Memoria + Perfil — [Nuestro]  (sin key salvo el chat)
- **Crear workspace + chat interno** · **Memoria del workspace** (upsert por key, se inyecta al prompt) · **Mi perfil global** (viaja a todos los chats) · **Exportar memoria** (PDF/CSV).

### 12. Cuenta / Pricing / Admin (fuera de app.html) — [Nuestro]
- **`/account.html`, `/pricing.html`** (requieren sesión) · 🔴 **`/admin.html`** KB admin (admin + Supabase Storage) · **`/admin-academia.html`**.

### 13. Secundarios
- **Contactos** (CRUD, sin key) · 🔴 **Canales/Telegram pairing** · **Recordatorios CRUD** · **Ingesta** `POST /api/data/ingest` · **Usage** (tokens + costo) · **Landing** `GET /api/public/landing` (sin login).

---

## Troubleshooting
- Puerto 8000/8080 ocupado por zombie: PowerShell `Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess` → `Stop-Process -Id <pid>`. En Windows, uvicorn `--reload` muestra varios PIDs escuchando el mismo socket (handles heredados): es normal, no los mates.
- Backend responde pero el chat/SOL falla: casi siempre falta `ANTHROPIC_API_KEY`/`GEMINI_API_KEY` en `.env`.
- NO corras migraciones alembic salvo pedido explícito (la DB es la de prod).
- Tests: por archivo, `python -m pytest tests/test_X.py --import-mode=importlib -q`.
