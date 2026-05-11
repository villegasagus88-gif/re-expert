---
title: "Vehículos CNV aplicados a Real Estate"
topic: "cnv-bcra"
subtopic: "vehiculos"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "Ley 26.831, Ley 27.440"
  - "Normas CNV"
  - "Ley 24.083 (FCI)"
keywords: [fideicomiso financiero, fci cerrado, on, obligaciones negociables, cedear, reit, regimen pyme, securitizacion, valores fiduciarios]
audience: ["developer", "inversor", "asset manager", "chat"]
confidence: "alta"
---

# Vehículos CNV en RE

## TL;DR
- 4 vehículos clave CNV para canalizar inversión en RE: **Fideicomiso Financiero (FF)**, **FCI cerrado inmobiliario**, **Obligaciones Negociables (ON)**, **CEDEAR de REITs**.
- Cada uno tiene mecánica, costo y target de inversor distinto.
- En AR: FF + FCI cerrado son los más usados para canalizar capital institucional al sector.

## 1. Fideicomiso Financiero (FF)

### 1.1 Qué es
- Fideicomiso (CCyCN 1666+) con cuotapartes / valores fiduciarios ofrecidos al público bajo CNV.
- "Securitización" de flujos o activos.

### 1.2 Aplicación a RE
- FF que invierte en proyectos inmobiliarios.
- FF que securitiza alquileres / cuotas de boletos.
- FF con suelo + obra + venta.

### 1.3 Estructura
- **Fiduciante** aporta los bienes/derechos.
- **Fiduciario** (entidad financiera autorizada CNV) gestiona el patrimonio.
- **Beneficiarios** = inversores que tienen cuotapartes / VRD (valores representativos de deuda).
- **Fideicomisario** residual.

### 1.4 Clases de títulos
- **VDF** (Valores de Deuda Fiduciaria): renta fija, prelación de cobro.
- **CP** (Certificados de Participación): renta variable, residual.

### 1.5 Costos
- Estructuración legal: USD 50-200k.
- Calificación de riesgo: USD 20-50k.
- Fiduciario: 0.5-1.5% anual.
- Auditor: USD 10-50k anual.
- CNV: aranceles fijos + variables.

### 1.6 Plazo típico
- 3-7 años para proyecto inmobiliario.

## 2. FCI cerrado inmobiliario

### 2.1 Qué es
- Fondo Común de Inversión cerrado (Ley 24.083) que invierte en RE.
- Cuotas se compran en la suscripción inicial; salida = vender en mercado secundario o esperar fin de plazo.

### 2.2 Ver detalle
- `../06-financiero/fci-inmobiliarios.md`.

### 2.3 Diferencias clave con FF
- FCI cerrado: vida del fondo + estructura de gerente.
- FF: vida del proyecto + estructura fiduciaria.

## 3. Obligaciones Negociables (ON)

### 3.1 Qué son
- Bonos / deuda corporativa emitida por SA bajo régimen Ley 23.576.

### 3.2 Tipos
- **ON simple**: deuda pura.
- **ON convertible**: convertible en acciones.
- **ON garantizada**: con garantías reales (hipoteca, prenda).
- **ON dolar linked / USD payable / UVA**: distintas monedas o ajustes.

### 3.3 Régimen PYME CNV
- Para empresas pequeñas y medianas.
- Cargo regulatorio más bajo.
- Útil para developers chicos / medianos.

### 3.4 Aplicación a RE
- Developers grandes (IRSA, Consultatio, Argencons, Raghsa) emiten ON regularmente.
- Plazos típicos: 2-7 años.
- Tasas según riesgo emisor + moneda.

## 4. CEDEAR — Certificado de Depósito Argentino

### 4.1 Qué son
- Certificados negociables en AR que representan tenencia de valores extranjeros.

### 4.2 Aplicación a RE
- CEDEAR de **REITs** (Real Estate Investment Trusts) globales.
- Ejemplos: Simon Property Group, Realty Income, Vanguard Real Estate ETF (VNQ).
- Permite exposición a RE internacional sin sacar dólares del país.

### 4.3 Ventajas
- Diversificación geográfica.
- Liquidez (mercado AR).
- Cobro de dividendos.

### 4.4 Limitaciones
- Riesgo cambiario (CCL).
- Spread bid/ask en mercado AR.
- Comisiones brokers.

## 5. Acciones de empresas RE

### 5.1 AR
- IRSA, IRSA Propiedades Comerciales — cotizantes locales.
- Cresud (agro + RE).
- TGLT (cotizó).

### 5.2 NYSE / NASDAQ vía CEDEAR
- IRSA Inc. (NYSE).
- Cresud (NASDAQ).

## 6. Régimen impositivo (orientativo)

### 6.1 FF e FCI cerrado
- Transparencia fiscal: inversor tributa por la cuotaparte.
- Algunas ventajas según normativa vigente.

### 6.2 ON
- Intereses gravados según residencia + categoría.
- Posibles exenciones a personas humanas (verificar normativa vigente).

### 6.3 Acciones / CEDEAR
- Régimen Cedular para PHs argentinos.
- Tratamiento favorable a ciertas plusvalías.

> 🔴 Régimen tributario complejo + cambios frecuentes → asesor impositivo.

## 7. Comparativa rápida

| Vehículo | Inversor target | Capital min | Plazo típico | Liquidez |
|---|---|---|---|---|
| FF inmobiliario | Institucional + público | Variable | 3-7 años | Limitada |
| FCI cerrado RE | Mixto | USD 1.000-10.000 | 5-15 años | Mercado secundario |
| ON developer | Institucional + minorista | USD 1.000+ | 2-7 años | Buena (cotizante) |
| CEDEAR REIT | Minorista | USD 50+ | Indefinido | Alta |
| Acción cotizante RE | Minorista | USD 50+ | Indefinido | Alta |

## 8. Quién intermedia

### 8.1 Agentes Colocadores (CNV)
- Bancos + sociedades de bolsa autorizados.
- Galicia, Macro, Santander, BBVA, etc.
- Sociedades de bolsa: Allaria, Adcap, PPI, Cohen, Bell, etc.

### 8.2 Asesores
- Estudio jurídico (CNV + tributario).
- Asset manager (si FCI).
- Calificadora (FF y ON).
- Auditor.

## 9. Selección del vehículo

### 9.1 Proyecto chico (<USD 3M)
- Difícil amortizar costos CNV.
- Mejor: SAS + inversores privados o fideicomiso ordinario.

### 9.2 Proyecto mediano (USD 3-15M)
- FF privado o FCI cerrado puede empezar a tener sentido.
- ON PYME para developers con track record.

### 9.3 Proyecto grande (>USD 15M)
- FF público.
- ON.
- Acciones (si la empresa va a bolsa).

## 10. Errores comunes

- Estructurar CNV "para verse profesional" sin tamaño que justifique los costos.
- Olvidar costos recurrentes (auditor + fiduciario + CNV cada año).
- No prever obligaciones de información al inversor.
- Subestimar tiempo de estructuración (6-12 meses).

## 11. Reglas operativas para el chat

- **Estable:** vehículos y su mecánica.
- **🔴 Volátil:** régimen tributario, requisitos puntuales CNV → consultar normativa al día.
- **Sensible:** estructurar vehículo CNV requiere asesor especializado.
- Si el usuario pregunta "¿qué vehículo elijo?", responder: depende del tamaño + perfil del inversor + horizonte. Para <USD 3M raramente conviene CNV.

## Ver también
- `./marco-cnv.md`
- `./oferta-publica.md`
- `../06-financiero/fci-inmobiliarios.md`
- `../04-impuestos/estructuras-fiscales/fideicomiso-financiero.md`
- `../04-impuestos/estructuras-fiscales/comparativa-vehiculos.md`
