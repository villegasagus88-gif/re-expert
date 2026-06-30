# Nota para Agus — morados viejos en tu dominio (2026-06-30)

Mati + Claude. Rediseñamos el **login y todas las páginas de auth** al naranja de
marca (#BE5103, light + dark) y de paso barrimos el `app.html` con un QA visual
multi-agente. Arreglamos todos los morados (#6366f1 / #818cf8 / #a855f7) que eran
de **nuestro dominio** (spinner de carga, link "↑ Pro", iconos de onboarding,
icono del modal upgrade, alertas de auth).

Quedan morados viejos **en tu dominio** (carpetas/workspaces y documentos
exportados) — no los tocamos para no pisarte. Cuando puedas, conviene pasarlos a
naranja para consistencia de marca. Todos son cambios **solo de color** (front,
sin tocar lógica):

## 1) Color por defecto de carpetas/workspaces (`app.html`)
El default de un workspace sin color es **#6366f1** (morado). Aparece al crear/
editar carpetas y en los dots del sidebar.
- `app.html:887` swatch "active" por defecto `data-color="#6366f1"` → `#BE5103`
- `app.html:880` `#wsNameDot` `background:#6366f1` → `#BE5103`
- `app.html:1141` `_editingColor: '#6366f1'` → `'#BE5103'`
- Fallbacks `w.color || '#6366f1'` en `app.html:1316, 1337, 1433, 1484, 1586, 1595, 1616` → `'#BE5103'` (idealmente una const `WS_DEFAULT_COLOR='#BE5103'`)
- `app.html:891` swatch alternativo `#a855f7` (morado) — si querés cero morado en la paleta, cambialo por un tono fuera del violeta (ej. `#d97706` ámbar o `#8f3d02` teja oscuro). Es una opción de color de carpeta, decisión tuya.

## 2) Branding de documentos exportados (`app.html`)
El reporte/PDF que se genera sale con encabezado y gráfico en morado:
- `app.html:2599` gradiente SVG de la curva-S del reporte (`#pvg`, `stop-color #6366f1` ×2) → `#BE5103`
- `app.html:2758` encabezado del documento exportado: `.hd` `border-bottom:2px solid #6366f1` y `.hd .logo color:#6366f1` → `#BE5103`

## 3) Opcional — colores semánticos de categoría (`app.css`)
Estos NO son morado de marca sino color-coding de categorías; los dejamos. Si
querés cero morado en toda la UI, son candidatos (verificá que no colisionen con
otras categorías):
- `app.css:568` `.chip-opinion` (categoría "opinión")
- `app.css:711` `.course-icon.design` (categoría "design" en Academia)
- `app.css:1142` `.news-cat-badge.proyectos` (categoría "proyectos" en Noticias)

---

**TL;DR:** el auth ya está 100% en naranja (light+dark). Estos morados restantes
son de carpetas y documentos exportados (tu dominio) — cambios solo de color
cuando quieras. Nada urgente ni bloqueante.
