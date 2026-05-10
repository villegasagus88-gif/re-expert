# 04 — Impuestos

Tributos aplicables al desarrollo y a las operaciones inmobiliarias en AR.
Organizado por nivel de gobierno + capítulo aparte para estructuras fiscales.

## Subcarpetas
- `nacional/` — IVA, Ganancias, Bienes Personales, Monotributo, Cedular
- `provincial/` — IIBB, Sellos, Inmobiliario provincial (CABA, PBA y otras)
- `municipal/` — ABL/TSG, derechos de construcción, plusvalía
- `estructuras-fiscales/` — fideicomisos, SAS, condominio, leasing, comparativa

## Reglas de la carpeta
- **Toda alícuota tiene fecha** y `last_verified`.
- Separar por jurisdicción — no mezclar CABA con PBA en un mismo archivo.
- Citar AFIP, ARBA, AGIP, Rentas provincial respectiva, BORA.
- Cuando un esquema sea borderline (planificación fiscal agresiva), marcar `[CONSULTAR ASESOR]`.
- Mantener un comparativo de alícuotas vigente: `provincial/comparativo-alicuotas.md`.

## 🔴 Datos volátiles vs 🟢 estables

Aplican las reglas de `_meta/politica-datos.md`. Por carpeta:

**🔴 Volátil — el chat NO da el número, deriva a fuente:**
- Mínimos no imponibles, deducciones personales, escalas Ganancias.
- Categorías y topes de Monotributo (anuales).
- Retenciones y percepciones por RG (cambian con frecuencia).
- Valor de UVA / CER (diario).
- Régimen informativo y umbrales UIF (cambian).

**🟡 Semivolátil — guardar con `last_verified`:**
- Alícuotas centrales (IVA 21%, Ganancias sociedades 35%, IIBB construcción) → guardar con fecha y advertir si > 6 meses sin verificar.
- Mínimos exentos de Bienes Personales.
- Fechas de vencimiento generales.

**🟢 Estable — el chat responde directo:**
- Estructura del impuesto (qué grava, base imponible, sujeto pasivo).
- Funcionamiento del régimen (IVA débito/crédito, complejidades de fideicomisos, etc.).
- Diferencia entre vehículos (SAS vs fideicomiso vs condominio).
- Marco legal (Ley 23.349 IVA, Ley 20.628 Ganancias, Ley 23.966 Bs Personales, etc.).
- Lógica del Convenio Multilateral.

**Para datos del día → enviar a:** AFIP (afip.gob.ar), ARBA (arba.gov.ar), AGIP (agip.gob.ar), BORA, InfoLEG. Ver `_meta/fuentes-oficiales.md`.
