---
description: Levanta el proyecto en local (backend :8000 + frontend :8080) y verifica que ambos respondan
---

Levantá el entorno de desarrollo local de RE Expert. Argumento opcional: `$ARGUMENTS`
(`back` = solo backend, `front` = solo frontend, vacío = ambos).

## Contexto fijo del proyecto
- **Backend**: FastAPI en `backend/`, corre con uvicorn en el puerto **8000**.
  Python 3.14 **global** (el venv `backend/.venv` puede estar vacío — no usarlo).
  Necesita `backend/.env` (ya existe en esta máquina; NUNCA leer ni imprimir su contenido).
- **Frontend**: estático en `frontend/`, puerto **8080**. `config.js` ya apunta
  localhost:8080 → API `http://localhost:8000`, así que con ambos arriba el
  login y la app funcionan completos contra el backend local.

## Pasos

1. **Chequeo de puertos** (no duplicar procesos):
   - `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health` — si da 200, el backend ya está arriba; no lo relances.
   - Ídem `http://localhost:8080/` para el frontend.

2. **Backend** (salvo `$ARGUMENTS` = `front`):
   - Lanzalo con el Bash tool en background (`run_in_background: true`):
     `cd backend && python -m uvicorn main:app --reload --port 8000`
   - Si falla por dependencias (`ModuleNotFoundError`): `cd backend && pip install -r requirements.txt -r requirements-dev.txt` y reintentá.
   - Si falla porque no existe `backend/.env`: NO inventes valores — decile al usuario que lo cree desde `backend/.env.example` y qué variables mínimas necesita (DATABASE_URL, JWT_SECRET, ANTHROPIC_API_KEY).

3. **Frontend** (salvo `$ARGUMENTS` = `back`):
   - Usá `preview_start` con el nombre `"RE Expert - Chat Real Estate"` (config en `.claude/launch.json`).
   - Si el preview falla o se cae (pasa seguido en esta máquina), fallback con Bash en background: `cd frontend && python -m http.server 8080`.

4. **Verificación** (obligatoria antes de decir "listo"):
   - Backend: `curl -s http://localhost:8000/health` → esperar `200`. Si tarda, reintentá hasta ~30s (uvicorn + imports tardan unos segundos).
   - Frontend: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/app.html` → `200`.
   - Reportá al usuario las URLs con los HTTP codes reales:
     - App: http://localhost:8080/app.html (login local contra el backend :8000)
     - Landing: http://localhost:8080/index.html
     - API docs: http://localhost:8000/docs

5. **Troubleshooting conocido**:
   - Puerto 8000/8080 ocupado por un proceso zombie: en PowerShell `Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess` y `Stop-Process -Id <pid>`; en Git Bash `netstat -ano | grep :8000`.
   - El backend local usa la MISMA DB que producción (Supabase) vía `.env` — avisale al usuario que los datos que cree localmente son reales. No corras migraciones alembic salvo pedido explícito.
   - Los tests NO se corren con la suite completa: por archivo con `python -m pytest tests/test_X.py --import-mode=importlib -q`.
