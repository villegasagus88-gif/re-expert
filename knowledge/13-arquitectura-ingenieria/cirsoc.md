---
title: "Reglamentos CIRSOC — normas estructurales y de construcción AR"
topic: "arquitectura-ingenieria"
subtopic: "cirsoc"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "CIRSOC — Centro de Investigación de los Reglamentos Nacionales de Seguridad para las Obras Civiles"
  - "INTI — Instituto Nacional de Tecnología Industrial"
  - "INPRES — Instituto Nacional de Prevención Sísmica"
keywords: [cirsoc, normas estructurales, hormigon armado, acero, madera, mamposteria, fundaciones, cargas, viento, sismo, cirsoc 201, cirsoc 301, inpres-cirsoc 103]
audience: ["arquitecto", "ingeniero", "developer", "chat"]
confidence: "alta"
---

# Reglamentos CIRSOC

## TL;DR
- **CIRSOC** = Centro de Investigación de los Reglamentos Nacionales de Seguridad para las Obras Civiles. Establece las normas estructurales obligatorias en AR.
- Cubre: cargas, viento, sismo (INPRES-CIRSOC 103), hormigón armado, acero, madera, mampostería, fundaciones.
- Aplicación obligatoria en obras nuevas + criterio en proyectos existentes.
- 🔴 Versiones de las normas se actualizan. Verificar versión vigente al momento del proyecto.

## 1. Marco general

### 1.1 Qué es CIRSOC
- Organismo creado en 1980 por INTI + INPRES + Cámara Argentina de la Construcción.
- Compila y actualiza los Reglamentos Argentinos de Seguridad para Obras Civiles.

### 1.2 Obligatoriedad
- Algunos reglamentos son **legalmente obligatorios** (incorporados a códigos de edificación).
- Otros tienen carácter **técnico-obligatorio** (deben respetarse por buena práctica).

### 1.3 Estructura de los reglamentos
- Numeración: **CIRSOC NNN** donde NNN es el código del reglamento.
- Series principales:
  - 100-199 → Cargas y acciones.
  - 200-299 → Hormigón armado.
  - 300-399 → Estructuras de acero.
  - 400-499 → Otros materiales (madera, aluminio).
  - 500-599 → Fundaciones.
  - 600-699 → Mampostería.

## 2. Reglamentos principales

### 2.1 CIRSOC 101 — Cargas y sobrecargas gravitatorias
- Cargas permanentes (peso propio).
- Cargas variables (uso, ocupación).
- Cargas accidentales.

### 2.2 CIRSOC 102 — Acción del viento
- Cálculo de cargas por viento.
- Zonas eólicas de AR.
- Coeficientes según altura, exposición, forma.

### 2.3 INPRES-CIRSOC 103 — Acción sísmica
- Zonas sísmicas de AR (zona 0 a 4 según peligrosidad).
- Coeficientes sísmicos.
- Diseño antisísmico.
- Ver `./sismicidad-inpres.md`.

### 2.4 CIRSOC 104 — Acción de la nieve y el hielo
- Cargas en zonas con nevadas (Patagonia, alta montaña).

### 2.5 CIRSOC 201 — Hormigón armado y pretensado
- El más usado en RE residencial AR.
- Reemplazó al antiguo CIRSOC 201-82.
- Sigue lineamientos ACI (American Concrete Institute).

### 2.6 CIRSOC 301 / 302 / 303 / 304 — Acero
- Estructuras metálicas, frío y caliente.

### 2.7 CIRSOC 401 — Estudios geotécnicos
- Reconocimiento de suelos.
- Ensayos.

### 2.8 CIRSOC 501 — Fundaciones
- Bases, pilotes, plateas.
- Capacidad portante.
- Ver `./estudio-suelos.md`.

### 2.9 CIRSOC 601 / 602 — Mampostería
- Mampostería portante y no portante.

## 3. Aplicación práctica al proyecto

### 3.1 Quién firma el cálculo estructural
- **Ingeniero civil matriculado** (CPIC en CABA, CIC en provincias).
- Firma el proyecto de estructura + memoria de cálculo.

### 3.2 Documentación que produce el ingeniero
- Memoria de cálculo estructural.
- Planos de estructura (encofrado, armadura, detalles).
- Planilla de hierros.
- Especificaciones de hormigón (calidad H, recubrimientos).
- Memoria descriptiva.

### 3.3 Coordinación con el arquitecto
- El arquitecto define forma + función.
- El ingeniero valida estructuralmente y propone soluciones.
- En proyectos complejos, BIM facilita la coordinación.

## 4. Materiales más usados en AR

### 4.1 Hormigón armado
- Calidades estándar: H-21, H-25, H-30, H-35 (resistencia característica MPa).
- H-21 / H-25 en residencial común.
- H-30+ en edificios altos.

### 4.2 Acero
- Construcciones industriales, naves, oficinas modulares.
- Steel framing en residencial liviano.

### 4.3 Mampostería
- Tradicional ladrillo cerámico hueco/macizo.
- Bloques de hormigón.
- Mampostería portante en edificios bajos.

### 4.4 Madera (steel framing alternativa)
- Patagonia, zonas turísticas.
- Norma CIRSOC 601 / 602 en mampostería; específicas para madera están en desarrollo.

## 5. Ensayos de materiales

### 5.1 Hormigón
- Probetas (rotura a 7 y 28 días).
- Slump (asentamiento).
- Carbonatación / espesor del recubrimiento.

### 5.2 Acero
- Ensayos de tracción, doblado.
- Certificación de origen.

### 5.3 Soldaduras
- Inspección visual + ensayos no destructivos.

## 6. Errores comunes

- Adoptar un código extranjero (ACI, Eurocódigo) sin adaptar a CIRSOC argentino.
- No considerar zona sísmica.
- Subestimar cargas por viento en zonas costeras.
- Diseñar sin estudio de suelos.
- Cambios estructurales durante la obra sin recalcular.

## 7. Reglas operativas para el chat

- **Estable:** mapa de reglamentos, materiales típicos, qué profesional firma cada cosa.
- **🔴 Volátil:** versión vigente de cada reglamento → CIRSOC.
- **Sensible:** todo cálculo estructural lo firma ingeniero matriculado. El chat NO calcula estructuras.

## Ver también
- `./sismicidad-inpres.md`
- `./estudio-suelos.md`
- `./instalaciones.md`
- `../02-normativa/codigo-edificacion-caba.md`
- `../05-construccion/garantias-vicios-ruina.md`
