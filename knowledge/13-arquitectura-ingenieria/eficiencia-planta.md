---
title: "Eficiencia de planta — m² vendible vs construido, factor K"
topic: "arquitectura-ingenieria"
subtopic: "eficiencia"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "CPAU — Métricas de proyecto"
  - "Manuales de proyecto residencial AR"
keywords: [eficiencia planta, m2 vendible, m2 construido, factor k, factor ocupacion, espacios comunes, circulaciones, rentabilidad arquitectura]
audience: ["developer", "arquitecto", "inversor", "chat"]
confidence: "alta"
---

# Eficiencia de planta

## TL;DR
- **Eficiencia = m² vendibles / m² construidos.** Es la métrica más importante del diseño desde el punto de vista del developer.
- Edificio residencial AMBA bien diseñado: **75-85% eficiencia**. Por debajo de 70%, el proyecto pierde rentabilidad rápido.
- **Factor K** = m² balcón / m² propio (otras métricas locales lo definen distinto).
- Cada punto porcentual de eficiencia se traduce en utilidad final del developer.

## 1. Definiciones clave

### 1.1 m² construidos
- Total construido del edificio: UFs + común + circulaciones + tabiques + estructura.
- Es lo que paga el developer al constructor.

### 1.2 m² propios / vendibles
- m² interiores de las UF (lo que el comprador "se lleva").
- Si hay balcón propio: se suele computar al 50% en algunos códigos.

### 1.3 m² comunes
- Hall, circulaciones, escaleras, ascensores, salas técnicas, amenities, baulera común.
- No vendibles directamente; en algunos casos prorrateados.

### 1.4 m² semicubiertos
- Balcones, pórticos, galerías.
- Cómputo variable según código urbanístico y según mercado (precio diferenciado).

### 1.5 m² cocheras y bauleras
- A veces venta separada, a veces incluida.
- Tienen su propio precio m².

## 2. Eficiencia — fórmula

```
Eficiencia = Σ m² propios vendibles / m² construidos totales
```

### 2.1 Rangos típicos AR

| Tipo de edificio | Eficiencia típica |
|---|---|
| Torre residencial bien diseñada | 75-82% |
| Edificio bajo / mediano | 78-85% |
| Edificio con muchos amenities | 70-77% |
| Oficinas A | 75-85% (depende del lobby) |
| Hotel | 60-70% (mucho común) |
| Logística | 90-95% |

## 3. Por qué importa tanto

### 3.1 Sensibilidad económica
- Subir 5 puntos de eficiencia (de 75% a 80%) en un edificio de 10.000 m² → 500 m² extra vendibles.
- A USD 3.000/m² → USD 1.500.000 adicionales en ingreso.
- Mismo costo de construcción.
- Casi todo se traduce en mayor utilidad.

### 3.2 Sensibilidad de pricing
- Edificio eficiente puede vender más barato y seguir rentable.
- Edificio ineficiente requiere precio más alto para cerrar.

## 4. Factor K (concepto local)

- **K = m² balcón / m² propio cubierto** (o m² semicubiertos / cubiertos según definición).
- Indicador de "cuánta planta vendida es semicubierta".
- Códigos urbanísticos suelen poner topes (típico K = 0.20-0.30 en residencial).
- Mercado valora positivamente balcones amplios (suben precio m²).

## 5. Variables que mueven la eficiencia

### 5.1 Volumen del edificio (cuanto más grande, más eficiente)
- Edificio chico tiene un % alto de circulaciones.
- Edificio grande diluye los m² comunes en más UFs.

### 5.2 Distribución de núcleos (ascensores + escaleras)
- Núcleos compactos = más eficiencia.
- Núcleos múltiples (premium con doble ascensor) = menos eficiencia.

### 5.3 Cantidad de UFs por piso
- 4-8 UFs por piso suelen ser óptimas en residencial.
- 2 UFs por piso (premium) = menos eficiencia.

### 5.4 Forma del edificio
- Rectángulos compactos = más eficiencia.
- Plantas en L, T, complejas = menos eficiencia.

### 5.5 Amenities
- SUM, piscina, gym, etc. → m² comunes que bajan eficiencia.
- Pero suben precio m² propio si están bien dimensionados.

### 5.6 Estacionamientos
- Subsuelos = más m² construidos no vendibles propios pero sí cocheras (otro mercado).
- Bicicleteros, depósitos.

## 6. Métricas auxiliares relevantes

### 6.1 UFs / m² construidos
- "Cuántas UFs por m² de obra" — mide diversificación del activo.

### 6.2 UFs / cocheras
- 1:1 ideal en gama media-alta.
- 0.7:1 aceptable en gama media.
- 0.5:1 en zonas con buen transporte.

### 6.3 m² promedio por UF
- Define el ticket medio.
- 30-60 m² monoambiente / 1amb.
- 60-90 m² 2-3 ambientes.
- 100-160 m² 3-4 ambientes.
- 180+ m² premium.

## 7. Tradeoffs típicos

### 7.1 Más amenities vs. más eficiencia
- Amenities cuestan eficiencia pero suben precio.
- Análisis: ¿el upside de precio paga el m² extra común?

### 7.2 Premium vs. masivo
- Premium quiere menos UFs por piso (más privacidad) → menos eficiencia.
- Compensa con precio m² mayor.

### 7.3 Plantas tipo vs. plantas variadas
- Plantas tipo iguales = construcción más barata + más eficiencia.
- Plantas variadas (penthouse, dúplex) = atractivo comercial.

## 8. Cómo el developer evalúa al arquitecto

- Pide **plantas con m² propios vs comunes vs semicubiertos**.
- Pide **ratio de eficiencia** del anteproyecto.
- Compara con benchmarks del segmento.
- Si la eficiencia es baja, exige justificación (¿es premium con razón?, ¿hay forma de mejorarla?).

## 9. Errores comunes

- No medir eficiencia desde el anteproyecto.
- Sobre-amenitiy un edificio masivo (pierde rentabilidad sin ganar precio).
- Plantas complejas por capricho arquitectónico.
- Núcleos múltiples sin razón comercial.
- Cocheras sub-aprovechadas en subsuelo (pasillos sobredimensionados).

## 10. Reglas operativas para el chat

- **Estable:** definiciones, rangos típicos, variables que mueven eficiencia, tradeoffs.
- **🔴 Volátil:** valor m² del mercado para calcular impacto en USD.
- Si el usuario aporta m² construidos y m² vendibles, el chat puede correr el cálculo y dar lectura.

## Ver también
- `./programa-arquitectonico.md`
- `../11-tasacion/metodo-residual-suelo.md`
- `../07-comercial/mix-tipologias.md`
- `../06-financiero/sensibilidad.md`
