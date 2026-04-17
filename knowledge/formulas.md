# Fórmulas Financieras y de Construcción — Argentina

## 1. Análisis de Inversión Inmobiliaria

### ROI (Return on Investment)
```
ROI = (Ganancia Neta / Inversión Total) x 100

Ejemplo:
  Inversión Total: USD 120,000
  Precio Venta: USD 165,000
  Costos (escritura, impuestos, comisión): USD 12,000
  Ganancia Neta = 165,000 - 120,000 - 12,000 = USD 33,000
  ROI = (33,000 / 120,000) x 100 = 27.5%
```

### ROI Anualizado
```
ROI Anual = ((1 + ROI)^(1/años) - 1) x 100

Ejemplo (proyecto de 2 años con ROI 27.5%):
  ROI Anual = ((1.275)^(1/2) - 1) x 100 = 12.9%
```

### Cap Rate (Tasa de Capitalización)
```
Cap Rate = (NOI anual / Valor de Mercado) x 100

NOI = Ingreso Bruto por Alquiler - Gastos Operativos
Gastos Operativos = Expensas + ABL + Seguro + Mantenimiento + Vacancia

Ejemplo (departamento en CABA):
  Alquiler mensual: USD 800
  Ingreso Bruto Anual: USD 9,600
  Gastos Operativos: USD 2,400 (25%)
  NOI: USD 7,200
  Valor Propiedad: USD 150,000
  Cap Rate = (7,200 / 150,000) x 100 = 4.8%
```

### TIR (Tasa Interna de Retorno)
```
La TIR es la tasa que hace VAN = 0.

0 = -Inversión + Σ(Flujo_t / (1 + TIR)^t)

Se calcula iterativamente. Regla general:
  TIR > Costo de Oportunidad → Proyecto viable
  TIR referencia Argentina (2026): 8-15% en USD para proyectos inmobiliarios
```

### VAN (Valor Actual Neto)
```
VAN = -Inversión_0 + Σ(Flujo_t / (1 + r)^t)

r = tasa de descuento (costo de oportunidad)

Ejemplo (fideicomiso 24 meses):
  Inversión: USD 100,000
  Flujos: mes 12 = USD 0, mes 24 = USD 135,000
  r = 10% anual
  VAN = -100,000 + 135,000 / (1.10)^2
  VAN = -100,000 + 111,570 = USD 11,570
  VAN > 0 → Proyecto viable
```

### Payback Period (Período de Recupero)
```
Payback = Inversión Inicial / Flujo de Caja Anual

Ejemplo (departamento para alquiler):
  Inversión: USD 95,000
  Alquiler neto anual: USD 6,000
  Payback = 95,000 / 6,000 = 15.8 años
```

## 2. Costos de Construcción

### Costo por m² según categoría (Argentina, Abril 2026)
```
Económica (vivienda social):        USD 650-800 /m²
Media (vivienda estándar):          USD 900-1,200 /m²
Media-Alta (buenas terminaciones):  USD 1,300-1,700 /m²
Premium (alta gama):                USD 1,800-2,500 /m²
Lujo (ultra premium):               USD 2,500-4,000 /m²

Fuente: Revista Vivienda / CAMARCO
Nota: incluye materiales + mano de obra, NO incluye terreno ni honorarios profesionales.
```

### Incidencia por rubro (vivienda media)
```
Estructura (hormigón + hierro):     22-28%
Mampostería:                         8-12%
Instalación sanitaria:               8-10%
Instalación eléctrica:               6-8%
Instalación de gas:                  3-4%
Pisos y revestimientos:              8-12%
Revoques y cielorrasos:              6-8%
Carpintería (aberturas):             8-12%
Pintura:                             3-5%
Cubierta (techo):                    5-8%
Varios (limpieza, obrador, seguros): 5-8%
Total:                              100%
```

### Cálculo de hormigón para losa
```
Vol_hormigón = Superficie x Espesor

Losa maciza:
  Vol = Sup x 0.12m (espesor típico 12cm)
  Ejemplo: losa 50m² → 50 x 0.12 = 6 m³ de H21

Losa de viguetas:
  Vol = Sup x 0.05m (carpeta de compresión 5cm)
  + viguetas aparte
  Ejemplo: losa 50m² → 50 x 0.05 = 2.5 m³ de H21
```

### Dosificación hormigón H21 (1 m³)
```
Cemento:   350 kg (7 bolsas de 50kg)
Arena:     0.65 m³
Piedra:    0.65 m³
Agua:      180 litros
```

### Mezcla para mampostería (1 m³)
```
Cemento:   200 kg (4 bolsas)
Cal:       100 kg (3.3 bolsas)
Arena:     1 m³
Agua:      250 litros
Rinde aprox: 30-35 m² de pared (ladrillo hueco 18)
```

## 3. Fórmulas de Superficie

### FOS (Factor de Ocupación del Suelo)
```
FOS = Superficie Cubierta Planta Baja / Superficie Terreno

Ejemplo:
  Terreno: 300 m²
  FOS permitido: 0.60
  Máximo a cubrir en PB: 300 x 0.60 = 180 m²
```

### FOT (Factor de Ocupación Total)
```
FOT = Superficie Total Cubierta / Superficie Terreno

Ejemplo:
  Terreno: 300 m²
  FOT permitido: 1.50
  Máximo a construir total: 300 x 1.50 = 450 m²
```

### Superficie Cubierta vs Semicubierta
```
Superficie cubierta: 100% computa para FOT
Superficie semicubierta: 50% computa para FOT
Balcones abiertos (según jurisdicción): 30-50% computa

Ejemplo:
  Cubierta: 120 m² (computa 120 m²)
  Cochera semicubierta: 30 m² (computa 15 m²)
  Balcón: 8 m² (computa 4 m²)
  Total para FOT: 139 m²
```

## 4. Impuestos y Costos de Transacción

### Compra de inmueble (CABA)
```
Escritura (comprador):        2-3% del valor escriturado
Comisión inmobiliaria:        3% + IVA (comprador) + 3% + IVA (vendedor)
Impuesto de sellos (CABA):    3.5% (puede haber exenciones vivienda única)
Certificados y trámites:      0.3-0.5%
ITI (vendedor):               1.5% del valor de venta
Ganancia (vendedor):          15% sobre ganancia (si aplica ley 27.430)

Costo total comprador: ~8-9% sobre el valor de compra
```

### Alquiler — Ley 27.737 (vigente 2026)
```
Plazo mínimo: 2 años (vivienda)
Ajuste: índice ICL del BCRA (trimestral o semestral según contrato)
Garantía: máximo 1 mes de alquiler (propietario individual)
Depósito: máximo 1 mes (devuelve actualizado al finalizar)
Comisión: 4.15% + IVA del monto total del contrato (solo locador)
Expensas ordinarias: locatario / Extraordinarias: locador
```

## 5. Conversión y Referencia

### Tipo de cambio referencia
```
Consultar siempre tipo de cambio oficial y MEP/CCL vigente.
Para proyectos de construcción se usa generalmente dólar MEP.
Para compraventa de inmuebles se usa dólar billete (blue/MEP según operación).
```

### Índice CAC (Cámara Argentina de la Construcción)
```
El índice CAC mide la variación de costos de construcción.
Se publica mensualmente en www.camarco.org.ar
Se usa para actualizar presupuestos en contratos de obra.

Fórmula de actualización:
  Monto_actualizado = Monto_original x (CAC_actual / CAC_base)
```
