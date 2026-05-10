---
title: "Régimen cambiario y tipo de cambio en Argentina"
topic: "macro"
subtopic: "fx-cambiario"
jurisdiction: "Argentina"
last_verified: "2026-05-10"
sources:
  - "BCRA — Comunicaciones de cambios"
  - "AFIP — impuesto PAIS y percepciones"
  - "Mercado de capitales (BYMA)"
keywords: [tipo cambio, USD, MEP, CCL, blue, brecha, cepo, BCRA, dolarizacion]
audience: ["developer", "financiero", "comprador", "inversor"]
confidence: "alta"
---

# Régimen cambiario y FX

## TL;DR
- Argentina tuvo, en los últimos años, **múltiples tipos de cambio coexistentes**: oficial, MEP, CCL, blue, "tarjeta", "cripto".
- La **brecha** entre tipos es indicador de stress cambiario.
- En real estate AR los precios suelen expresarse en **USD MEP / CCL**, mientras los costos están parcialmente en pesos.
- El régimen cambia frecuentemente — verificar normativa BCRA vigente al momento.

---

## 1. Tipos de cambio históricos coexistentes

### 1.1 Oficial mayorista (BCRA)
- Tipo de cambio mayorista al que opera el Banco Central.
- Referencia para importaciones y exportaciones autorizadas.

### 1.2 Oficial minorista
- Para personas físicas en bancos.
- Sumando: impuesto PAIS, percepciones a cuenta de Ganancias / Bienes Personales.
- Resulta más alto que el mayorista.

### 1.3 MEP / Bolsa
- Compra y venta de bonos en pesos y vendiéndolos en USD.
- Legal, declarado.
- Más cercano al precio real del USD.

### 1.4 CCL (Contado con Liquidación)
- Compra de bonos en BA, venta en NY.
- Legal, declarado.
- Permite girar al exterior.

### 1.5 Blue / informal
- Mercado paralelo no regulado.
- No declarado.
- Refleja la verdad del mercado en escenarios de cepo.

### 1.6 Cripto
- Stablecoins (USDT, USDC, DAI).
- USD físicos vía P2P.
- Cada vez más usados como referencia.

---

## 2. Brecha cambiaria

### 2.1 Qué mide
$$ \text{Brecha} = \frac{\text{TC libre} - \text{TC oficial}}{\text{TC oficial}} \times 100\% $$

### 2.2 Niveles típicos
- 🔴 Volátil — variable según momento. En crisis: 80-150%; estable: 5-30%.

### 2.3 Implicancias
- A mayor brecha → más dificultad para ejecutar pagos al exterior.
- Importadores con TC oficial → ventaja competitiva.
- Exportadores liquidan al oficial → desincentivo.

---

## 3. Cepo cambiario

### 3.1 Concepto
- Restricciones para acceder al USD oficial.
- Variantes: cupos personas físicas (USD 200/mes histórico), restricciones a empresas, "candado" en MEP/CCL.

### 3.2 Impacto en RE
- Compradores no pueden acceder a USD oficial fácilmente.
- Operaciones se hacen vía MEP / CCL / cripto / efectivo.
- Escrituras: típicamente en USD billete, dependiendo del marco vigente.

### 3.3 Riesgos
- Cambios bruscos en el régimen.
- Restricciones a la cesión de boletos en USD.
- Modificaciones a la operatoria MEP / CCL.

---

## 4. Mercado inmobiliario y dolarización

### 4.1 Por qué se dolariza
- Reserva de valor frente a inflación.
- Tradición histórica.
- Confianza del comprador en USD.

### 4.2 Cómo se opera
- Boletos en USD, generalmente USD billete (físico).
- Algunas operaciones en USD MEP por transferencia bancaria.
- Escrituras: USD físicos en escribanía + acta de entrega de fondos.

### 4.3 Conversión
- Compradores convierten pesos → USD vía MEP / CCL / blue.
- Costo implícito: brecha.

### 4.4 Implicancias para developer
- Stock en USD: protección frente a la inflación local.
- Ingresos en USD: estabilidad real del proyecto.
- Pero: parte del costo en pesos sin trasladar 1:1.

---

## 5. Dólar tarjeta y otros

### 5.1 Dólar tarjeta
- Compras al exterior con tarjeta.
- Lleva impuesto PAIS + percepciones (varía).
- Más caro que el oficial.

### 5.2 Dólar Qatar / dólar ahorro
- Variantes según contexto.
- Distintos niveles de impuestos.

### 5.3 Dólar exportador / importador
- Esquemas temporales que dan TC mejor a sectores específicos.
- Soja, energía, etc.

> 🔴 Volátil. Cada gobierno crea sus propios "dólares". Verificar régimen vigente.

---

## 6. Política cambiaria del BCRA

### 6.1 Régimen
- Flotación administrada vs flotación libre vs tipo fijo.
- Bandas de flotación.
- Crawling peg (devaluación gradual programada).

### 6.2 Reservas
- Nivel de reservas brutas y netas del BCRA.
- Indicador de capacidad para sostener el TC.

### 6.3 Acuerdos
- IMF (FMI): condicionalidades.
- Swap con China.

---

## 7. Cobertura cambiaria

### 7.1 Forwards / futuros
- ROFEX (futuros del peso).
- Cobertura de TC para empresas.

### 7.2 Bonos en USD
- Activos dolarizados que protegen patrimonio.

### 7.3 Real estate
- Funciona como reserva en USD, aunque ilíquido.

### 7.4 Cripto / stablecoins
- Cada vez más usadas, especialmente para tickets chicos.

---

## 8. Implicancia para diferentes actores

### 8.1 Developer
- Cashflow modelado en USD.
- Cobertura de costos: comprar adelantado, indexar.
- Decisión de qué TC usar para conversión.

### 8.2 Comprador
- Compra UF en USD para preservar capital.
- Plan de pago: USD físicos vs cuotas en pesos indexadas.

### 8.3 Inversor
- Yield en USD del cap rate.
- Plusvalía en USD.
- Riesgo cambiario asumido al alquilar en pesos.

### 8.4 Renta de alquileres
- Alquileres en pesos vs en USD (depende del segmento).
- Impacto de la indexación en flujos.

---

## 9. Indicadores a seguir

- TC oficial mayorista y minorista.
- TC MEP y CCL.
- Brecha.
- Reservas brutas y netas BCRA.
- Resultado fiscal.
- Cuenta corriente.
- Riesgo país (EMBI+).

---

## 10. Errores comunes

- Confundir tipos de cambio en cálculos.
- Asumir que la brecha es estable.
- Ignorar restricciones a la operatoria USD.
- No tener plan B ante cambios regulatorios.
- Modelar todo a un solo TC sin sensibilizar.
- No declarar correctamente la operación (riesgo AFIP / UIF).

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** tipos de cambio, conceptos, brecha, dolarización del RE, indicadores.
- **🔴 Volátil:** valores actuales de TC, brecha, restricciones BCRA → consultar fuente oficial al momento.
- **🔴 Caso particular:** estructura de pago para una operación → escribano + asesor cambiario.

---

**Ver también:**
- `./inflacion.md`
- `./politica-monetaria.md`
- `./ciclos-mercado.md`
- `./escenarios.md`
- `../06-financiero/cashflow-real-estate.md`
- `../_meta/data-policy.md`
