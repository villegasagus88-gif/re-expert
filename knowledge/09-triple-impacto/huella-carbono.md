---
title: "Huella de carbono en construcción y operación"
topic: "triple-impacto"
subtopic: "huella-carbono"
jurisdiction: "Internacional + Argentina"
last_verified: "2026-05-10"
sources:
  - "GHG Protocol — corporate accounting"
  - "IPCC — informes climáticos"
  - "World Green Building Council"
keywords: [huella carbono, CO2, embebido, operacional, ciclo vida, net zero, compensacion, scopes]
audience: ["developer", "ESG specialist", "arquitecto"]
confidence: "alta"
---

# Huella de carbono

## TL;DR
- La huella de un edificio tiene dos componentes: **embebida** (construcción + materiales) y **operacional** (uso a lo largo de la vida útil).
- Edificios representan ~38% de las emisiones globales de CO2.
- En proyectos eficientes la huella operacional cae fuerte → la embebida pasa a dominar.
- Mediciones: GHG Protocol (3 scopes), Whole Life Carbon Assessment.

---

## 1. Conceptos básicos

### 1.1 Tipos de emisiones
- **Embebidas (embodied)**: emisiones por la fabricación, transporte y construcción de los materiales.
- **Operacionales**: emisiones por el uso (electricidad, gas, agua, residuos).
- **Fin de vida**: demolición, disposición, reciclado.

### 1.2 Whole Life Carbon
- Suma de embebidas + operacionales + fin de vida en toda la vida útil (típicamente 50-60 años).

### 1.3 Net zero
- Edificio cuyas emisiones netas se compensan a cero.
- Compensación: vía reducción + offsets (compra de créditos de carbono).

---

## 2. Huella embebida

### 2.1 Componentes
- **Estructura** (hormigón, acero): el mayor contribuyente. 50-60% típicamente.
- **Envolvente** (aberturas, mampostería).
- **Instalaciones** (cañerías, cableado, equipos).
- **Terminaciones** (pisos, revestimientos, sanitarios).
- **Transporte** de materiales a obra.
- **Construcción** propiamente (consumo de obra).

### 2.2 Materiales con alta huella
- Cemento Portland.
- Acero estructural.
- Aluminio.
- Aluminio anodizado.
- Plásticos derivados del petróleo.

### 2.3 Materiales con baja huella
- Madera certificada (FSC).
- Cementos con adiciones (escorias, puzolanas).
- Acero reciclado.
- Tierra cruda / adobe.
- Bambú.

### 2.4 Reducciones típicas
- Cemento bajo en C: -20-30%.
- Acero reciclado: -50%.
- Madera estructural CLT: -50-70% vs hormigón.

---

## 3. Huella operacional

### 3.1 Fuentes
- **Electricidad**: depende del mix de la red. AR ~60% térmica + 30% hidro + renovables.
- **Gas natural**: calefacción y agua caliente.
- **Agua**: bombeo y tratamiento.
- **Residuos**: descomposición y disposición.

### 3.2 Reducciones
- Eficiencia energética: aislación, equipos eficientes.
- Energía solar: fotovoltaica + térmica.
- Bombas de calor (reemplazan calderas a gas).
- Iluminación LED + sensores.
- Domótica para optimizar consumos.

### 3.3 Net Zero Operacional
- Genera tanta energía como consume (idealmente local).
- Edificios passivhaus + solar + eficiente.

---

## 4. GHG Protocol — Scopes

### 4.1 Scope 1
- Emisiones directas: combustibles quemados en el edificio (gas natural).

### 4.2 Scope 2
- Emisiones indirectas por electricidad comprada.

### 4.3 Scope 3
- Resto de la cadena: materiales, transporte, residuos, viajes de los empleados, etc.

### 4.4 Reportes
- Inventario corporativo (la empresa).
- Inventario por edificio.

---

## 5. Cálculo de huella en un proyecto

### 5.1 Software
- One Click LCA.
- Tally (Revit plugin).
- BEAM Software.

### 5.2 Inputs
- Cantidades de materiales (por planos / cómputo).
- Factores de emisión por material (depende de origen).
- Consumo energético previsto (simulación).

### 5.3 Output
- kgCO2e/m² embebido.
- kgCO2e/m²/año operacional.
- Total Whole Life.

### 5.4 Benchmarks
- Edificio convencional: 800-1.500 kgCO2e/m² embebido.
- Edificio eficiente: 400-700 kgCO2e/m² embebido.
- Net Zero ready: < 300 kgCO2e/m² embebido.

---

## 6. Compensación (offsets)

### 6.1 Mecanismos
- Forestación / reforestación.
- Energía renovable adicional (REC).
- Captura de metano.
- Eficiencia energética en otros edificios.

### 6.2 Calidad
- Verificados por terceros (Verra, Gold Standard).
- Adicionalidad: el offset financia algo que no hubiera ocurrido sin él.
- Permanencia: el carbono queda secuestrado en el largo plazo.

### 6.3 Costo
- USD 5-50/tCO2e según calidad.

### 6.4 Crítica
- "Greenwashing": comprar offsets baratos de baja calidad para declarar net zero.
- Mejor: reducir primero, compensar al final.

---

## 7. Marco regulatorio AR

### 7.1 Ley 27.520 (Cambio Climático)
- Marco general nacional.
- Plan Nacional de Adaptación y Mitigación.

### 7.2 NDC
- Compromisos internos del país a reducir emisiones (Acuerdo de París).

### 7.3 Acción provincial
- Algunas provincias tienen leyes y programas más avanzados.
- CABA: Plan de Acción Climática.

### 7.4 Sector construcción
- Por ahora sin regulación obligatoria de huella en RE AR.
- Tendencia internacional sugiere que llegará.

---

## 8. Implicancias para el developer

### 8.1 Obligaciones futuras
- Anticipar requisitos regulatorios.
- Reducir huella desde ahora minimiza costo de adaptación futuro.

### 8.2 Diferenciación
- Edificios con huella declarada y baja: premium creciente.

### 8.3 Acceso a capital ESG
- Fondos verdes / sustentables exigen métricas claras.

### 8.4 Reportes corporativos
- Si la empresa avanza a reporte ESG (GRI, SASB), incluir huella es central.

---

## 9. Estrategia para reducir huella

### 9.1 Prioridad 1: diseño
- Forma compacta, orientación correcta.
- Reducir m² no esenciales.
- Usar luz natural y ventilación.

### 9.2 Prioridad 2: materiales
- Sustituir cemento alto en C.
- Acero reciclado.
- Madera certificada cuando aplica.

### 9.3 Prioridad 3: sistemas eficientes
- Bombas de calor.
- Solar.
- Domótica.

### 9.4 Prioridad 4: medición
- Documentar en obra cantidades reales.
- Comparar contra el modelo.

### 9.5 Prioridad 5: compensación
- Solo después de reducir lo posible.

---

## 10. Errores comunes

- Cero medición → no se puede mejorar lo que no se mide.
- Solo medir operacional ignorando embebida.
- Compensar sin reducir.
- Materiales de bajo costo con alta huella.
- Subestimar el aporte del transporte.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** conceptos, scopes, fuentes, herramientas, estrategia.
- **🟡 Semivolátil:** factores de emisión locales (varían).
- **🔴 Caso particular:** cálculo para un proyecto → especialista LCA.

---

**Ver también:**
- `./marco-conceptual.md`
- `./certificaciones.md`
- `./eficiencia-energetica.md`
- `./esg-inversores.md`
