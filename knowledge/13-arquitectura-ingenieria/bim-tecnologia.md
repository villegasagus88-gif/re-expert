---
title: "BIM y tecnología en arquitectura/ingeniería"
topic: "arquitectura-ingenieria"
subtopic: "bim"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "ISO 19650 — gestión BIM"
  - "buildingSMART International — IFC"
  - "Strategia BIM Argentina (Subsecretaría Obras Públicas)"
keywords: [bim, building information modeling, ifc, revit, archicad, navisworks, gemelo digital, digital twin, lod, ce, cad, coordinacion, clash detection, autodesk]
audience: ["arquitecto", "ingeniero", "developer", "chat"]
confidence: "alta"
---

# BIM y tecnología

## TL;DR
- **BIM** (Building Information Modeling) = trabajar con un **modelo digital 3D** que contiene información (materiales, costos, plazos, instalaciones, etc.) de todo el edificio.
- Beneficios principales: detección de conflictos antes de obra, mejor presupuestación, coordinación entre disciplinas, mantenimiento facilitado.
- En AR adopción creciente; obras públicas grandes ya lo exigen en algunos casos.
- Curva de aprendizaje + inversión en software + capacitación, pero retorno alto en edificios complejos.

## 1. Qué es BIM

### 1.1 Definición
- No es solo "3D bonito" — es un modelo paramétrico con datos.
- Cada objeto (muro, columna, ventana, caño) lleva metadata: dimensiones, material, costo, fabricante, mantenimiento.

### 1.2 Dimensiones BIM
- **3D**: geometría espacial.
- **4D**: 3D + tiempo (planificación, cronograma).
- **5D**: 4D + costos (presupuesto).
- **6D**: 5D + sostenibilidad / eficiencia energética.
- **7D**: 6D + facility management / mantenimiento post-obra.

### 1.3 LOD — Level of Development
- **LOD 100**: conceptual.
- **LOD 200**: aproximado (forma + dimensiones generales).
- **LOD 300**: preciso (forma + dimensiones + posición).
- **LOD 350**: incluye conexiones e interfaces.
- **LOD 400**: fabricación / instalación.
- **LOD 500**: as-built (lo construido tal cual).

## 2. Software principal

### 2.1 Diseño arquitectónico
- **Revit** (Autodesk) — dominante.
- **ArchiCAD** (Graphisoft) — alternativa fuerte.
- **Vectorworks** — menor cuota.

### 2.2 Estructura
- **Revit Structure**.
- **Tekla Structures** — fuerte en acero.

### 2.3 Instalaciones (MEP)
- **Revit MEP**.
- **MagiCAD**.

### 2.4 Coordinación / clash detection
- **Navisworks** (Autodesk).
- **BIM Track**, **BIMcollab**.

### 2.5 Visualización / renderizado
- **Twinmotion**, **Lumion**, **Enscape**, **V-Ray**.

### 2.6 Plataformas colaborativas
- **BIM 360 / Autodesk Construction Cloud**.
- **Trimble Connect**.
- **BIMcollab**.

## 3. Formato de intercambio

### 3.1 IFC (Industry Foundation Classes)
- Estándar abierto (buildingSMART International).
- ISO 16739.
- Permite interoperabilidad entre software (Revit ↔ ArchiCAD ↔ Tekla).
- Recomendado para que el dueño no quede atado a un proveedor.

## 4. Beneficios concretos

### 4.1 Para el developer
- Mejor presupuesto desde anteproyecto.
- Menos sorpresas en obra → menos imprevistos.
- Marketing: tour virtual realista, render, walk-through VR.
- Mantenimiento post-obra documentado.

### 4.2 Para el arquitecto
- Cambios de diseño propagan automáticamente.
- Cortes / vistas automáticos del modelo.
- Coordinación visual con ingenierías.

### 4.3 Para el ingeniero
- Modelo único = menos interpretación.
- Cálculo y simulación sobre el modelo.

### 4.4 Para la constructora
- Cubicación automática.
- Planificación 4D.
- Menos pérdida por errores de planos.

### 4.5 Para el operador / propietario final
- Modelo as-built para mantenimiento.
- Posible integración con IoT (sensores en edificio).
- Gemelo digital del activo.

## 5. Adopción en AR

### 5.1 Sector privado
- Estudios grandes y medianos: adoptado en proyectos medianos+.
- Proyectos premium / institucionales: estándar.

### 5.2 Sector público
- Estrategia BIM AR (Subsecretaría Obras Públicas).
- Obras públicas de cierta escala ya lo requieren.
- Tendencia ascendente.

### 5.3 Constructoras
- Adopción más lenta que estudios.
- Algunas grandes (CRIBA, Caputo, Riva) ya usan.

## 6. Costo de adoptar BIM

### 6.1 Software
- Licencias Revit / ArchiCAD: USD 2.000-3.500/año por usuario.
- Plataforma colaborativa: USD 600-1.500/año.

### 6.2 Hardware
- Workstations potentes: USD 2.500-5.000+.

### 6.3 Capacitación
- Cursos formales: USD 500-2.000 por persona.
- Curva de aprendizaje: 6-12 meses para productividad.

### 6.4 Modelado inicial
- Para un edificio mediano: 200-600 horas de modelado.

### 6.5 Retorno
- Reducción 10-30% de costos por mejor coordinación.
- Ahorro de re-trabajos en obra.
- Mejor velocidad de venta (marketing).

## 7. Gemelo digital (digital twin)

### 7.1 Concepto
- Réplica digital viva del edificio.
- Recibe data de sensores IoT en tiempo real.
- Permite operación + mantenimiento predictivo.

### 7.2 Casos
- Edificios corporativos: gestión energética, ocupación.
- Hospitales: trazabilidad de instalaciones críticas.
- Logística: gestión de almacenes.

### 7.3 Aún incipiente en AR
- Pocas implementaciones plenas.
- Crecimiento esperado en sectores premium / industriales.

## 8. Realidad virtual / aumentada

### 8.1 VR
- Tour virtual del proyecto antes de construir.
- Marketing premium: el comprador "camina" su UF.

### 8.2 AR
- Superponer el modelo en el sitio para verificación.
- En obra: replantear con AR.

## 9. Errores comunes

- Comprar Revit sin estrategia de implementación.
- Modelar sin definir LOD por etapa.
- No usar IFC → quedar atado a un proveedor.
- Modelar arquitectura solo, sin coordinar estructura / instalaciones.
- Esperar que BIM "solo" resuelva sin proceso humano detrás.

## 10. Reglas operativas para el chat

- **Estable:** qué es BIM, beneficios, software, dimensiones, LOD.
- **🔴 Volátil:** precios de licencias, adopción específica de sector.
- Si la pregunta es "¿uso BIM o no?": depende del tamaño del proyecto, complejidad, plan del operador, presupuesto.
- Recordar: BIM es **proceso + herramienta + cultura**. Sin proceso, el software no rinde.

## Ver también
- `./programa-arquitectonico.md`
- `./instalaciones.md`
- `../05-construccion/documentacion-obra.md`
- `../14-costos-presupuesto/`
- `../09-triple-impacto/eficiencia-energetica.md`
