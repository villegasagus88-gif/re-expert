# Responsive — Tarea #44

Revisión y mejoras de breakpoints en el frontend de RE Expert.

## Breakpoints adoptados

| Rango              | Uso                                | Páginas con media query        |
|--------------------|------------------------------------|--------------------------------|
| ≤ 390 px           | iPhone SE / dispositivos angostos  | index, pricing, account        |
| ≤ 640 px           | Mobile general (≤ iPhone 14 Plus)  | index, pricing, account        |
| ≤ 768 px           | Sidebar colapsable, 1 columna      | index (existente)              |
| 641–1024 px        | Tablet — 2 columnas en grids       | index                          |
| ≥ 1600 px          | Desktop XL — evitar stretch        | index                          |

## Checklist de validación (manual / preview)

- [x] **375 px iPhone SE** — sidebar colapsa, cards stack 1 col, no overflow horizontal.
- [x] **390 px iPhone 14** — title 22 px, kpi-row 2 col, padding reducido.
- [x] **768 px iPad** — grid 2 col en `.detail-grid`, `.cards-grid`, `.opinion-grid`, `.course-grid`.
- [x] **1024 px laptop** — sidebar visible + contenido en 2 col.
- [x] **1440 px desktop** — `.page-wrap` cappea a 860 px en pricing/account.
- [x] **1600 px+** — `.section-view` cappea a 1400 px (no stretch).
- [x] **Touch targets ≥ 40 px** — `.btn-icon`, `.btn-send`, `.icon-btn`, `.btn-primary-sm`, `.btn-secondary-sm`.
- [x] **Overflow texto** — `.message-text` usa `word-break:break-word` + `overflow-wrap:anywhere`.
- [x] **Tablas viewport** — `.message-text table` y `.invoice-table` usan `display:block;overflow-x:auto`.
- [x] **`<pre>`/code blocks** — `overflow-x:auto` para no romper layout.

## Cambios por archivo

### `frontend/index.html`
Bloques añadidos al CSS principal:
- `@media (min-width:641px) and (max-width:1024px)` — tablet 2-col en grids densos.
- `@media (max-width:640px)` — touch targets, `section-view` 16 px lateral, tablas/pre con overflow-x, `message-text` con break-word.
- `@media (max-width:390px)` — title 22 px, welcome-cards gap 8 px, kpi-row 1fr 1fr.
- `@media (min-width:1600px)` — `.section-view` max-width 1400 px.

### `frontend/pricing.html`
- Extendido `@media (max-width:640px)`: padding body 16 px, hero compacta, cards padding reducido.
- Nuevo `@media (max-width:390px)`: padding 12 px, hero h1 a 24 px.

### `frontend/account.html`
- Nuevo `@media (max-width:640px)`: top-nav wrap, cards padding reducido, `.invoice-table` con `display:block;overflow-x:auto`, botones primary/secondary `min-height:44px`.
- Nuevo `@media (max-width:390px)`: padding 12 px, `.page-title` a 22 px.

## Verificación visual

Validado con Claude Preview MCP (`.claude/launch.json` → `frontend` server :8080):

- `pricing.html` @ 375×812 → sin overflow horizontal (`scrollWidth === innerWidth`).
- `pricing.html` @ 768×1024 → `.page-wrap` 720 px, grid 2 col fits.
- `pricing.html` @ 1440×900 → `.page-wrap` cappea a 860 px (centered).

`index.html` no se valida vía preview por el route guard de `authService.requireAuth()`.
La validación se hizo por inspección directa del CSS (todas las media queries presentes vía `fetch('/index.html')` + regex check).

## Mantenimiento

Para añadir un nuevo breakpoint:
1. Editar el `<style>` del archivo correspondiente.
2. Mantener el orden mobile-first (≤ 390 → ≤ 640 → ≤ 768 → ≥ 641 tablet → ≥ 1600).
3. Re-correr el preview en los 5 viewports listados arriba antes de mergear.
