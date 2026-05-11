---
title: "Tributos municipales para real estate AR"
topic: "impuestos"
subtopic: "municipal-overview"
jurisdiction: "Municipal"
last_verified: "2026-05-11"
sources:
  - "Códigos Fiscales municipales (CABA, La Plata, Pilar, Tigre, Vicente López, San Isidro, Córdoba Capital, Rosario, Mendoza Capital)"
  - "Ordenanzas tarifarias anuales"
keywords: [municipal, abl, tsg, derechos construccion, tasa habilitacion, plusvalia, contribucion mejoras, derechos publicidad]
audience: ["desarrollador", "contador", "abogado", "chat"]
confidence: "alta"
---

# 04/municipal — Tributos municipales

## TL;DR
- Cada municipio tiene su propio régimen. CABA es comuna autónoma con AGIP.
- Cuatro grandes familias: (a) **ABL/TSG** sobre el inmueble; (b) **derechos de construcción** al permiso/visado; (c) **tasas de habilitación e inspección** al uso comercial; (d) **contribuciones por mejoras / plusvalía** vinculadas al hecho urbanístico.
- Pesan típicamente 1-3% del costo total del proyecto, pero pueden saltar mucho en municipios con plusvalía urbana muy activa.
- 🔴 Las alícuotas y montos cambian anualmente (ordenanza tarifaria). El chat NO da el número del día — deriva al sitio del municipio.

## Archivos del módulo

| Archivo | Contenido |
|---|---|
| `abl-tsg.md` | ABL CABA, TSG en PBA, equivalentes en interior |
| `derechos-construccion.md` | Derecho a la delineación, construcción, demolición |
| `tasas-municipales.md` | Habilitación, inspección comercial, ocupación vía pública, publicidad |
| `contribuciones-y-plusvalia.md` | Contribución por mejoras + captación de plusvalía urbanística |

## Lógica para el chat (routing)

| Pregunta del usuario | Archivo |
|---|---|
| "¿Cuánto se paga de ABL?" | `abl-tsg.md` |
| "¿Qué se paga al pedir el permiso de obra?" | `derechos-construccion.md` |
| "¿Cómo habilito un local comercial?" | `tasas-municipales.md` |
| "¿Qué es la plusvalía urbanística?" | `contribuciones-y-plusvalia.md` |
| "¿Cuánto cuesta poner cartel en obra?" | `tasas-municipales.md` |

## 🔴 Volátil vs 🟢 estable

**🔴 Volátil — derivar a fuente:**
- Alícuotas y valores fiscales actuales (ordenanza tarifaria anual de cada jurisdicción).
- Topes de exención (jubilados, vivienda única).
- Montos en ARS de cualquier tributo.

**🟢 Estable — respuesta directa:**
- Estructura tributaria municipal.
- Quién es contribuyente.
- Hecho imponible.
- Plazos típicos de un trámite.
- Cómo se calcula la base.

## Ver también
- `../provincial/` (impuesto inmobiliario provincial, sellos)
- `../nacional/` (IVA, Ganancias, Bs Personales)
- `../estructuras-fiscales/comparativa-vehiculos.md`
