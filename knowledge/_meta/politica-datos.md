---
title: "Política de datos — volátiles vs estables"
topic: "meta"
subtopic: "politica"
jurisdiction: "N/A"
last_verified: "2026-05-10"
sources: []
keywords: [politica, datos, volatiles, estables, frescura, fuentes, actualizacion, criterio, vigencia]
audience: ["chat", "desarrollador", "estudiante"]
confidence: "alta"
priority: "obligatorio"
---

# Política de datos del KB — volátiles vs estables

> **Este archivo es lectura obligatoria del chat.** Define qué información se
> guarda en el KB con un valor concreto y qué información sólo se referencia
> con su fuente oficial para que el usuario consulte el dato del día.

## TL;DR
- **Estable** = se guarda con valor concreto + fuente. El chat lo da directo.
- **Volátil** = NO se guarda el número. El chat dice **dónde** buscarlo + cómo se calcula + cuándo se publica.
- **Semivolátil** = se guarda con `last_verified`; si pasaron > X días el chat lo da con disclaimer y link.
- Política activa: **antes errar por consultar la fuente que dar un número desactualizado.**

---

## 1. Taxonomía oficial

### 🔴 VOLÁTIL — el chat NUNCA da el número del KB
Se actualiza con frecuencia ≤ 1 mes y/o un valor desactualizado puede generar pérdida económica directa o decisión legal errónea.

| Tipo de dato | Frecuencia de cambio | Fuente oficial |
|---|---|---|
| Tipo de cambio (oficial / MEP / CCL / billete) | Diaria | BCRA + AMBITO/Rava |
| Precio de materiales en ARS | Mensual | Lista de proveedor mayorista al día |
| Jornales UOCRA y escalas salariales | Cada paritaria (~30–90 días) | UOCRA + MTEySS |
| Salario mínimo, vital y móvil (SMVM) | Decretos del PE | Ministerio de Trabajo |
| Tasa de política monetaria | Reuniones BCRA | BCRA Comunicaciones |
| Inflación mensual (IPC) | Mensual | INDEC (~día 12 mes siguiente) |
| ICC INDEC (índice costo construcción) | Mensual | INDEC |
| UVA (Unidad de Valor Adquisitivo) | Diaria | BCRA |
| CER | Diaria | BCRA |
| Alícuotas cambiantes (IIBB sub-rubros, retenciones) | Anual o por RG ad-hoc | AFIP / ARBA / AGIP |
| Mínimos no imponibles (Bs Personales, Ganancias, Monotributo) | Ley 27.617 + actualizaciones | AFIP |
| Valor m² por zona (precio listado / cierre) | Mensual | Reporte Inmobiliario / Colegio Escribanos |
| Cap rate / yield por barrio | Trimestral | Reportes de mercado |
| Comisiones bancarias y costos financieros | Comunicaciones BCRA | Cada banco |
| Stock de UFs en obra / pre-venta competencia | Mensual | Reporte Inmobiliario |
| Costo USD/m² por categoría | Mensual | CAC + cómputos vivos |
| Honorarios profesionales mínimos | Resoluciones de cada Consejo | CPAU / CPIC / SCA / colegios |

**Regla operativa para el chat:**
> Cuando la pregunta requiera un dato volátil:
> 1. NO inventes ni des de memoria.
> 2. Decí: *"Este dato cambia [periodicidad]. Te dejo dónde consultarlo al día y cómo se interpreta."*
> 3. Linkeá la fuente oficial (de `_meta/fuentes-oficiales.md`).
> 4. Si el usuario igual pide una estimación, dale un **rango histórico amplio** marcado como "estimación informativa, no operativa".

### 🟡 SEMIVOLÁTIL — se guarda con vigencia
Cambia cada 6–18 meses. Se guarda el último valor verificado **siempre con `last_verified`**.

| Tipo de dato | Frecuencia de cambio | Manejo |
|---|---|---|
| Alícuotas centrales (IVA 21%, Ganancias 35% sociedades) | Cada reforma tributaria | Guardar + nota "vigente desde DD-MM-YYYY" |
| Indicadores urbanísticos (FOT/FOS) por distrito | Cada modificación de código | Guardar; alertar si > 12 meses sin verificar |
| Régimen monotributo (categorías y topes) | Anual (julio típico) | Guardar año + advertir |
| Asignaciones, mínimos, deducciones | Anual | Guardar año fiscal |
| Honorarios mínimos profesionales | Anual o resolución ad-hoc | Guardar año |
| Tasas de Cap Rate de referencia AR | Trimestral | Guardar como rango + fecha |

**Regla:** si el chat detecta `last_verified` > 90 días en un dato semivolátil, lo entrega con disclaimer:
> *"Último verificado: [fecha]. Confirmá vigencia en [fuente]."*

### 🟢 ESTABLE — el chat lo da directo
Cambia con muy baja frecuencia (años) o no cambia. Información teórica, conceptual, normativa estructural.

- Definiciones del rubro (qué es FOT, fideicomiso, factibilidad).
- Artículos centrales del CCyCN (PH 2037–2072, fideicomiso 1666–1707).
- Estructura del proceso de desarrollo (8 fases, gates).
- Fórmulas financieras (TIR, VAN, payback).
- Marcos teóricos (triple impacto, Peiser/Hamilton, ULI).
- Estructura de un modelo de factibilidad.
- Tipologías de vehículos legales.
- Estructura del Código Urbanístico (no los indicadores numéricos por distrito).
- Procesos: cómo se inscribe una sociedad, cómo se registra un fideicomiso, cómo se escritura una UF.
- Riesgos y mitigadores genéricos.
- Marcos de impacto (B Corp, ODS, IRAM 11600).
- Glosario.

**Regla:** estos datos se mantienen en el KB sin disclaimer. Son la columna vertebral del chat.

---

## 2. Protocolo de respuesta del chat

Cuando llega una pregunta, el chat sigue este árbol:

```
1. ¿La pregunta involucra un número o dato puntual?
   ├─ NO → respuesta teórica/conceptual usando archivos ESTABLES del KB.
   └─ SÍ →
       2. ¿El dato es VOLÁTIL?
          ├─ SÍ →
          │   - NO dar número del KB.
          │   - Decir periodicidad + fuente oficial + cómo se interpreta.
          │   - Si el usuario insiste, dar rango histórico marcado como "informativo".
          │
          └─ NO (semivolátil o estable) →
              3. ¿Está en el KB con last_verified vigente (< 90 días para semivolátil)?
                 ├─ SÍ → respuesta directa con cita interna del archivo.
                 └─ NO →
                     - Decir el último valor verificado + fecha.
                     - Pedir confirmación al usuario o linkear fuente.
```

## 3. Frase de seguridad (al responder con dato volátil)

Plantilla recomendada:

> *"El [dato] varía [periodicidad]. Al [fecha de mi base], el rango histórico fue [X–Y], pero **no te lo doy como referencia operativa**. Para el valor del día consultá: [fuente oficial con link]. ¿Querés que te explique cómo se calcula o cómo impacta en tu proyecto?"*

## 4. Qué NO hace el chat nunca

- ❌ Dar tipo de cambio "actual" (cualquiera) sin link a BCRA.
- ❌ Dar precio en ARS de un material o jornal sin disclaimer + fecha.
- ❌ Dar alícuota tributaria sin verificar `last_verified`.
- ❌ Dar valor m² en USD de una zona como dato firme (siempre rango + "informativo").
- ❌ Confirmar normativa que no está citada en `02-normativa/` con número de ley.
- ❌ Dar asesoramiento legal o fiscal "operativo" — siempre derivar a profesional matriculado.
- ❌ Inventar fechas de vigencia. Si no las sabe, lo dice.

## 5. Qué SÍ hace el chat siempre

- ✅ Citar archivo del KB cuando usa un dato.
- ✅ Distinguir USD de ARS y aclarar tipo de USD (oficial/MEP/CCL/billete).
- ✅ Mencionar fecha de la base ("según `last_verified` 2026-MM-DD").
- ✅ Sugerir consulta profesional para decisiones legales/fiscales puntuales.
- ✅ Dar el **proceso** y el **criterio** aunque no pueda dar el número.
- ✅ Diferenciar dato vs opinión.

## 6. Información estable que el chat tiene SIEMPRE en memoria

Para evitar latencia y errores, esta es la información que ya está cargada
y el chat usa de manera prioritaria (sin recurrir a búsqueda externa):

| Tema | Archivo |
|---|---|
| Rol y ecuación del developer | `00-fundamentos/teoria-desarrollador.md` |
| Las 8 fases del ciclo de desarrollo | `00-fundamentos/ciclo-desarrollo-inmobiliario.md` |
| Checklist de DD por dimensión | `00-fundamentos/analisis-factibilidad.md` |
| Marco de triple impacto | `00-fundamentos/triple-impacto.md` |
| Glosario de 70+ términos | `_meta/glosario.md` |
| Catálogo de fuentes oficiales | `_meta/fuentes-oficiales.md` |
| Mapa keyword → archivo | `_meta/indice-rapido.md` |
| Reglas de respuesta | `_meta/instrucciones-chat.md` |
| Política de datos (este archivo) | `_meta/politica-datos.md` |
| Flujos por intención del usuario | `_meta/flows-por-intencion.md` |
| Anti-patterns del rubro (guardrails) | `_meta/anti-patterns.md` |
| Fórmulas financieras (TIR, VAN, sensibilidad) | `06-financiero/tir-van.md`, `06-financiero/sensibilidad.md`, `06-financiero/metricas-developer.md` |
| Estructura de costos y rubros de obra | `14-costos-presupuesto/estructura-costos.md` |
| Rendimientos de mano de obra por tarea | `05-construccion/rendimientos-mano-obra.md` |

Cuando se sumen archivos a las carpetas temáticas (Fase 2 en adelante),
todos los temas **estables** quedarán pre-cargados (normativa estructural,
estructuras fiscales, modalidades de contratación, indicadores teóricos,
marcos ESG).

## 7. Política de actualización

| Volatilidad | Cadencia de revisión |
|---|---|
| 🔴 Volátil | NO se guarda. Sólo se actualiza la fuente oficial cuando cambie. |
| 🟡 Semivolátil | Revisión trimestral del KB. Refresh manual de `last_verified`. |
| 🟢 Estable | Revisión semestral. Nuevas leyes / nuevos marcos. |

## 8. Excepciones (cuándo sí cargar un dato volátil)

Sólo se carga un dato volátil al KB si:
1. Es un **rango histórico** explícitamente marcado como tal (ej: "rango histórico 2018–2025 del Cap Rate CABA fue 4.5%–6.5%"), Y
2. Tiene `confidence: media` o `baja`, Y
3. La pregunta esperada es de tipo *educativa* (no operativa), Y
4. Se acompaña de "para valor del día consultar [fuente]".

Ejemplos válidos:
- "Históricamente el FX MEP osciló entre X y Y en el período Z" (educativo).
- "El IIBB construcción CABA estuvo en torno a X% en el último año" (verificar).

Ejemplos NO válidos:
- "Hoy el dólar está en $X" → NO.
- "El m² en Palermo es USD X" → NO (rango sí, valor puntual no).

---

**Ver también:**
- `./instrucciones-chat.md` — protocolo de respuesta detallado
- `./fuentes-oficiales.md` — catálogo para enviar al usuario
- `../README.md` — índice general del KB
