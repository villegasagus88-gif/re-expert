---
title: "Instalaciones: electromecánica, sanitaria, gas, telecomunicaciones"
topic: "arquitectura-ingenieria"
subtopic: "instalaciones"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "AEA — Asociación Electrotécnica Argentina (Reglamento AEA 90364)"
  - "ENRE, ENARGAS — entes reguladores"
  - "Normas AySA, ABSA, empresas sanitarias provinciales"
  - "Códigos de Edificación CABA y provinciales"
keywords: [instalaciones, electrica, sanitaria, gas, ventilacion, hvac, telecomunicaciones, aea 90364, enargas, aysa, abas, edenor, edesur]
audience: ["arquitecto", "ingeniero", "developer", "chat"]
confidence: "alta"
---

# Instalaciones edilicias

## TL;DR
- Toda obra tiene 4-6 sistemas de instalaciones que coordinar: **eléctrica**, **sanitaria** (agua + cloaca), **gas**, **HVAC** (calefacción / ventilación / AC), **telecomunicaciones / datos**, **incendios**.
- Cada sistema tiene **profesional firmante** especializado + ente regulador + norma técnica.
- Suelen pesar 15-25% del costo total de obra (variable según calidad).
- Coordinación tardía = re-trabajos caros. BIM ayuda.

## 1. Instalación eléctrica

### 1.1 Norma principal
- **AEA 90364** (Asociación Electrotécnica Argentina) — versión vigente.
- Coordinada con CIRSOC para aspectos físicos.

### 1.2 Profesional
- Ingeniero electricista matriculado o instalador con matrícula.

### 1.3 Componentes típicos
- Tablero general + tableros por unidad.
- Acometida desde el medidor.
- Circuitos: iluminación, tomacorrientes generales, especiales (cocina, baño).
- Puesta a tierra (PAT) — obligatoria.
- Disyuntor diferencial — obligatorio.
- Llaves termomagnéticas.
- Iluminación de emergencia, salidas.

### 1.4 Empresa distribuidora
- CABA: Edenor, Edesur.
- AMBA y provincias: cada distribuidora.
- Aprueba acometida y medidor.

### 1.5 Verificación
- Habilitación AEA (CABA y muchas provincias).
- DCI (Declaración de Conformidad de Instalación).
- Final de obra eléctrico.

## 2. Instalación sanitaria

### 2.1 Norma
- AySA (CABA + AMBA) — reglamento.
- ABSA (PBA interior).
- Cada provincia / municipio: su empresa y norma.

### 2.2 Profesional
- Ingeniero sanitario o instalador matriculado.

### 2.3 Componentes
- **Agua fría**: medidor, columna, distribución por UF.
- **Agua caliente**: termotanque, calefón, sistema central.
- **Cloaca**: bajadas, ramales, salida a colectora.
- **Pluvial**: desagües de azotea, terraza, balcón.
- **Bombas y tanques** (presurización, reserva).
- **Drenaje** en sótanos.

### 2.4 Aprobaciones
- AySA / empresa provincial: aprobación de plano sanitario.
- Conexión de agua + cloaca: cargo separado.

## 3. Instalación de gas

### 3.1 Norma
- **ENARGAS** — Ente Nacional Regulador del Gas.
- Reglamentación específica + normas técnicas.

### 3.2 Profesional
- Matriculado en ENARGAS (gasista categoría I, II, III según escala).

### 3.3 Componentes
- Medidor.
- Columna distribuidora.
- Bajadas a las UFs.
- Cocinas, calefones, calderas, calefactores.
- Ventilaciones obligatorias.

### 3.4 Aprobaciones
- ENARGAS aprueba proyecto + inspecciones.
- Distribuidora: Metrogas (CABA), Camuzzi, Naturgy, Litoral Gas (regiones).
- Final de obra de gas obligatorio para habilitación.

### 3.5 Alternativas
- Edificios **all-electric** sin gas (tendencia creciente, especialmente premium).
- Implica más demanda eléctrica → coordinar con distribuidora.

## 4. HVAC (climatización, ventilación)

### 4.1 Calefacción
- Radiadores con caldera central (zona fría).
- Losa radiante.
- Split AC.
- Sistemas mixtos.

### 4.2 Aire acondicionado
- Splits individuales (más común).
- Sistemas VRV / VRF (premium).
- Chillers + fan coils (oficinas, hoteles).

### 4.3 Ventilación
- Forzada para baños interiores sin ventana.
- Cocinas con campana extractora.
- Garajes con extracción forzada.

### 4.4 Profesional
- Ingeniero mecánico o termomecánico.

## 5. Telecomunicaciones / datos

### 5.1 Componentes
- Acometida de fibra (FTTH).
- Distribución en muros: rack común, troncal por edificio.
- Tomas RJ-45 / fibra por UF.
- TV satelital / cable (LG abandonado, fibra dominante).
- Telefonía analógica (residual).

### 5.2 Profesional
- Especialista en telecomunicaciones.
- Norma TIA-568 internacional + adaptaciones locales.

## 6. Incendios

### 6.1 Norma
- Códigos de edificación + normas IRAM.
- Para edificios altos: protecciones extra.

### 6.2 Componentes
- Hidrantes (red de incendio independiente).
- Rociadores (sprinklers) — obligatorio en cierta altura/superficie.
- Detección de humo y alarma.
- Iluminación de emergencia.
- Salidas de emergencia + señalética.
- Cortinas cortafuego en circulaciones.
- Sistema de bombas + tanque dedicado.

### 6.3 Aprobación
- Bomberos / autoridad de aplicación.

## 7. Otras instalaciones

### 7.1 Domótica
- Premium: sistemas integrados de iluminación, climatización, audio, video, seguridad.

### 7.2 Energía solar
- Termotanques solares (creciente).
- Generación fotovoltaica (poco común en residencial AR, más en oficinas / industria).

### 7.3 Recolección de pluviales
- Para uso en riego de áreas verdes o sanitarios (sustentabilidad).

## 8. Coordinación entre instalaciones

### 8.1 BIM
- Modelo único con todas las instalaciones.
- Detecta conflictos (interferencias entre tuberías, ductos).
- Ahorra re-trabajo en obra.

### 8.2 Sin BIM
- Planos sectorizados.
- Reuniones de coordinación periódicas.
- Mayor riesgo de interferencias.

## 9. Costos típicos (orden de magnitud)

| Instalación | % del costo de obra |
|---|---|
| Eléctrica | 4-6% |
| Sanitaria | 3-5% |
| Gas | 1-2% |
| HVAC | 5-15% (depende calidad) |
| Telecomunicaciones | 0.5-1% |
| Incendios | 1-3% (sube en altura) |

> 🔴 Magnitudes varían por categoría, tecnología y geografía. ICC INDEC mide ARS; en USD varía con FX.

## 10. Errores comunes

- Empezar la obra sin proyecto coordinado de instalaciones.
- Subestimar potencia eléctrica para premium con AC + cocinas eléctricas.
- No prever ventilación forzada en cocinas / baños interiores.
- Olvidar pendiente sanitaria.
- No coordinar con bomberos para edificios altos.
- Sin BIM en edificios complejos → costos por interferencias.

## 11. Reglas operativas para el chat

- **Estable:** sistemas, profesionales, normas marco, componentes típicos.
- **🔴 Volátil:** versión vigente de AEA 90364, ENARGAS, tarifas de conexión → entes correspondientes.
- **Sensible:** cada sistema lo firma matriculado específico. El chat NO calcula instalaciones.

## Ver también
- `./programa-arquitectonico.md`
- `./bim-tecnologia.md`
- `../05-construccion/`
- `../02-normativa/codigo-edificacion-caba.md`
