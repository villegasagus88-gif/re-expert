---
title: "Inflación en Argentina y su impacto en real estate"
topic: "macro"
subtopic: "inflacion"
jurisdiction: "Argentina"
last_verified: "2026-05-10"
sources:
  - "INDEC — IPC, ICC"
  - "Cámara Argentina de la Construcción — CAC"
  - "BCRA — informes monetarios"
keywords: [inflacion, IPC, CAC, ICC, indices, indexacion, peso, USD, redeterminacion]
audience: ["developer", "financiero", "analista"]
confidence: "alta"
---

# Inflación en Argentina

## TL;DR
- Argentina convive con inflación elevada y volátil → **toda decisión inmobiliaria se desdolariza** o se indexa.
- Índices clave: **IPC** (general), **ICC** (construcción), **CAC** (Cámara Construcción), **UVA** (CER + spread), **CVS** (salarios).
- Real estate: precios de venta dolarizados, costos parcialmente en pesos → exposición compleja.
- Indexación de cuotas, redeterminación de obra y cobertura de costos son las herramientas principales.

---

## 1. Marco general

### 1.1 Niveles típicos
- 🔴 Volátil — depende del momento. Argentina tuvo períodos de inflación 25-200%+ anual en distintas etapas.
- Verificar IPC vigente en INDEC al momento de la respuesta.

### 1.2 Composición
- Inflación de bienes vs servicios.
- Inflación core vs estacional.
- Inflación de transables vs no transables.
- Mayor en algunos rubros (alimentos, salud, educación) que en otros.

### 1.3 Causas estructurales (síntesis)
- Déficit fiscal monetizado.
- Expectativas inflacionarias autovalidatorias.
- Brecha cambiaria.
- Indexación generalizada (salarios, contratos, alquileres).
- Pérdida de credibilidad institucional.

---

## 2. Índices principales

### 2.1 IPC (INDEC)
- Índice de Precios al Consumidor.
- Inflación general urbana.
- Base nacional + GBA + 5 regiones.
- Publicación mensual (en el día 12-14 del mes siguiente).

### 2.2 ICC (INDEC)
- Índice del Costo de la Construcción.
- Componentes: materiales, mano de obra, gastos generales.
- Específico al sector.

### 2.3 CAC (Cámara Argentina de la Construcción)
- Índice privado, similar al ICC pero con metodología propia.
- Más usado en contratos de construcción privada.

### 2.4 CER y UVA
- **CER** (Coeficiente de Estabilización de Referencia): ajusta por IPC.
- **UVA** (Unidad de Valor Adquisitivo): valor en pesos ajustado por CER.
- Usado en créditos hipotecarios indexados.

### 2.5 CVS (Coeficiente de Variación Salarial)
- Salarios formales registrados.
- Importante para indexar costos de mano de obra.

### 2.6 IPIM (precios mayoristas)
- Mayoristas internos.
- Útil para anticipar precios al consumidor.

### 2.7 RIPTE (remuneración imponible)
- Promedio de salarios sujetos a aportes.

---

## 3. Tipo de cambio y brecha

### 3.1 Tipos de cambio coexistentes
- **Oficial (mayorista, BCRA)**.
- **Minorista** (con impuesto PAIS y percepciones).
- **MEP** (mercado electrónico de pagos): bolsas de USD vía bonos.
- **CCL** (contado con liqui): bonos en NY.
- **Blue / informal**.
- **CCL / MEP - 30%, 50%**, etc.: variantes intervenidas.

### 3.2 Brecha
- Diferencia % entre tipos.
- Refleja desconfianza.
- Distorsiona decisiones (qué USD usar para evaluar).

### 3.3 Aplicación a RE
- Precio de venta: usualmente USD MEP o CCL.
- Costos de obra en pesos: convertir con qué tipo de cambio.
- Margen real depende del tipo de cambio aplicado.

---

## 4. Indexación en RE

### 4.1 Alquileres
- Ley 27.551 (modificada) + DNU 70/2023.
- Marco actual: libertad de pacto + frecuencia de actualización (típicamente 3-6 meses).
- Indices habituales: ICL (Índice de Contratos de Locación), IPC, USD.

### 4.2 Boletos de preventa
- Cuotas en pesos ajustables por CAC, IPC, USD.
- Topes y suelos negociables.

### 4.3 Contratos de obra
- Redeterminación polinómica (CAC + ICC + USD).
- Frecuencia: mensual / trimestral.

### 4.4 Servicios profesionales
- Honorarios pesificados con cláusula de actualización trimestral.

---

## 5. Impacto en el cashflow

### 5.1 Asimetría temporal
- Ingresos por preventa: mes 1 a mes 24.
- Costos de obra: mes 1 a mes 30.
- Si los ingresos están indexados a un índice y los costos a otro distinto: asimetría que erosiona márgenes.

### 5.2 Mismatch de moneda
- Costos en pesos, ingresos en pesos pero "marcados" a USD: si el USD sube y los pesos no se ajustan rápido, se compromete el margen.

### 5.3 Cobertura
- Comprar materiales por adelantado (clavar precios).
- Indexar al CAC los contratos.
- Crédito en USD si los ingresos están en USD.

---

## 6. Análisis en moneda dura

### 6.1 Trabajar en USD
- Convertir todo al tipo de cambio del momento.
- Comparar con precios de mercado dolarizados.

### 6.2 Riesgo
- Si la brecha cambiaria se mueve, los flujos en USD cambian sin que cambien los flujos en pesos.

### 6.3 Mejor práctica
- Modelo dual currency: ARS para costos locales, USD para ingresos, conversión visible.
- Sensibilizar el resultado al tipo de cambio.

---

## 7. Inflación en USD

### 7.1 Concepto
- Aún cuando se mide en USD, los precios cambian.
- Costo de obra en USD ha tenido variaciones del +30% al -20% en distintos años.

### 7.2 Drivers
- Brecha cambiaria.
- Costos en pesos que no se trasladan al USD.
- Incentivos / desincentivos del momento (ej. decretos PAIS).

### 7.3 Implicancia
- Un proyecto evaluado a USD/m² actual puede perder margen si el costo USD/m² sube.
- Sensibilizar también la inflación en USD del costo.

---

## 8. Estrategias macro para developers

### 8.1 Activos como cobertura
- Real estate como reserva de valor en contextos de alta inflación.
- Demanda de USD físicos canalizada en ladrillos.

### 8.2 Diversificación moneda
- Equity en USD, costos pesificados con cláusulas, ingresos en USD: mantener match.

### 8.3 Cuándo construir
- Períodos con costos USD bajos = momento de construir.
- Períodos con costos USD altos = momento de comprar terminado.

### 8.4 Cuándo vender
- Períodos con USD alto y mercado activo = momento de vender stock.
- Períodos de baja actividad = retener.

---

## 9. Frecuencia de actualización

### 9.1 Índices
- IPC: mensual.
- ICC y CAC: mensual.
- CER: diario.
- Tipos de cambio: continuo.

### 9.2 Modelos del developer
- Actualización mensual con cierre.
- Re-pricing de stock mensual.
- Ajuste de cuotas según contrato.

---

## 10. Errores comunes

- Trabajar exclusivamente en USD ignorando la dinámica del peso.
- No indexar las cuotas → compradores pagan precios "viejos".
- Asumir un único tipo de cambio.
- No prever bandas de redeterminación → conflictos con constructor.
- Ignorar la inflación de costos en USD.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** marco general, índices, mecánica de indexación, lógicas de cobertura.
- **🔴 Volátil:** valores actuales de IPC, ICC, CAC, tipos de cambio → INDEC, CAC, BCRA, mercado.
- **🔴 Caso particular:** modelo de un proyecto → analista financiero.

---

**Ver también:**
- `./fx-cambiario.md`
- `./politica-monetaria.md`
- `./ciclos-mercado.md`
- `./escenarios.md`
- `../06-financiero/cashflow-real-estate.md`
- `../05-construccion/certificacion-obra.md`
