---
title: "Logística de obra y acopio"
topic: "construccion"
subtopic: "logistica"
jurisdiction: "Argentina"
last_verified: "2026-05-12"
sources:
  - "Práctica habitual AR"
  - "Lean Construction Institute — logistics best practices"
keywords: [logistica, acopio, obrador, just in time, jit, descarga, recepcion, stock obra, materiales criticos, hierro, hormigon, layout obrador]
audience: ["jefe de obra", "project manager", "comprador", "developer"]
confidence: "alta"
---

# Logística y acopio en obra

## TL;DR
- La logística mal pensada **dispara costos ocultos**: hora-hombre improductiva, accidentes, retrabajos, costos financieros del stock.
- En obra urbana CABA/AMBA, la **planificación del obrador y los horarios de descarga** suele ser el cuello de botella.
- Mix óptimo: acopio de commodities estructurales con volatilidad de precio + JIT en terminaciones.

---

## 1. Diseño del obrador

### 1.1 Layout: zonas mínimas
- Acceso vehicular + maniobra de camiones.
- Zona de descarga + báscula si aplica.
- Pañol cerrado (herramienta, fungibles, EPP).
- Acopio cubierto (madera, hierro doblado, sanitarios).
- Acopio descubierto con cobertura básica (hierro en barra, hormigón premezclado: directo).
- Oficinas (DO + Constructor + comitente).
- Sanitarios + comedor + vestuario (Decreto 911/96).
- Botiquín + camilla.
- Lugar para residuos por tipo (RCD, peligrosos, papel).

### 1.2 Restricciones típicas en obra urbana
- Espacio limitado → acopio en planta baja o subsuelo según obra.
- Vereda limitada → horario y permiso municipal para descarga.
- Vecinos → ruido, polvo, vibraciones reguladas.
- Tránsito → permiso municipal de corte de calle si aplica.

### 1.3 Layout dinámico
- El obrador cambia con la obra. Layout fase casco ≠ layout fase terminaciones.
- Revisar cada 2-3 meses.

---

## 2. Permisos municipales para logística

### 2.1 CABA (referencial)
- Permiso de ocupación de vereda (valla, contenedor).
- Permiso de corte de calle (para descargas críticas, bombeos hormigón).
- Aviso a Tránsito (camión hormigonero, bombeo, grúa móvil).
- Horarios de descarga regulados por zona (típico: 8-18 hs en zonas céntricas, prohibido fines de semana en muchas comunas).

### 2.2 PBA / interior
- Cada municipio define ordenanzas. Verificar antes de programar entregas.

---

## 3. Acopio: criterios

### 3.1 Qué acopiar (típico AR contexto inflacionario)
- **Hierro** — alta volatilidad de precio + bajo costo de almacenamiento. Acopio frecuente.
- **Cemento** — vida útil 60-90 días (riesgo de endurecimiento). Acopio acotado.
- **Hormigón premezclado** — no se acopia. JIT puro.
- **Madera fenólica** — sí, si hay storage cubierto.
- **Mampuestos** — sí, en cantidades grandes con buen descuento.
- **Aberturas / muebles fijos / sanitarios** — no acopiar hasta que el rubro arranque (riesgo robo + cambio spec).

### 3.2 Cuánto acopiar
- En commodities con OC firmada: lo que se necesita para 30-60 días + buffer del 10%.
- En contextos de alta inflación: lock con anticipo + acopio físico cuando se puede.

### 3.3 Stock de seguridad
- Para materiales de alta criticidad de uso (alambre, electrodos, EPP): 7-14 días.

---

## 4. Recepción de materiales

### 4.1 Procedimiento
1. Verificar OC abierta + datos del remito.
2. Inspección visual (cantidad, daño, identificación de lote).
3. Inspección técnica si el material lo requiere (hierro: certificado de origen; hormigón: probeta).
4. Firma de remito conforme / con observación.
5. Carga en sistema (planilla stock o ERP).
6. Movimiento a acopio o consumo directo.

### 4.2 Rechazo
- Material no conforme → no se descarga, se devuelve.
- Si ya se descargó: nota de rechazo + se separa físicamente con cartel.

### 4.3 Trazabilidad
- Lote del material en partes de uso.
- Crítico en estructura (hierro, hormigón): vincular con probeta y planilla de hormigonado.

---

## 5. Movimiento interno de materiales

### 5.1 Vertical
- En obra con altura: grúa torre o autoelevador + montacargas.
- Planificar **plataformas de carga** por planta.
- Tiempos de subida son fricción real: planificar entregas por planta + agrupar cargas.

### 5.2 Horizontal
- Carretilla, hidrolavadora, autoelevador eléctrico interior.

### 5.3 Hora pico de grúa
- Limita la productividad de gremios. Coordinar uso entre estructura, instalaciones y terminaciones.

---

## 6. Just-in-time aplicado

### 6.1 Para qué rubros
- Aberturas (modular según planta).
- Pisos.
- Sanitarios + griferías.
- Pintura.
- Mobiliario fijo.

### 6.2 Requisitos
- Proveedor confiable + ventana de entrega estrecha (1-2 días).
- Coordinación con grúa / acceso.
- Espacio mínimo en obra para descarga (no para stock).

### 6.3 Riesgo
- Falla del proveedor frena obra inmediatamente.
- Mitigación: proveedor B identificado + stock mínimo de seguridad.

---

## 7. Mermas y pérdidas

### 7.1 Tipos
- Rotura en transporte / descarga.
- Mal estibo en acopio.
- Robo (interno o externo).
- Sobre-pedido (acopiar más de lo necesario y no usar).
- Cambio de spec (terminación que se queda guardada y no se usa).

### 7.2 Indicador
- **Coeficiente de pérdida** por rubro: % de material comprado que no termina puesto en obra.
- Hierro: 2-5%.
- Hormigón: 3-7%.
- Mampuestos: 3-5%.
- Pisos / revestimientos: 5-10%.
- Pintura: 5-15%.

### 7.3 Reducción
- Cómputo + pedido ajustado a real necesidad.
- Acopio cubierto y custodiado.
- Inventario mensual (ciego, no avisado).
- Política clara de descarte y reuso.

---

## 8. Residuos de obra (RCD)

### 8.1 Tipos
- Inertes: escombros, hormigón endurecido, ladrillo.
- Reciclables: hierro, madera, cartón, plástico.
- Peligrosos: lubricantes, pinturas, solventes, baterías.
- Asimilables urbanos: alimentos, sanitarios.

### 8.2 Gestión
- Contenedor diferenciado por tipo.
- Transportista habilitado por municipio.
- Manifiesto de carga + entrega.
- En obras grandes: plan de gestión de RCD aprobado.

### 8.3 Tendencia
- Algunos municipios obligan a separar y/o reciclar % mínimo.
- Ver `../09-triple-impacto/circular-construction.md`.

---

## 9. Coordinación con cronograma

### 9.1 Lead time por rubro (referencial AR)
| Rubro | Lead time aprox |
|---|---|
| Hormigón premezclado | 24-48 hs |
| Hierro doblado a medida | 7-15 días |
| Mampuestos | 1-3 días |
| Aberturas estándar | 30-60 días |
| Aberturas a medida | 60-90 días |
| Aberturas premium importadas | 90-150 días |
| Ascensores | 90-180 días (fabricación) + 30-45 días montaje |
| Estructura metálica | 60-120 días |
| Climatización VRF | 60-120 días |

> Valores típicos. Verificar con proveedor cada caso.

### 9.2 Look-ahead de compras
- 3-6 semanas hacia adelante para tareas; el look-ahead de compras suele ser de **8-12 semanas** porque incluye lead time + tránsito + tolerancia.

---

## 10. Errores comunes

- Acopiar terminaciones meses antes de usarlas → robo o cambio de spec.
- Layout estático sin revisión → obrador colapsado en fase terminaciones.
- No coordinar grúa entre gremios → tiempo muerto.
- Recibir sin chequear remito vs OC → pagos erróneos.
- No medir mermas → coeficientes de pérdida descontrolados.
- Olvidar el horario / permiso municipal de descarga → multa + camión a la espera.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** layout del obrador, criterios para acopiar o JIT, mecánica de recepción y trazabilidad, gestión de RCD, coordinación con cronograma.
- **🔴 Volátil:** lead times específicos (varían por marca y momento), coeficientes de pérdida puntuales (varían por equipo y disciplina), porcentajes de inflación / acopio óptimo.

---

**Ver también:**
- `./compras-proveedores.md`
- `./gestion-diaria-obra.md`
- `./higiene-seguridad.md`
- `../09-triple-impacto/circular-construction.md`
