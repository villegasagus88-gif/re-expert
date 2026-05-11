---
title: "MEP, CCL y stablecoin: dolarización legal y RE"
topic: "cnv-bcra"
subtopic: "mep-ccl"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "BCRA — Comunicaciones A vigentes"
  - "CNV — RG 1010/2024 (PSAV)"
keywords: [mep, ccl, contado con liquidacion, dolar bolsa, stablecoin, usdt, usdc, dolarizacion, bonos, al30, gd30]
audience: ["developer", "comprador", "inversor", "chat"]
confidence: "alta"
---

# MEP, CCL y stablecoin

## TL;DR
- **MEP** = USD vía compra/venta de bonos en bolsa AR.
- **CCL** = USD via bonos pero liquidados en el exterior.
- **Stablecoin** (USDT/USDC) = USD digital, marco PSAV en construcción.
- Tres mecanismos legales (con sus matices) para dolarizar / movilizar capital en AR.

## 1. MEP — Mercado Electrónico de Pagos / Dólar Bolsa

### 1.1 Mecánica
1. Comprar bonos en pesos (típicamente AL30, GD30).
2. Vender los mismos bonos en USD (en su especie USD).
3. Resultado: USD en cuenta comitente.

### 1.2 Tiempo
- Operación completa: 1-2 días hábiles (T+1 o T+2 según especie).

### 1.3 Costo
- Spread bid/ask del bono.
- Comisiones broker.
- Total efectivo: 0.5-2% típicamente.

### 1.4 Restricciones
- Parking: a veces se requiere mantener el bono X días.
- Si compraste USD MEP, no acceso a oficial 90 días (típico).

### 1.5 Aplicación a RE
- Reservar USD para pagar boleto en USD billete.
- Compradores AR usan habitualmente.

## 2. CCL — Contado con Liquidación

### 2.1 Mecánica
1. Comprar bonos en pesos AR.
2. Transferir bonos a cuenta de broker en el exterior.
3. Vender bonos en USD en NY o Montevideo.
4. USD queda en cuenta en el exterior.

### 2.2 Tiempo
- 3-5 días hábiles típicamente.

### 2.3 Costo
- Similar al MEP + comisiones internacionales.

### 2.4 Restricciones
- Tope mensual a veces aplicado.
- Restricciones para acceder al MULC después.

### 2.5 Aplicación a RE
- Salida de USD al exterior para diversificar.
- Inversores que arman cartera offshore.
- Repatriar utilidades de proyectos AR.

## 3. Stablecoin

### 3.1 Qué son
- Tokens crypto con valor estable atado a USD.
- **USDT** (Tether), **USDC** (Circle), **DAI** (descentralizado).

### 3.2 Mecánica de uso AR
1. Comprar USDT/USDC en exchange local o internacional.
2. Custodiar en wallet (cold / hot / exchange).
3. Transferir / vender cuando se requiere.

### 3.3 Plataformas AR
- Belo, Lemon, Buenbit, Ripio, Bitso, Binance.
- Bajo nuevo marco CNV PSAV.

### 3.4 Ventajas
- Liquidez 24/7.
- Sin restricciones bancarias / horario.
- Costos bajos.

### 3.5 Riesgos
- Regulatorio (marco en construcción).
- Custodia (perder claves = perder fondos).
- Riesgo de emisor (USDT colapso = riesgo bajo pero existente).
- Exchanges (bancarrota / hack).

### 3.6 Aplicación a RE
- Pagos / pre-venta entre privados (con cuidado UIF).
- Custodia de capital antes de cierre.
- Pago a freelancers internacionales (arquitecto / consultor).

## 4. Compliance

### 4.1 MEP / CCL
- Bancarizado.
- Reportado en cuenta comitente.
- Declarable a AFIP.

### 4.2 Stablecoin
- Sujeto obligado UIF (PSAV registrado).
- KYC obligatorio.
- Reportes (Res. UIF y Ley 27.739).
- Declarar tenencia (Bienes Personales).

### 4.3 Operación inmobiliaria
- Origen de fondos documentado.
- Comprador: KYC + DDC.
- Escribanos: sujetos obligados (Res UIF 21/2018).
- Inmobiliarias: sujetos obligados (Res UIF 28/2018).

## 5. Comparativa rápida

| Mecanismo | Tiempo | Costo | Risk | Use case típico |
|---|---|---|---|---|
| MEP | 1-2 días | 0.5-2% | Bajo | Dolarizar para pago RE local |
| CCL | 3-5 días | 0.7-2.5% | Bajo-medio | Sacar USD al exterior |
| Stablecoin | minutos | 0.1-1% | Medio (regulatorio) | Pagos rápidos, custodia |
| USD billete | inmediato | 0% mercado | Bajo (físico) | Cierre escritura RE |
| MULC | depende | tipo oficial | Variable | Importaciones, compradores ext |

## 6. Casos de uso en RE

### 6.1 Comprador AR con pesos
1. Convierte pesos → USD MEP.
2. Custodia USD billete o cuenta USD AR.
3. Paga reserva + boleto en USD.
4. Cierre escritura.

### 6.2 Comprador AR con USD billete
1. Tiene USD físico.
2. Bancariza para pasar UIF (si > USD 1.000).
3. Paga directo.

### 6.3 Comprador extranjero
1. Transfiere USD a banco AR vía SWIFT.
2. Liquidación obligatoria en MULC (a oficial).
3. Pesos a pagar (con brecha negativa si hay cepo).
4. Alternativa: escribanía con USD billete (ingreso por viaje + declaración).

### 6.4 Developer cobrando cuotas en USD pozo
1. Recibe USD billete del comprador.
2. Bancariza (Ley 25.345).
3. Custodia / fideicomiso.
4. Mantiene en USD o convierte a pesos para pagar obra (según estrategia).

### 6.5 Inversor saca utilidades al exterior
1. Estructura legal previa (vehículo).
2. Distribución de utilidades.
3. Conversión a USD vía CCL → exterior.

## 7. Errores comunes

- Operar con cueva → riesgo UIF + AFIP.
- No declarar tenencias cripto.
- Asumir que USDT es 100% seguro.
- Olvidar parking en MEP/CCL.
- No documentar origen de USD físico.

## 8. Reglas operativas para el chat

- **Estable:** mecánica de los tres canales.
- **🔴 Volátil:** restricciones específicas, paridad MEP/CCL/oficial → mercado al día.
- **Sensible:** estrategia cambiaria requiere asesor + cumplimiento UIF + AFIP.
- Si el usuario pregunta "¿cómo paso pesos a USD legal?": MEP es la vía principal. Costo + tiempo + parking aplicables.

## Ver también
- `./cepo-cambiario.md`
- `./psav-cripto.md`
- `../08-macro-argentina/fx-cambiario.md`
- `../16-uif-blanqueo/kyc-y-origen-de-fondos.md`
- `../15-tecnologia-proptech/tokenizacion-blockchain.md`
