---
title: "Cepo cambiario y restricciones BCRA"
topic: "cnv-bcra"
subtopic: "cepo"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "BCRA — Comunicaciones A (vigentes)"
  - "Ley 27.541 (Emergencia 2019)"
  - "Decreto 609/2019"
keywords: [cepo, control de cambios, bcra, comunicacion a, mulc, mercado unico cambios, formacion activos externos, importaciones, dividendos, restricciones]
audience: ["developer", "comprador", "extranjero", "abogado", "chat"]
confidence: "alta"
---

# Cepo cambiario y BCRA

## TL;DR
- **Cepo cambiario** = conjunto de restricciones BCRA al acceso al mercado oficial de cambios (MULC).
- En AR el cepo se ha endurecido o aflojado según la coyuntura (2011-2015, 2019-actualidad).
- En RE impacta: dolarización legal, pago a proveedores extranjeros, remisión de utilidades, alquileres en USD a no residentes, compras de extranjeros.
- 🔴 Marco altamente volátil. Verificar Comunicaciones A vigentes.

## 1. Estructura del mercado cambiario AR

### 1.1 MULC (Mercado Único y Libre de Cambios)
- Mercado oficial regulado por BCRA.
- Tipo de cambio: **USD oficial** (mayorista / minorista).

### 1.2 MEP / Bolsa
- Mercado de valores (MEP) — vía compra/venta de bonos.
- Legal y declarable.
- Cotización: USD MEP.

### 1.3 CCL (Contado con Liquidación / Cable)
- Compra de activos en AR + venta en exterior.
- Permite "salir" del país con USD.
- Legal pero con restricciones.

### 1.4 Blue / informal
- Mercado paralelo (cueva).
- Informal e indeclarable.
- Para empleo institucional o de developer: **no usar**.

### 1.5 Brecha cambiaria
- Diferencia entre USD oficial y MEP/CCL/blue.
- Varía: 0% (sin cepo) a 100%+ (cepos duros).

## 2. Marco normativo

### 2.1 BCRA — Comunicaciones A
- Forma típica de regulación.
- "Com. A 7777" formato.
- Actualizadas mensualmente.

### 2.2 Ley 27.541 (Emergencia 2019)
- Marco que habilita restricciones extendidas.

### 2.3 Decreto 609/2019
- Norma fundacional del cepo actual.

### 2.4 AFIP / RG
- Percepciones / impuesto PAIS (cuando hubiera).

## 3. Restricciones típicas

### 3.1 A personas humanas
- Cupo mensual USD 200 al oficial (suspendido / variable).
- Percepciones impositivas (35% adicional histórico).
- Prohibición de comprar oficial si se compró MEP/CCL en 90 días.

### 3.2 A personas jurídicas
- Acceso al MULC sólo para importaciones autorizadas.
- Pago a proveedores: cronograma SIRA / sistema vigente.
- Remisión de utilidades / dividendos: restringido.
- Pago de deuda: cronograma BCRA.

### 3.3 A no residentes
- Restricciones a la salida de utilidades.
- Restricciones a la repatriación de capital.

### 3.4 A operaciones inmobiliarias
- Pago de compra de inmueble en USD: típicamente fuera del cepo (mercado libre USD físico entre privados).
- Si se necesita comprar USD desde pesos para pagar inmueble: usar MEP.
- Compradores extranjeros: ingreso de USD vía MULC genera obligación de liquidación.

## 4. Impacto en Real Estate

### 4.1 Precios en USD
- Mercado RE AR opera en USD desde décadas.
- Brecha cambiaria afecta competitividad regional + atractivo para extranjeros.

### 4.2 Costos en pesos / ingresos en USD
- Developer: ingresa en USD (venta), paga obra en pesos (con materiales y MO ligados al oficial / blue).
- Brecha amplia → mayor margen "contable" pero también más riesgo cambiario.

### 4.3 Pre-venta en USD
- Compradores AR tienen USD billete (no MULC).
- Pagos en cuotas USD billete = común en pozo.

### 4.4 Compra de extranjeros
- Necesitan ingresar fondos vía sistema bancario (Ley 26.737 + Res UIF).
- Marco más complejo en cepo.

### 4.5 Remisión de utilidades a inversor extranjero
- Restricciones BCRA limitan salida.
- Estructuración legal previa para mitigar (offshore + tributación correcta).

### 4.6 Importación de materiales
- HVAC, ascensores, terminaciones premium importadas → impacto SIRA / cuotas.
- Plazo de pago + brecha = riesgo de costo.

## 5. Mecanismos legales de dolarización en RE

### 5.1 MEP
- Compra USD vía bonos.
- Common para reservar USD antes de pagar boleto.

### 5.2 CCL
- Para tener USD en cuenta del exterior.
- Útil para inversores que quieren externalizar.

### 5.3 USD billete
- Operaciones entre privados.
- Escribanías custodian el cierre.

### 5.4 Stablecoin (USDT / USDC)
- Marco PSAV en construcción.
- Usado informalmente pero gana legalidad.

## 6. Cómo afecta al developer

### 6.1 Modelo financiero
- Hay que sensibilizar por escenarios de brecha (10%, 30%, 80%+).
- USD oficial vs MEP impacta directo.

### 6.2 Contratos
- Especificar moneda y mecanismo de conversión.
- Cláusula USD billete vs MEP vs Oficial.

### 6.3 Cobranza
- Recibir USD billete + custodia en cajas + procesos AML.
- Estructurar para cumplir UIF (sujeto obligado).

### 6.4 Pago a contratistas
- En pesos. Coordinar con ICC + redeterminación.

### 6.5 Inversores no residentes
- Estructura corporativa previa.
- Vehículo offshore + holding.
- Asesor tributario internacional.

## 7. Apertura / cierre del cepo

### 7.1 Cuando se afloja
- Aumenta confianza.
- Comprador extranjero vuelve.
- Cap rate mejora.
- Pozo más demandado.

### 7.2 Cuando se endurece
- Mercado se "argentiniza".
- Operaciones cash USD.
- Bajan precios USD por ajuste.
- Permanece movimiento por urgencia (mudanza, herencia, divorcio).

### 7.3 Histórico
- 2002-2003: post-corralito, mercado deprimido.
- 2011-2015: cepo Kirchner.
- 2016-2019: apertura Macri.
- 2019-2023: cepo Fernández.
- 2024-2026: liberalización Milei (gradual).

## 8. Compliance del developer

### 8.1 Bancarización
- Operaciones >USD 1.000 deben bancarizarse (Ley antievasión 25.345).

### 8.2 UIF
- Operaciones RE son sujetas a régimen de prevención de lavado.

### 8.3 BCRA reportes
- Posición cambiaria + ingresos / egresos de divisas reportados.

### 8.4 AFIP
- Operaciones inmobiliarias declaradas + COTI.

## 9. Errores comunes

- Subestimar volatilidad del marco cambiario.
- No tener cláusulas claras de moneda en boletos.
- Asumir que extranjeros pueden ingresar dinero sin trámite.
- Operar con efectivo informal (riesgo UIF).
- Asumir que cepo "se va" sin sensibilizar.

## 10. Reglas operativas para el chat

- **Estable:** estructura cambiaria + impacto general en RE.
- **🔴 Volátil:** Comunicaciones BCRA específicas, tipos de cambio, restricciones puntuales → BCRA al día.
- **Sensible:** estructuración cambiaria requiere asesor cambiario / abogado especializado.
- Si el usuario pregunta "¿cómo cobro USD?": dependiendo de origen (residente / extranjero), USD billete + bancarización + UIF.

## Ver también
- `./mep-ccl-cripto.md`
- `./marco-cnv.md`
- `../08-macro-argentina/fx-cambiario.md`
- `../16-uif-blanqueo/`
- `../12-suelo-y-dominio/ley-26737-tierras-rurales.md`
