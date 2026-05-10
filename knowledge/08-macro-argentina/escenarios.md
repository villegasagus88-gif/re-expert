---
title: "Construcción de escenarios macro para real estate"
topic: "macro"
subtopic: "escenarios"
jurisdiction: "Argentina"
last_verified: "2026-05-10"
sources:
  - "Práctica de mercado RE AR"
  - "Modelos de escenarios económicos (REM, consultoras)"
keywords: [escenarios, base, optimista, pesimista, stress, contingencia, prospectiva]
audience: ["financiero", "estratega", "developer"]
confidence: "alta"
---

# Construcción de escenarios macro

## TL;DR
- Escenarios = relatos coherentes de futuros macroeconómicos posibles.
- Mínimo 3 escenarios: **base + pesimista + optimista**.
- Cada escenario incluye: inflación, FX, actividad, política fiscal, política monetaria, marco regulatorio, demanda RE.
- Output: implicancias para el proyecto (cashflow, TIR, decisión).

---

## 1. Lógica de los escenarios

### 1.1 Por qué construirlos
- Proyectar a 3-5 años en Argentina con un único set de supuestos = ilusión.
- Múltiples futuros plausibles → tener un plan para cada uno.
- Comunicar incertidumbre a inversores con honestidad.

### 1.2 Cantidad
- 3 mínimo (base / pesimista / optimista).
- 4-5 si hay incertidumbre estructural alta (ej. cambio de régimen).

### 1.3 Coherencia interna
- Variables macro deben estar correlacionadas dentro del escenario.
- Ej: en pesimista no puede haber crecimiento alto + inflación baja + FX estable + crédito disponible.

---

## 2. Variables a definir por escenario

### 2.1 Macroeconómicas
- Crecimiento del PIB.
- Inflación anual (IPC).
- Tipo de cambio (oficial, MEP, brecha).
- Tasas de interés (BADLAR, hipotecaria).
- Reservas BCRA.
- Riesgo país.

### 2.2 Fiscales
- Resultado primario y financiero.
- Impuestos relevantes (alícuotas).
- Nuevos regímenes / promociones.
- Subsidios.

### 2.3 Marco regulatorio
- Cepo o no cepo.
- Régimen de alquileres.
- Régimen laboral (Ley Bases).
- Promociones sectoriales.

### 2.4 Demanda RE
- USD/m² promedio.
- Velocidad de venta.
- Disponibilidad de crédito hipotecario.
- Composición de compradores (uso vs inversor).

### 2.5 Costos RE
- USD/m² costo de obra.
- ICC / CAC anual.
- Salarios UOCRA.
- Materiales clave.

---

## 3. Escenario base

### 3.1 Lógica
- Continuación de la tendencia actual con cambios incrementales.
- Probabilidad típica asignada: 50-60%.

### 3.2 Plantilla
- Inflación cercana al consenso REM.
- Crecimiento moderado.
- TC ajustando lentamente.
- Política fiscal neutra.
- Marco regulatorio estable.

---

## 4. Escenario pesimista

### 4.1 Lógica
- Las cosas empeoran. Variables se mueven en correlación negativa.
- Probabilidad típica: 20-30%.

### 4.2 Drivers posibles
- Crisis cambiaria.
- Recesión profunda.
- Shock externo.
- Cambio de gobierno con políticas adversas.
- Pérdida de credibilidad institucional.

### 4.3 Variables
- Inflación más alta.
- Devaluación brusca.
- Caída del PIB.
- Tasas altas, crédito caro.
- Reaparición o agravamiento del cepo.
- Caída de USD/m² y de velocidad de venta.

### 4.4 Implicancias para RE
- Stock acumulado.
- Demoras de obra.
- Problemas de cashflow.
- Necesidad de descuentos.
- Mayor costo en USD del crédito.

---

## 5. Escenario optimista

### 5.1 Lógica
- Las cosas mejoran. Inversor extranjero, crédito, confianza.
- Probabilidad típica: 15-25%.

### 5.2 Drivers
- Estabilización exitosa.
- Vuelta del crédito hipotecario en escala.
- Apertura de cepo.
- Acuerdo con FMI exitoso.
- Boom de inversión externa.

### 5.3 Variables
- Inflación cae.
- TC estable.
- Crédito barato.
- Demanda RE en alza.

### 5.4 Implicancias
- Velocidad de venta alta.
- Precios USD/m² al alza.
- Posibilidad de subir precios.
- Mayor competencia (más proyectos).

---

## 6. Escenario de stress (a veces 4°)

### 6.1 Por qué
- Para verificar resiliencia del proyecto.
- No necesariamente probable, pero plausible.

### 6.2 Configuración
- Devaluación 100% sin trasladar precios.
- Pause de ventas 12 meses.
- Costo USD obra +40%.
- Default de un comprador grande.
- Cambios fiscales adversos.

### 6.3 Output
- ¿Sobrevive el proyecto?
- ¿Necesita llamadas de capital?
- ¿Vende stock con pérdida?

---

## 7. Probabilidades subjetivas

### 7.1 Distribución
- Asignar probabilidad a cada escenario.
- Suma = 100%.

### 7.2 Cálculo del VAN esperado
$$ VAN_{\text{esp}} = \sum_i p_i \cdot VAN_i $$

### 7.3 Discusión con socios
- Cada inversor puede tener distribución distinta.
- Acuerdo común sobre escenarios facilita decisiones.

---

## 8. Aplicación al proyecto

### 8.1 Modelo financiero por escenario
- Clonar el cashflow base.
- Ajustar variables según el escenario.
- Recalcular VAN, TIR, payback.

### 8.2 Decisiones derivadas
- Plan A para escenario base.
- Plan B para pesimista.
- Plan C para optimista (oportunidades adicionales).

### 8.3 Triggers
- ¿Qué evento dispara un cambio de plan?
- Ej: si la velocidad de venta cae 30% por 2 meses → activar plan B.

---

## 9. Comunicación a inversores

### 9.1 Honestidad
- Mostrar los 3 escenarios, no solo el optimista.
- Presentar implicancias claras de cada uno.

### 9.2 Ranges, no puntos
- "El proyecto entrega TIR entre 14% (pesimista) y 28% (optimista), con 19% en escenario base."
- Más confiable que un único número.

### 9.3 Sensibilidad
- Acompañar con análisis de sensibilidad (univariado).
- Refuerza credibilidad.

> Ver `../06-financiero/sensibilidad.md`.

---

## 10. Errores comunes

- Solo analizar el caso optimista.
- Construir escenarios incoherentes (variables descorrelacionadas).
- No actualizar los escenarios con nueva información.
- Pesimismo o optimismo sesgado por la situación personal.
- No definir triggers de acción.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** lógica, plantilla, variables, aplicación, comunicación.
- **🟡 Semivolátil:** distribución de probabilidades.
- **🔴 Volátil:** valores específicos por escenario en el momento → analista al momento.
- **🔴 Caso particular:** escenarios para un proyecto → estratega + financiero.

---

**Ver también:**
- `./inflacion.md`
- `./fx-cambiario.md`
- `./politica-monetaria.md`
- `./politica-fiscal.md`
- `./ciclos-mercado.md`
- `../06-financiero/sensibilidad.md`
- `../10-estrategia/decision-frameworks.md`
