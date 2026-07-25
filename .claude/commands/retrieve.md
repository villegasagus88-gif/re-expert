---
description: Trae los cambios nuevos del repo (los de Agus y los nuestros), los integra sin romper nada y reporta qué cambió y cómo está prod
---

Poné el proyecto al día con GitHub y contame qué cambió. Argumento opcional:
`$ARGUMENTS` (`solo-ver` = reportar sin integrar nada; vacío = traer e integrar).

## Contexto fijo del proyecto
- Repo `origin` = `git@github.com:villegasagus88-gif/re-expert.git`. Producción es **`main`**.
- Dos devs: **nosotros** (Mati, commits como `MatiasParola`) y **Agustín**
  (`Agustin Villegas` / `villegasagus88-gif`). Agus pushea seguido y a cualquier hora.
- Branch de trabajo nuestra: la que esté activa (hoy `refactor/sol-hardening`).
- **Deploy automático desde `main`**: Railway (backend) y Netlify (frontend). No
  hay que publicar nada a mano.
- Dominios: nuestro = SOL, frontend, billing, auth, infra. De Agus = chat/Capa 2,
  retrieval, entregables, **voz**. Ver `CLAUDE.md`.

## Pasos

1. **Fetch y foto del estado** (siempre, aunque `$ARGUMENTS` sea `solo-ver`):
   - `git fetch --all --prune`
   - `git status --short` → **si hay cambios sin commitear, avisá y NO los pises**
     (puede ser trabajo esperando OK del usuario). Con working tree sucio, integrá
     solo si el merge/FF no toca esos archivos; si los toca, pará y preguntá.
   - `git rev-parse --short HEAD` y `git rev-parse --short origin/main` en
     comandos SEPARADOS (juntos con `tr` fallan si una ref no resuelve).

2. **¿Qué hay de nuevo?**
   - `git log HEAD..origin/main --date=format:"%m-%d %H:%M" --pretty=format:"%h | %ad | %an | %s"`
   - Si no hay nada: confirmalo mirando también el último commit de Agus en
     cualquier ref (`git log --all --author="Villegas\|villegasagus\|Agust" -1`)
     y las branches por delante de main:
     `for b in $(git branch -r | grep -v HEAD); do n=$(git rev-list --count origin/main..$b); [ "${n:-0}" -gt 0 ] && echo "$b: +$n"; done`
   - Si hay commits nuevos: `git diff --stat HEAD...origin/main` para ver el alcance.

3. **Integrar** (salvo `$ARGUMENTS` = `solo-ver`):
   - Intentá `git merge --ff-only origin/main`. Si el FF no aplica (divergimos
     porque tenemos commits locales), hacé `git merge origin/main` con mensaje
     descriptivo — **nunca rebase ni reset --hard**.
   - Actualizá también `main` local: `git branch -f main origin/main` (si no
     divergimos) para que futuros retrieves comparen bien.

4. **Verificar que lo nuevo integra sano** (obligatorio si entraron cambios):
   - Backend tocado → `cd backend && python -c "import main"` + las suites de lo
     que cambió (`python -m pytest tests/test_X.py --import-mode=importlib -q`;
     NUNCA la suite completa junta: colisiona por nombres de módulos).
   - Frontend tocado → chequeo de sintaxis de TODOS los bloques `<script>` inline
     de `app.html` (extraerlos sacando comentarios HTML y correr `node --check`),
     y llaves balanceadas en `app.css`.
   - Si algo falla, reportalo con el output real — no lo maquilles.

5. **Estado de producción**:
   - `curl -s https://re-expert-production.up.railway.app/health` → devuelve
     `{"status":"ok","commit":"<sha corto>"}`. **Comparalo con `origin/main`**:
     si coinciden, prod corre ese build.
   - Netlify: solo si entraron cambios de `frontend/`, verificá con cache-bust
     (`curl -s "https://re-expert.netlify.app/app.css?nc=$(date +%s)" | grep -c "<marcador del cambio>"`).
     El deploy tarda ~1 min; si todavía no está, decilo y ofrecé re-chequear.

## Cómo reportar (esto es lo que el usuario quiere leer)
- **Qué hizo Agus**, en castellano y por feature (no pegues el log crudo):
  qué agregó/arregló y en qué área. Si tocó algo de NUESTRO dominio
  (CSP, settings, auth, billing, infra), **revisalo con ojo crítico** y decí si
  está bien o si abre un riesgo.
- **Qué cambió de lo nuestro** si hubo pushes propios desde el último retrieve.
- **Veredicto de integración**: tests/sintaxis verdes o qué rompió.
- **Estado de prod**: qué commit corre Railway, si Netlify ya publicó el front.
- **Pendientes que siguen abiertos**: branches esperando review de Agus
  (`perf/prompt-cache-split-agus`), decisiones suyas (WhatsApp/Telegram, config
  en Railway) y lo que quedó en `docs/PARA_AGUS.md`.
- Si NO hubo nada nuevo, decilo directo y en una línea: "todo al día, local =
  origin/main = `<sha>`, sin actividad de Agus desde `<fecha>`".
