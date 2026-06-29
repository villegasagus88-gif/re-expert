# Nota para Agus (y su Claude) — 2026-06-29

Mati + Claude. Resumen de lo que tocamos y lo que necesitamos de tu lado.
Todo esto ya está en `main` y **el backend ya está deployado en Railway**.

---

## 1) ⚠️ Publicar Netlify (lo único que falta y depende de vos)

El frontend nuevo (`frontend/app.html` + `frontend/app.css`) está en `main` pero
**no lo vemos en prod hasta que publiques Netlify** (no tenemos permisos en tu
cuenta; los pushes a `main` salen "Skipped"). Cuando hagas el Netlify Drop quedan
visibles dos cosas:

- **Reskin C1-v2**: tema naranja teja (`#BE5103`), chat con burbujas + skyline de
  edificios, botón "Nueva conversación" plano y banner de trial en naranja.
- **Dropdown multi-proyecto** en el Panel (ver punto 2).

El **backend ya soporta todo** — solo falta tu publish del front.

---

## 2) Multi-proyecto en el Panel (tu dominio — te lo dejamos andando)

Mati pidió poder tener **varios proyectos** y elegir cuál analizar desde un
desplegable en el Panel. Lo hicimos **backward-compatible**: si un usuario tiene
1 solo proyecto, **todo funciona exactamente igual que antes**.

**Qué cambió:**

- `models/project.py`: `Project.user_id` ya **no es `unique`** (N proyectos por
  usuario).
- `models/payment.py`: nuevo `Payment.project_id` (FK a `projects`, **nullable**)
  → costos/CPI separados por proyecto.
- **Migración `0021_multiproject_panel.py`** — saca el unique, agrega
  `payments.project_id` + FK + índice, y hace **backfill** de los pagos
  existentes al proyecto del usuario. **Ya corrió en la Supabase de prod** (deploy
  de Railway OK, `GET /api/project` responde, `/health` 200).
- `api/routes/project.py`:
  - Nuevo `GET /api/project` → **lista** de proyectos del usuario.
  - `GET /api/project/dashboard`, `PUT /api/project`, milestones → aceptan
    `?project_id=` opcional (con **validación de ownership**: siempre se filtra por
    `user_id`, no hay IDOR).
  - Sin `project_id` → cae al **primer proyecto** del usuario (compat).
  - Sacamos el `409` de "ya tenés un proyecto" (ahora se permiten varios).
- `api/routes/payments.py`: `GET /api/payments?project_id=` filtra por proyecto;
  el alta de pago se asigna al proyecto activo (id ajeno/inexistente → `None`).
- `frontend/app.html`: `state.activeProject` + `<select id="projSelect">` en el
  header del Panel; los loaders (`loadProyecto`, `loadPagos`, `savePayment`) usan
  el `project_id` activo. **No tocamos** el sistema de carpetas/workspaces.

**Verificación:** import OK (103 rutas), ruff limpio, **suite de tests sin fallas
nuevas**, frontend sin errores de JS, y una **review de seguridad dedicada
confirmó que no hay fugas cross-user (IDOR)**.

---

## 3) Observación de cálculo (tu dominio — decisión tuya, NO lo tocamos)

En `_build_dashboard` (`api/routes/project.py`, lógica EVM), hay un **edge case
pre-existente** (no lo introdujo el multi-proyecto): si un proyecto tiene **solo
pagos en estado `pendiente`** (ninguno `pagado`), `tiene_pagos` da `True` y el
AC se calcula como `pagado = 0`. Eso fuerza `AC=0` y deja **CPI/EAC en `None`**
en vez de caer al `costo_real` cargado a mano.

No es bug de seguridad ni rompe nada crítico, pero quizás quieras que en ese caso
(solo pendientes) el AC caiga al `costo_real` manual. **Te lo dejamos a vos** por
ser cálculo del Panel.

---

## 4) Los 3 tests que fallan (ver `NOTA_AGUS_TESTS_2026-06-28.md`)

Siguen las **mismas 3** fallas pre-existentes, todas de tu dominio / infra (NO
las causó nada nuestro):

- `test_context_router::test_classify_query_typical` (×2) — clasificación de query.
- `test_https::test_http_request_is_redirected_to_https` — redirect HTTPS.

Detalle en la nota del 28. El resto de la suite pasa (≈300 tests verdes).

---

**TL;DR:** publicá Netlify para ver el reskin + el dropdown. El backend
multi-proyecto ya está vivo en prod y verificado. Las observaciones de cálculo y
los 3 tests son tu dominio, sin urgencia.
