---
title: "Curva S — distribución temporal de costos y avance"
topic: "costos-presupuesto"
subtopic: "curva-s"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
keywords: [curva s, cronograma, gantt, avance fisico, avance financiero, ritmo de obra, desembolsos, cashflow obra, certificacion]
audience: ["developer", "constructor", "PM", "chat"]
confidence: "alta"
---

# Curva S

## TL;DR
- **Curva S** = representación gráfica del **avance acumulado** (físico o financiero) en función del tiempo.
- Forma típica de "S": arranque lento (movimiento de suelos, fundaciones), aceleración (estructura + mampostería + instalaciones), desaceleración final (terminaciones).
- Sirve para: programar desembolsos, controlar avance real vs planificado, detectar desvíos temprano, gestionar flujo de caja.

## 1. Concepto

### 1.1 Eje X
- Tiempo (semanas o meses).

### 1.2 Eje Y
- Acumulado %: avance físico (m² construidos, ítems terminados) o financiero ($ ejecutado).

### 1.3 Forma de "S"
- Inicio lento: < 10% en primer trimestre.
- Crecimiento rápido: 60-80% del avance entre meses 4 y 18 (edificio mediano).
- Cierre lento: terminaciones, instalaciones finales, habilitaciones.

## 2. Etapas típicas de obra

### 2.1 Edificio residencial medio (24-30 meses)

| Mes | % avance acumulado |
|---|---|
| 1-3 | 5-10% (excavación, fundaciones) |
| 4-9 | 25-40% (estructura HºAº) |
| 10-15 | 50-65% (mampostería + instalaciones gruesas) |
| 16-21 | 75-85% (terminaciones interiores) |
| 22-28 | 95-100% (terminaciones finas, espacios comunes, final de obra) |

> 🔴 Curvas reales varían por sistema, escala y clima.

## 3. Aplicaciones

### 3.1 Flujo de caja (cashflow)
- Cada % de avance = un desembolso.
- El developer arma su funding (equity + pre-venta + crédito) para cubrir esa curva.
- **Curva de ingresos** (pre-venta) vs **curva de egresos** (obra) → necesidad de capital de trabajo.

### 3.2 Certificación de obra
- Constructora certifica avance mensual.
- Director de obra audita.
- Se libera el pago contra avance certificado.

### 3.3 Control de avance
- **Curva planificada** vs **curva real**.
- Desvío > 10% → alerta de gestión.

## 4. Variantes de curva S

### 4.1 Por sub-rubro
- Una curva S específica por rubro (estructura, terminaciones, instalaciones).
- Permite detectar dónde está el atraso.

### 4.2 Earned Value Management (EVM)
- **PV** (Planned Value): valor planificado a la fecha.
- **EV** (Earned Value): valor ganado (avance real × costo planeado).
- **AC** (Actual Cost): costo real incurrido.
- Índices: **SPI** = EV/PV (schedule), **CPI** = EV/AC (costo).
- SPI < 1 = atraso. CPI < 1 = sobrecosto.

## 5. Vínculo con cronograma (Gantt)

### 5.1 Gantt
- Tareas, dependencias, duración, ruta crítica.

### 5.2 Curva S deriva del Gantt
- Suma de pesos por tarea acumulado en el tiempo.

### 5.3 Software
- MS Project, Primavera P6, Procore, BIM 360, hojas Excel.

## 6. Curva S financiera (developer)

### 6.1 Egresos
- Obra (curva clásica).
- Suelo (gran egreso inicial).
- Honorarios (distribuidos en proyecto + ejecución).
- Comercialización (mayoría en primeros meses + entrega).
- Impuestos (puntual al cierre o por etapas).

### 6.2 Ingresos
- Pre-venta en pozo (irregular, depende de mercado).
- Saldo a escritura (entrega).
- Renta (si BTR, post-entrega).

### 6.3 Brecha = necesidad de capital
- El developer necesita financiar la brecha entre curva egresos y curva ingresos.
- Mientras más alto el pre-venta y antes, menor necesidad de equity / deuda.

## 7. Errores comunes

- Asumir desembolso lineal (mismo % cada mes) → subestimar pico mes 8-15.
- No diferenciar avance físico vs financiero (algunos ítems son caros y rápidos, otros baratos y lentos).
- No actualizar la curva con la realidad.
- Ignorar el efecto inflación en la curva nominal (en AR es relevante).
- No coordinar curva de ventas con curva de obra (entregar antes de poder = problema).

## 8. Curva S y contexto AR

### 8.1 Inflación
- En AR la curva nominal en pesos crece más rápido que la física.
- Modelar siempre en **USD constantes o moneda dura** + ajustar por índice (CAC, ICC, UVA).

### 8.2 FX
- Variaciones del USD impactan en materiales importados / pesos vs venta en USD.

### 8.3 Estacionalidad
- Diciembre/enero baja actividad de obra (vacaciones, lluvias).
- Junio/julio puede ralentizarse por frío.

## 9. Reglas operativas para el chat

- **Estable:** concepto, forma de la curva, aplicaciones.
- **🔴 Volátil:** % por etapa específicos → derivar del cronograma del proyecto.
- **Sensible:** la curva la arma el PM / director de obra.
- Si el usuario pregunta "¿cómo planifico el desembolso?", responder: armar Gantt detallado + derivar curva S + ajustar con sensibilidad.

## Ver también
- `./estructura-costos.md`
- `./control-presupuestario.md`
- `../05-construccion/`
- `../06-financiero/`
