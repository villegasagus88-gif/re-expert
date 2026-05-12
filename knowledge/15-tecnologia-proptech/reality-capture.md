---
title: "Reality capture: drones, fotogrametría y scan-to-BIM"
topic: "tecnologia"
subtopic: "reality-capture"
jurisdiction: "Global / AR"
last_verified: "2026-05-12"
sources:
  - "Práctica observada en grandes contratistas globales"
  - "Documentación pública (DJI, Matterport, OpenSpace, Leica)"
keywords: [reality capture, dron, drone, fotogrametria, lidar, escaner laser, laser scanner, scan to bim, point cloud, nube de puntos, matterport, openspace, 360, recorrido virtual, ortofoto, dem, dsm]
audience: ["arquitecto", "ingeniero", "jefe de obra", "developer", "data"]
confidence: "media-alta"
---

# Reality capture

## TL;DR
- "Reality capture" = capturar el mundo físico en forma digital tridimensional + temporal.
- Tres tecnologías dominantes: **drones** (exterior y volumetría), **escáner láser / LiDAR** (interior con precisión), **fotogrametría 360°** (recorrido para documentación rápida).
- Aplicaciones en real estate: due diligence pre-compra, control de obra, as-built validado, virtual tours para venta, documentación de patrimonio.
- En AR ya hay proveedores accesibles para drones y 360°; LiDAR profesional todavía nicho.

---

## 1. Drones

### 1.1 Tipos
- **Multi-rotor** (cuadricópteros): vuelos cortos, alta maniobrabilidad, ideales para obra.
- **Ala fija** (RPA tipo planeador): vuelos largos, áreas grandes (sitios extensos, agropecuario).

### 1.2 Sensores
- Cámara RGB (foto y video estándar).
- Cámara térmica (detección de pérdidas energéticas, fugas, fallas eléctricas).
- LiDAR aéreo (point cloud preciso, costoso).
- Cámara multiespectral (vegetación, suelo).

### 1.3 Casos de uso
- **Avance de obra**: vuelos semanales/quincenales. Ortofoto + DEM (Digital Elevation Model) + DSM.
- **Volumetría**: medición de movimiento de suelos, pilas de material.
- **Inspección de cubiertas / fachadas**: sin necesidad de andamio ni cuerdista.
- **Marketing**: video aéreo del proyecto.
- **Due diligence**: cobertura visual de terreno antes de comprar.
- **Inspección post-evento** (sismo, inundación, incendio).

### 1.4 Procesamiento
- **Pix4D / Agisoft Metashape / DroneDeploy / WebODM**: fotogrametría.
- Output: ortofoto, DEM, DSM, modelo 3D, point cloud.

### 1.5 Regulación AR
- ANAC (Administración Nacional de Aviación Civil) — RAAC parte 100.
- Registro del dron + matrícula.
- Licencia de operador (según categoría de dron).
- Vuelo BVLOS (más allá del rango visual): permiso adicional.
- Vuelo en zona urbana: requisitos específicos.

### 1.6 Costo
- Dron profesional + cámara: USD 2k-15k.
- Servicio tercerizado (vuelo + procesamiento): USD 300-2000 por vuelo según escala.

---

## 2. LiDAR / escáner láser

### 2.1 Qué hace
- Emite pulsos láser y mide el tiempo de retorno → genera point cloud (nube de puntos millones de puntos en 3D).
- Precisión: milímetros a centímetros.

### 2.2 Tipos
- **Estacionario terrestre** (Leica, Faro, Trimble): set en trípode, escanea desde un punto. Para interiores y exteriores precisos.
- **Móvil** (mochila o vehículo): se mueve y mapea.
- **Handheld** (NavVis, GeoSLAM): mochila / mano.
- **Aéreo** (en drone o avión): áreas grandes.

### 2.3 Casos de uso
- **Levantamiento de edificios existentes** (refacción, restauración).
- **As-built ultra preciso** de instalaciones complejas.
- **Inspección estructural** (deformaciones, fisuras grandes).
- **Patrimonio histórico**: documentación permanente.

### 2.4 Output
- Point cloud (formato E57, LAS).
- Mesh 3D.
- Drawings 2D extraídas (planos).
- Integración con BIM (scan-to-BIM).

### 2.5 Costo
- Equipo: USD 30k-150k.
- Servicio tercerizado: USD 1k-10k por edificio según tamaño y precisión.

---

## 3. Fotogrametría 360°

### 3.1 Qué hace
- Cámara con lente esférico (Insta360, Ricoh Theta, Matterport Pro2/3).
- Toma panorámicas cada 1-3 metros.
- Plataforma genera **recorrido virtual** + medición aproximada.

### 3.2 Casos de uso
- **Documentación de obra fase por fase** (cada semana): OpenSpace, Stryd, HoloBuilder.
- **Recorrido virtual para venta**: Matterport para inmuebles a comercializar.
- **Visita remota** (inversor, comprador internacional).
- **Documentación previa a tapar** (instalaciones embebidas).

### 3.3 Plataformas
- **Matterport**: estándar para virtual tours (venta).
- **OpenSpace**: documentación obra (tracking de avance).
- **HoloBuilder**: idem.
- **Cupix**: idem.

### 3.4 Precisión
- Centímetros (no milimétrica como LiDAR).
- Suficiente para documentación y venta, no para drawing-grade.

### 3.5 Costo
- Cámara 360 prosumer: USD 300-1000.
- Cámara Matterport Pro: USD 3-4k.
- Suscripción plataforma: USD 50-500/mes según features.
- Servicio tercerizado: USD 200-1000 por unidad.

---

## 4. Scan-to-BIM

### 4.1 Qué es
- Convertir point cloud en modelo BIM editable.
- Útil para refacción de edificios existentes sin documentación.

### 4.2 Workflow
1. Escanear edificio (LiDAR o fotogrametría).
2. Limpiar point cloud (remover ruido, gente, vehículos).
3. Modelar geometría en BIM (Revit con plugin point cloud).
4. Validar contra escaneo.

### 4.3 Esfuerzo típico
- Escaneo: 1-3 días para edificio mediano.
- Modelado: 5-30 días según complejidad.
- LOD destino: 200-300 típico, 400+ posible con mucha más mano de obra.

### 4.4 Output
- Modelo BIM editable + point cloud de referencia.
- Habilita proyecto de refacción / ampliación sobre base precisa.

---

## 5. Aplicaciones en el ciclo del developer

### 5.1 Pre-compra / due diligence
- Drone para vista general del terreno.
- Inspección de límites, accesos, vecinos.
- Si hay edificio existente: scan para evaluar reformas.

### 5.2 Diseño
- Si hay preexistencia: scan-to-BIM para arrancar con base real.

### 5.3 Obra
- Drones semanales para tracking volumétrico.
- 360° semanales para documentación.
- Comparación contra BIM para detectar desvíos.

### 5.4 Cierre / recepción
- 360° + drone para entrega.
- As-built validado.

### 5.5 Comercialización
- Matterport para virtual tour.
- Drone para video aéreo del proyecto.

### 5.6 Operación
- Documentación permanente para FM.
- Inspecciones periódicas con drone.

---

## 6. Integración con BIM y digital twin

### 6.1 Comparación scan vs modelo
- Software (BIM 360, ClearEdge3D, Verity): compara point cloud actual con BIM proyectado.
- Detecta desvíos en obra antes de que sea irreversible.
- Alimenta as-built validado.

### 6.2 Update del modelo
- Cambios reales detectados → actualización automática del modelo BIM.
- Base para el gemelo digital.

> Ver `./bim-gemelo-digital-operacion.md`.

---

## 7. ROI casos reportados

| Caso | Ahorro / mejora |
|---|---|
| Tracking de obra con drone vs estimación manual | 80-95% más rápido + datos objetivos |
| Detectar desvío estructural con scan | Ahorro de retrabajo de 5-15% del costo del rubro |
| Virtual tour Matterport en venta | +20-40% conversión de leads internacionales |
| Inspección de cubierta con drone vs cuerdista | 50-80% más rápido, sin riesgo |
| Scan-to-BIM en refacción | Reducción del 50% en re-mediciones / re-trabajo |

---

## 8. Workflow recomendado para developer mid-size

### 8.1 Setup básico (USD 5-10k inicial)
- Dron consumer/prosumer (DJI Mavic / Air).
- Cámara 360 (Insta360 X3 o Ricoh Theta).
- Software de procesamiento (suscripción).
- Operador entrenado interno.

### 8.2 Cadencia
- Drone: semanal en obra activa.
- 360°: semanal por planta en obras grandes.
- LiDAR: por encargo cuando se justifica.

### 8.3 Output
- Reporte semanal con foto / video / mediciones.
- Dashboard de avance.
- Documentación archivada por fecha.

---

## 9. Aspectos legales y operativos

### 9.1 Permisos vuelo dron
- ANAC RAAC parte 100.
- Notificación de vuelo en zonas controladas.
- Privacidad: no enfocar propiedades vecinas / personas sin consentimiento.

### 9.2 Datos generados
- Storage: la nube de puntos puede pesar GB-TB.
- Decisión: archivo a largo plazo (cloud frío) vs descarte tras procesamiento.

### 9.3 Compartir con terceros
- Compradores: virtual tour controlado.
- Inversores: ortofoto + reporte ejecutivo.
- Equipo interno: acceso total.

---

## 10. Errores comunes

- Volar sin permiso ANAC → multa + decomiso.
- No tener operador entrenado → vuelos peligrosos o data mala.
- Escanear sin propósito → archivos pesados sin uso.
- Confundir 360° con LiDAR (precisiones distintas, propósitos distintos).
- No validar el resultado contra realidad → drift sin detectar.
- Olvidar privacidad de vecinos en vuelos de drone.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** tipos de tecnología, casos de uso, workflow, regulación ANAC, ROI por categoría.
- **🔴 Volátil:** modelos específicos de equipo (cambian anualmente), precios precisos, suscripciones de plataforma.

---

**Ver también:**
- `./bim-gemelo-digital-operacion.md`
- `./ai-workflows-developers.md`
- `./plataformas-gestion-integral.md`
- `../05-construccion/gestion-diaria-obra.md`
- `../05-construccion/recepcion-obra.md`
- `../13-arquitectura-ingenieria/bim-revit-ifc.md`
