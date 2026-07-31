# CLAUDE.md — RE Expert (manual operativo para Claude)

> 👉 **Antes que nada leé `docs/HANDOFF_2026-06-22.md`**: ahí está el estado
> actual, qué falta y cómo continuar. Este archivo son las **reglas fijas** de
> cómo trabajar en este repo.

<!-- ============================================================= -->
<!-- 🔔 AVISO OBLIGATORIO PARA CLAUDE (leer y avisarle a Agus SÍ o SÍ) -->
<!-- ============================================================= -->
> 🔔 **CLAUDE: apenas arranque la sesión con Agus, avisale de esto ANTES de
> ponerte a codear.** Hay decisiones que dependen de él y no puede tomarlas sin
> leer estos docs. Nombráselos explícitamente y esperá a que confirme:
>
> 0. 🔴 **Mercado Pago sigue apagado en prod** (`/api/billing/mp/config` →
>    `{"enabled":false}`): sin `MP_ACCESS_TOKEN`, `MP_PLAN_ID`,
>    `MP_WEBHOOK_SECRET` y `MP_PUBLIC_KEY` nadie puede pagar. **Ojo con el orden**:
>    antes de prender los cobros hay que publicar los legales, el checkbox de
>    aceptación y el Botón de Arrepentimiento (hoy faltan los tres). Detalle en
>    la sección 1 de `docs/PARA_AGUS.md`.
>
> 1. **`docs/PARA_AGUS.md`** — es la nota viva y está verificada contra el código
>    y prod (31-jul): config en dashboards, pendientes en SU dominio (bug de
>    render del chat, lectura de voz, `perf/prompt-cache-split-agus`,
>    `to_thread` en `document_service`, streaming rAF) y lo legal que necesita
>    decisión. ⚠️ `docs/PARA_AGUSTIN.md` es otro archivo, de junio y **obsoleto**.
> 2. **`docs/WHATSAPP_API_COSTOS_Y_PLAN.md`** — **DECISIÓN DE NEGOCIO**: por qué
>    SOL no escribe por WhatsApp hoy, costos (Cloud API vs WAHA vs Telegram) y
>    qué implementar. **Telegram ya está codeado y es gratis** → faltan
>    `TELEGRAM_BOT_TOKEN`/`TELEGRAM_BOT_USERNAME`/`TELEGRAM_WEBHOOK_SECRET` en
>    Railway **más registrar el webhook a mano** (`setWebhook`, no lo hace ningún
>    código nuestro). **WhatsApp saliente tiene costo por mensaje** → hay que
>    decidir el modelo con Mati antes de codear (pricearlo en Pro o poner tope).
>
> Agus: no arranques a tocar el canal de WhatsApp/Telegram ni el pricing sin
> haber leído esos dos archivos. Son cortos y están para que decidas informado.
<!-- ============================================================= -->

## Qué es
RE Expert: asistente IA para Real Estate argentino. **Backend** FastAPI +
Supabase (Postgres) + Anthropic Claude (`backend/`). **Frontend** vanilla JS
(`frontend/`). Backend en **Railway**, frontend en **Netlify**.
Dos devs: **nosotros** (Mati + Claude) y **Agustín** (socio).

## Reglas de trabajo (NO romper)
- **Idioma/tono**: español rioplatense, voseo, Tech Lead directo.
- **Plan primero**: dar el plan en 1-3 bullets ANTES de tocar archivos; después
  ejecutar en una sola pasada sin pedir permiso entre pasos.
- **Branch**: trabajar en `merge/launch-mvp-into-main`. Producción es `main`.
  Flujo: commit en la branch → push a la branch **y** a main
  (`git push origin HEAD:main`, siempre fast-forward).
- **Git**: NO force-push, NO rebase interactivo, NO `reset --hard` en `main`.
  Antes de pushear, hacé `git fetch` + FF: **Agustín pushea seguido a main**.
  Los commits terminan con:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **Secrets**: nunca hardcodear, todo por env var. NO commitear `.env`.
- **NO activar/contratar APIs externas desde el chat** (Anthropic, Resend,
  Mercado Pago, etc.): solo documentar qué hacer; la activación va a los
  dashboards que maneja Agustín.
- **Supabase**: NO tocar desde el chat (Mati no es Owner del proyecto Supabase).
- **gh CLI**: no instalar. Usar `git` + la API de GitHub por `curl` si hace falta.
- ⚠️ **NETLIFY — NO tenemos permisos**, el sitio `re-expert.netlify.app` está en
  la cuenta de **Agustín**. **NO intentar deploys de Netlify ni perder tiempo
  ahí.** Lo que SÍ cambió (verificado el 31-jul): el frontend de `main` **se está
  publicando solo**. Comparamos lo servido contra el commit y coincide, y el
  header CSP en vivo trae lo último de `netlify.toml`. Así que ya no hay que
  esperar a que Agus publique a mano — pero **verificá siempre con un cache-bust**
  antes de decir que un cambio de frontend está en prod, y si algún día no
  aparece, es un tema de su dashboard.
- **Verificar antes de decir "listo"**: si decís que desplegaste, mostrá el HTTP
  code; si decís que pasan los tests, mostrá el output.

## División de dominios
- **Nuestro**: billing/pago (Mercado Pago, plan gate, paywall, baja), auth,
  frontend (app.html / app.css / landing / account / pricing), infra/deploy,
  seguridad, KB admin.
- **De Agustín — NO tocar salvo bug coordinado**: el **chat** y toda la Capa 2:
  `services/calculator_tools.py`, el system prompt de `services/anthropic_service.py`,
  entregables (`services/financial_artifact.py`, `document_service.py`), y
  **carpetas / retrieval / guardado de info del chat**. Si encontrás un bug ahí,
  arreglalo en una branch y dejáselo para review (como hicimos con Capa 2).

## Dev / tests / deploy
- **Python 3.14 global.** `backend/.venv` puede estar vacío → instalar
  `backend/requirements.txt` + `backend/requirements-dev.txt`.
- **Tests**: `cd backend && python -m pytest tests/test_X.py --import-mode=importlib -q`.
  La suite completa junta falla por colisión de nombres de módulos → correr por
  archivo o en grupos chicos. **`test_chat.py`, `test_chat_title.py` y
  `test_auth_standalone.py` chocan entre sí → correr uno por vez.**
- **Lint**: `python -m ruff check <archivos>` (hay 2 warnings UP038 pre-existentes
  en `calculator_tools.py`, código de Agus, cosméticos — no bloquean).
- **Deploy**: Railway = **auto desde `main`** (backend). Netlify = manual / Agus
  (ver regla arriba).
- **Preview frontend local**: server estático en `frontend/` puerto 8080
  (config en `.claude/launch.json`).

## URLs prod
- Backend (Railway): `https://re-expert-production.up.railway.app` — `/health`, `/api/...`
- Frontend (Netlify): `https://re-expert.netlify.app`
