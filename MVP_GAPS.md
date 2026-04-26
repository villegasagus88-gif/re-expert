# RE Expert — Lo que falta para el MVP

> Estado al 26/04/2026.  
> Tests: 82/82 pasando. Bugs conocidos documentados por separado.

---

## Resumen ejecutivo

El backend está mayormente completo (auth, chat SSE, pagos, proyecto, materiales, SOL ingest, Stripe, knowledge base). El frontend tiene la estructura visual de todas las secciones. Los gaps principales son: dos secciones sin datos reales (Noticias y Academia), la feature de Planos sin implementar a fondo, un dato de contexto hardcodeado en SOL, un archivo HTML faltante, y la ausencia de un listener que refresque las vistas luego de un ingest de SOL.

---

## 1. Noticias — sección sin backend

**Estado:** El HTML y el render de cards existen en `index.html`, pero todo el contenido es estático hardcodeado. No hay API, no hay fuente de datos real.

**Lo que falta:**
- Decidir la fuente: scraping/RSS propio, API de noticias externa, o contenido curado manualmente en la knowledge base.
- Un endpoint `GET /api/noticias` (o similar) que devuelva los artículos.
- La función `loadNoticias()` en el frontend que haga fetch y reemplace el HTML estático.

**Scope mínimo para MVP:** si no hay fuente externa, alcanza con un JSON/JSONB en base de datos editable por admin + un endpoint read-only. La UI ya está construida.

---

## 2. Academia — sección sin backend

**Estado:** Mismo patrón que Noticias. Las tabs "Cursos" y "Rutas de aprendizaje" están hardcodeadas en el HTML. No hay fetch, no hay API.

**Lo que falta:**
- Un endpoint `GET /api/academia` (cursos + rutas de aprendizaje).
- La función `loadAcademia()` con fetch + render.
- Fuente de datos: puede ser JSONB en DB editable por admin, o archivos `.md` en Supabase Storage.

**Scope mínimo para MVP:** seeding manual de los datos estáticos actuales en la DB y un endpoint de lectura. La UI ya existe.

---

## 3. Planos — análisis sin contenido real

**Estado:** La sección tiene zona de drag-and-drop funcional. Al hacer "Analizar", envía al chat solo los **nombres** de los archivos (`file.name`), no el contenido. Claude recibe algo como: `"Analiza estos planos y estima materiales: planta_baja.pdf, corte_A.pdf"` — sin ver los archivos.

**Lo que falta:**
- Leer el contenido de los archivos con `FileReader` (imágenes → base64, PDFs → extracción de texto o base64).
- Enviar el contenido al chat como `image` o `document` blocks usando la API de mensajes de Anthropic (multimodal).
- Alternativa más simple para MVP: subir los archivos a Supabase Storage, obtener una URL firmada, y pasar la URL al prompt.

**Scope mínimo para MVP:** al menos extraer el contenido de imágenes (PNG/JPG) como base64 y pasarlo como bloque `image` al endpoint de chat. PDFs requieren más trabajo (pdf.js o extracción server-side).

---

## 4. SOL — contexto del proyecto hardcodeado

**Estado:** La constante `SOL_PROMPT` en `index.html` (línea 2448) incluye datos del proyecto completamente estáticos:

```
- Presupuesto base: $6.430.000
- Costo real: $4.250.000 (66% ejecutado)
- Avance de obra: 58% (vs 66% programado)
- Plazo: 14/18 meses
- Alertas: sobrecosto estructura +13.8%, retraso instalaciones 18 días
```

Estos valores no se actualizan aunque el usuario modifique su proyecto en la vista "Proyecto". La función `loadProyecto()` sí llama a `/api/project/dashboard`, pero ese resultado nunca se inyecta en `SOL_PROMPT`.

**Lo que falta:**
- Después de `loadProyecto()`, construir dinámicamente la sección "Datos actuales del proyecto" del `SOL_PROMPT` con los datos reales devueltos por la API.
- Si el proyecto no existe (404), dejar esa sección vacía o con un texto genérico.

**Scope:** 10–15 líneas de JavaScript. Alta prioridad porque sin esto SOL siempre trabaja con datos de ejemplo, no del usuario real.

---

## 5. SOL ingest — vistas no se refrescan tras cargar un dato

**Estado:** Cuando SOL persiste un dato en el backend (pago, hito, material, presupuesto), dispara `sol:data-ingested` en el frontend. **Nadie escucha ese evento.** El toast de confirmación se muestra, pero la vista de destino (Pagos, Proyecto, Materiales) sigue mostrando los datos anteriores hasta que el usuario navega a otra sección y vuelve.

**Lo que falta:**
- Un listener de `sol:data-ingested` que invalide el cache del state correspondiente según `detail.view`:
  - `pagos` → `pagosState.loaded = false` + `loadPagos(true)`
  - `materiales` → `materialesState.loaded = false` + `loadMateriales(true)`
  - `proyecto` → `proyectoState.loaded = false` + `loadProyecto(true)` (sólo si está en esa vista o al próximo acceso)

**Scope:** ~15 líneas. Sin esto el ciclo "cargué un dato → lo veo reflejado" no se cierra.

---

## 6. Forgot-password — página faltante

**Estado:** `authService.js` incluye `/forgot-password.html` en `PUBLIC_ROUTES` (línea 23), lo que indica que debe existir. La página **no existe** en el directorio `frontend/`.

**Lo que falta:**
- `frontend/forgot-password.html` con el formulario de recuperación de contraseña.
- El endpoint backend `POST /api/auth/forgot-password` (actualmente no existe en `auth.py`).
- El endpoint `POST /api/auth/reset-password` para aplicar la nueva contraseña con el token del mail.
- Integración con un servicio de envío de mail (puede ser Supabase Auth reset, SendGrid, o Resend).

**Scope:** es el flujo completo de recuperación de contraseña. Si Supabase Auth maneja esto nativamente, puede simplificarse mucho. Si no, requiere: tabla de tokens, lógica de expiración, y envío de mail.

---

## 7. Knowledge base — sin UI de administración

**Estado:** El backend tiene un API completo en `/api/knowledge/` (list, upload, download, delete, clear cache) que gestiona archivos en Supabase Storage. El frontend **no tiene ninguna pantalla** para acceder a estas funciones.

**Lo que falta:**
- Una vista o modal de administración para que el usuario (o un admin) pueda subir/eliminar archivos `.md`, `.pdf`, `.txt`, etc. que Claude usa como contexto en el chat.
- Puede ser tan simple como un panel en `account.html` o una nueva vista en el sidebar solo para admins.

**Scope:** si se restringe a admin (`user.role === 'admin'`), es un panel básico de file manager. Los endpoints ya existen.

---

## Tabla de prioridades

| # | Gap | Impacto UX | Scope estimado |
|---|-----|------------|----------------|
| 4 | SOL contexto hardcodeado | Alto — SOL trabaja con datos de ejemplo | Bajo (JS, ~15 líneas) |
| 5 | SOL ingest sin refresh de vistas | Alto — ciclo carga→ver roto | Bajo (JS, ~15 líneas) |
| 3 | Planos sin contenido real | Alto — feature principal no funciona | Medio (FileReader + multimodal) |
| 6 | Forgot-password faltante | Medio — flujo de auth incompleto | Medio–Alto (backend + frontend + mail) |
| 1 | Noticias sin backend | Medio — sección vacía en prod | Medio (endpoint + seeding) |
| 2 | Academia sin backend | Medio — sección vacía en prod | Medio (endpoint + seeding) |
| 7 | Knowledge base sin UI admin | Bajo para usuario final | Bajo–Medio (panel admin) |

---

## Lo que ya está completo

- Auth completo: register, login, refresh, `/api/auth/me`, update profile, onboarding.
- Chat SSE con historial de conversaciones, rate limiting por plan, logging de tokens.
- SOL: chat mode + ingest pipeline (`/api/data/ingest`) hacia Pagos, Hitos, Materiales, Presupuesto.
- Pagos: CRUD completo con summary y filtros.
- Proyecto: dashboard con indicadores (CPI, SPI, EAC), milestones CRUD.
- Materiales: listado con categorías y variación de precios.
- Stripe: checkout, portal de facturación, webhook de activación/cancelación.
- Billing: `GET /api/billing/status` con historial de facturas y estado de suscripción.
- Usage: `GET /api/usage` con consumo de tokens por ventana temporal.
- Knowledge base: backend completo con Supabase Storage.
- account.html: perfil, cambio de contraseña, billing portal, historial de facturas.
- 82 tests pasando.
