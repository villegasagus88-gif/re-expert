---
title: "Análisis de Precios Unitarios (APU)"
topic: "costos-presupuesto"
subtopic: "apu"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "Cámara Argentina de la Construcción (CAC)"
  - "INDEC — ICC"
  - "Manuales técnicos de constructoras"
keywords: [apu, analisis precio unitario, computo metrico, presupuesto obra, materiales, mano obra, equipos, gastos generales, utilidad, hh, jornal]
audience: ["developer", "constructor", "PM", "chat"]
confidence: "alta"
---

# Análisis de Precios Unitarios (APU)

## TL;DR
- **APU** = descomposición del precio de cada ítem de obra en sus componentes: **materiales + mano de obra + equipos + gastos generales + utilidad**.
- Es la base del presupuesto serio. Sin APU, los números son "a ojo".
- Estructura típica: cantidad × precio unitario por ítem → suma + GG + utilidad + impuestos.
- En AR se trabaja por **cómputo métrico + APU** (CAC, INDEC siguen esta lógica).

## 1. Estructura del APU

### 1.1 Componentes
1. **Materiales**: cemento, hierro, ladrillo, etc. → precio puesto en obra (con flete + pérdidas).
2. **Mano de obra**: horas-hombre (HH) × jornal (con cargas sociales).
3. **Equipos**: amortización + alquiler + combustible + operador.
4. **Gastos generales (GG)**: 8-15% sobre directos (obrador, supervisión, EPP, agua/luz obra).
5. **Utilidad / beneficio**: 10-20% según contratación y riesgo.
6. **Impuestos**: IVA, IIBB, sellos.

### 1.2 Fórmula simplificada
```
Precio unitario = (Materiales + MO + Equipos) × (1 + GG%) × (1 + Utilidad%) × (1 + Impuestos%)
```

## 2. Materiales

### 2.1 Componentes del precio
- Precio en depósito.
- Flete a obra.
- Descarga.
- **Pérdidas/desperdicios**: 5-10% según ítem (mampostería ~5%, revoque ~10%, hierro ~3%).
- Acopio (interés del capital inmovilizado).

### 2.2 Insumos clave AR
- Cemento, cal, arena, piedra, ladrillo, hierro (ADN-420), hormigón elaborado.
- Cerámicos, sanitarios, grifería.
- Aberturas (carpintería).
- Instalaciones (caños, cables, artefactos).

## 3. Mano de obra

### 3.1 Jornal
- Salario básico convenio UOCRA + cargas sociales (~70-100% sobre básico).
- Categorías: oficial especializado, oficial, medio oficial, ayudante.

### 3.2 HH por ítem (referencia típica)
| Ítem | HH aproximadas |
|---|---|
| Mampostería ladrillo común (m²) | 1.5-2.5 |
| Revoque grueso (m²) | 0.8-1.2 |
| Contrapiso (m²) | 0.6-1.0 |
| Carpeta (m²) | 0.4-0.7 |
| Hormigón armado losa (m³) | 8-12 |

> 🔴 Valores varían por sistema constructivo, escala y rendimiento. Verificar con tablas CAC.

### 3.3 Productividad
- Sistema tradicional vs prefabricado.
- Curva de aprendizaje al inicio de obra.
- Clima, condiciones del sitio.

## 4. Equipos

### 4.1 Tipos
- Grúa torre, montacargas, hormigonera, vibradores, bombas, herramientas eléctricas.

### 4.2 Costos
- Alquiler diario/mensual.
- Operador (jornal).
- Combustible / energía.
- Amortización (si es propio).
- Movilización inicial y desmovilización final.

## 5. Gastos generales de obra (GG)

### 5.1 Directos al proyecto
- Obrador (oficina, comedor, baño).
- Director de obra, jefe de obra, capataces, administrativo.
- EPP (seguridad).
- Agua, luz, internet de obra.
- Seguros (todo riesgo construcción, responsabilidad civil).
- Vigilancia.

### 5.2 Indirectos (estructura empresa)
- Oficina central prorrateada.
- Gerencia, contabilidad, RRHH.

### 5.3 Porcentaje típico
- GG directos: 8-12% sobre costo directo.
- GG indirectos: 3-6% adicional.

## 6. Utilidad / beneficio

### 6.1 Rangos típicos AR
- Constructora por contrato cerrado (llave en mano): 10-18%.
- Administración (admin fee): 8-15% sobre costo.
- Pozo / costo + fee: variable.

### 6.2 Factores
- Riesgo (suelo, plazo, complejidad).
- Posición de la empresa (estructura disponible).
- Competencia del mercado.

## 7. Impuestos sobre la obra

### 7.1 IVA
- 10.5% sobre obras de vivienda (alícuota reducida).
- 21% sobre obras comerciales/industriales.

### 7.2 IIBB
- 1-3.5% sobre facturación según jurisdicción.

### 7.3 Sellos
- En contratos de obra (varía por provincia).

### 7.4 Ganancias / cargas
- Embebidas en costo de personal y empresa.

## 8. Cómputo métrico

### 8.1 Qué es
- Medición cuantitativa de cada ítem del proyecto.
- Base sobre la que se aplica el precio unitario.

### 8.2 Buenas prácticas
- Cómputo por **planilla detallada** (por planta, por sector).
- Validación cruzada (computista + profesional independiente).
- BIM acelera y reduce errores.

### 8.3 Errores comunes
- Olvidar pérdidas/desperdicios.
- No medir terminaciones (zócalos, guardasillas, frisos).
- Olvidar instalaciones embutidas.
- Confundir m² útiles vs construidos.

## 9. Presentación del presupuesto

### 9.1 Niveles de detalle
- **Estimativo (anteproyecto):** precio/m² × superficie.
- **Por rubros:** descomposición en 15-25 rubros.
- **Detallado (proyecto ejecutivo):** APU completo por ítem.

### 9.2 Documentos del presupuesto
- Planilla de cómputo + APU.
- Memoria descriptiva.
- Pliego de especificaciones técnicas.
- Cronograma + curva S.
- Cláusulas de redeterminación / ajuste.

## 10. Errores comunes

- Presupuestar por "$/m² del vecino" sin APU propio.
- Olvidar GG e impuestos.
- No prever ajustes por inflación en obras > 6 meses.
- Subestimar imprevistos.
- No actualizar APU mensual en contexto inflacionario AR.

## 11. Reglas operativas para el chat

- **Estable:** metodología APU, estructura, conceptos.
- **🔴 Volátil:** precios de materiales, jornales, IIBB → INDEC, CAC, sindicato UOCRA, cotizaciones.
- **Sensible:** todo presupuesto definitivo lo firma profesional. El chat NO reemplaza al computista.
- Si el usuario pide "cuánto cuesta el m²", responder: depende sistema, calidad, ubicación → benchmark + APU detallado.

## Ver también
- `./estructura-costos.md`
- `./indices-costo.md`
- `./curva-s.md`
- `../13-arquitectura-ingenieria/`
- `../05-construccion/`
