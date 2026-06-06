# Revisión de la Capa 2 (tools financieras/impositivas) — para Agustín

> De: Mati (+ Claude) · Fecha: 2026-06-06
> Contexto: tras mergear tu trabajo a `main` (commits `1fc5e46`..`c1d9155`, 13
> commits del 03 al 05/06), hicimos una revisión del código nuevo. Buenas
> noticias primero, después 2 bugs para que les pegues una mirada.

---

## TL;DR

- **Tu Capa 2 convive bien con el modelo pago-only** que metimos del otro lado:
  73 tests verdes en conjunto, el gate de acceso no te rompe nada, y las 8 tools
  están bien registradas (schema ↔ impl ↔ dispatcher matchean 1:1).
- **La matemática del grueso está bien** (VAN/TIR/payback, IVA, sellos, tasación,
  valor residual, break-even — verificados contra valores conocidos).
- **2 bugs P1 a corregir** (los 2 están en prod ahora): uno de cálculo en el
  flujo de fondos, y una contradicción entre el system prompt y la tool de
  transferencia.

---

## 🔴 Bug 1 — `flujo_fondos_desarrollo` descarta costo de obra en silencio

**Archivo:** `backend/services/calculator_tools.py` → helper `_spread()` usado por
`_tool_flujo_fondos_desarrollo`.

**Qué pasa:** cuando la obra (o los gastos) se reparten en períodos que caen
fuera del array (`obra_inicio + obra_duracion - 1 > último_periodo`), la porción
que no entra **se descarta sin avisar** en `notas`.

**Reproducción:**
```python
from services.calculator_tools import _tool_flujo_fondos_desarrollo as f
r = f(periodos=3, costo_obra_total=900, obra_inicio=2, ingresos_total=2000)
# total_egresos = 600.0   ← deberían ser 900 (se perdieron 300 de obra)
# resultado_neto = 1400.0 ← debería ser 1100
# notas: no menciona que se perdió obra
```
Se dispara con inputs razonables (con `obra_inicio>=2` y el `obra_duracion` por
defecto = nº de períodos, parte de la obra cae fuera).

**Impacto (P1):** subvalúa egresos → **infla margen / TIR / resultado**. En una
tool de inversión, dar un proyecto como más rentable de lo que es es el error más
peligroso que puede tener.

**Fix sugerido:** en `_spread`, clampear el remanente que no entra al último
período disponible (o reasignarlo al período de entrega). Como mínimo, si se
recorta, agregarlo a `notas` para que el modelo lo aclare. Idealmente: validar
`obra_inicio + obra_duracion - 1 <= periodos` y avisar si no.

---

## 🔴 Bug 2 — El prompt de Transferencia contradice a la tool

**Archivos:** `backend/services/anthropic_service.py:298-300` y `:311-313`
(system prompt) vs `_tool_calcular_impuesto_transferencia` en `calculator_tools.py`.

**Qué pasa:** el system prompt instruye al modelo:
> *"desde 2018 → Ganancias cedular 15% sobre la ganancia"* … *"desde 2018 →
> cedular 15% y pedí el costo de adquisición"*

Pero la **tool** (que ya tiene el marco actualizado) devuelve, para persona
física no habitualista en venta 2026+:
```
impuesto = 0.0 · cedular_situacion = "exento_2026" · EXENTO (Ley 27.802)
```

**Impacto (P1):** el modelo, guiado por el prompt, puede decirle al usuario que
**paga 15% de cedular** cuando la tool calcula **$0**. Info fiscal incorrecta de
cara al usuario, en prod.

**Fix sugerido:** la **tool tiene el marco correcto (2026)** — hay que actualizar
la sección del prompt (líneas 298-300 y la regla 3 en 311-313) para que coincida:
no habitualista → $0 / exento (Ley 27.802); dejar el 15% solo como referencia
histórica o para el caso habitualista. Alinearlo con la regla dura que ya tenés
bien en las líneas 92-97.

---

## 🟡 Menores (no bloquean)

- `calculator_tools.py`: 2 warnings de `ruff` UP038 (`isinstance(x, (A, B))` →
  `isinstance(x, A | B)`). Cosmético. `ruff check --fix --unsafe-fixes` los arregla.
- `calcular_sellos`: si pasás un `tramos` con `alicuota_pct` faltante, tira
  `TypeError` (el dispatcher lo captura y devuelve error limpio, así que no rompe
  el chat) — convendría validar el tramo y devolver `{"error", "ok": False}`.

---

## ✅ Lo que está bien (para que no quede solo lo malo)

- Registro/wiring de las 8 tools: impecable. `run_calculator_tool` captura toda
  excepción → ninguna tool puede romper el stream del chat.
- VAN/TIR (bisección con guarda de cambio de signo)/payback: exactos.
- `factibilidad_rapida`: break-even, sensibilidad por eficiencia y precio,
  ROI/markup con guarda de división por cero — todo correcto.
- IVA (extraer/agregar), sellos (base = máx(precio, valuación), tramos, reparto,
  exención por tope), tasación por comparables (mediana + dispersión + guard de
  plausibilidad), valor residual: verificados.
- Tus 282 líneas de tests nuevos pasan.

Cualquier duda sobre los 2 bugs, hablamos. Si querés, los fixeamos nosotros y te
los dejamos en una branch para que los revises antes de prod — avisá.
