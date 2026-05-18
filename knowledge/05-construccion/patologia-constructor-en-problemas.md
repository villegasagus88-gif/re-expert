---
title: "Patología del constructor en problemas: señales tempranas, step-in y reemplazo"
topic: "construccion"
subtopic: "patologia-contratista"
jurisdiction: "Argentina"
last_verified: "2026-05-12"
sources:
  - "CCyCN — locación de obra (arts. 1251-1279) y resolución por incumplimiento (arts. 1083-1090)"
  - "LCT art. 30 — solidaridad del comitente"
  - "Ley 24.522 — concursos y quiebras"
  - "Decreto 911/96 — higiene y seguridad de la construcción"
  - "Práctica profesional habitual en obras privadas AR (cap obra, dirección, gestión de claims)"
keywords: [constructor en problemas, contratista en problemas, contratista quiebra, contratista concurso, abandono de obra, abandono obra, mora contratista, default contratista, sobrefacturacion, sobre facturacion, sobreprecio, certificacion inflada, sobre certificacion, avance papel, avance real, fraude obra, step in, step-in, reemplazo contratista, retencion solidaria, fondo de reparo, caucion, garantia fiel cumplimiento, art 30, solidaridad lct, subcontratista no pagado, acopio en riesgo, propiedad materiales, embargo obra, interdicto obra, claims preventivos, telegrama intimacion constructor, paralizacion obra, parada de obra, ieric, art 1083, art 1086, locacion de obra]
audience: ["developer", "director de obra", "project manager", "comitente", "fiduciario", "abogado", "controller"]
confidence: "alta"
---

# Patología del constructor en problemas

## TL;DR
- El constructor que está por reventar **manda señales** semanas o meses antes. El comitente que las ignora pierde tiempo, plata y la obra.
- Tres patologías típicas: **abandono / parálisis**, **sobrefacturación / fraude de avance** y **concurso o quiebra**. Cada una tiene workflow distinto.
- La defensa real no es contractual sino **operativa + documental**: certificación validada, retención del fondo de reparo, subcontratistas mapeados, libro de obra al día, fotos fechadas, caución viva.
- **Step-in** (toma de la obra y reemplazo del contratista) es legal pero solo se ejecuta limpio si el contrato lo prevé y la documentación lo soporta. Sin eso, se va a juicio largo.
- En AR sumar: solidaridad art 30 LCT, IERIC, ART y AFIP del subcontratista insolvente caen sobre el comitente si no retiene.

---

## 1. Qué se entiende por "constructor en problemas"

### 1.1 Tres patologías de fondo
1. **Patología de caja / solvencia**: el contratista no puede pagar a sus proveedores y operarios. Antesala del abandono o de la quiebra.
2. **Patología de gestión**: tiene caja pero el equipo no funciona (rotación, conflictos internos, cambios en dirección técnica, pérdida de control).
3. **Patología de fraude**: sobrefactura, sobrecertifica, desvía pagos, vende materiales del acopio. No siempre es premeditado; muchas veces empieza por urgencia financiera y se vuelve sistémico.

### 1.2 Tres desenlaces típicos
- **Abandono / parálisis** (rendir el contrato unilateralmente, dejar de ir, ritmo cero).
- **Resolución contractual** (por una u otra parte, judicial o extrajudicial).
- **Concurso preventivo / quiebra** (Ley 24.522), con efectos automáticos sobre la obra.

### 1.3 Por qué importa al comitente
- **Pérdida directa**: anticipos sin contraprestación, sobreprecios pagados.
- **Pérdida indirecta**: costo financiero de la parálisis, ventas perdidas en pozo, intereses de inversores, expensas anticipadas.
- **Pasivos heredados**: subcontratistas no pagados que persiguen al comitente vía art 30 LCT; embargos sobre acopio; multas IERIC / ART.
- **Riesgo penal-reputacional**: si hay fraude documentado y el comitente firmó certificados, queda como cómplice culposo o doloso ante un perito.

---

## 2. Early warnings (señales tempranas)

### 2.1 Señales de caja / solvencia
- **Demora en pago a subcontratistas** (preguntarles directamente, no al constructor).
- **Proveedores reclaman al comitente** o aparecen a "ver la obra".
- **Pedido de adelanto fuera del cronograma** por "tema puntual de caja".
- **Cambio de cuenta bancaria** para recibir pagos del comitente.
- **Cheques diferidos** propios cada vez más largos.
- **Maquinaria propia desaparece** de la obra (la rentaba y la devolvió, o la vendió).
- **Cambio frecuente de subcontratistas** en gremios críticos (estructura, instalaciones, terminaciones).
- **Llegada de materiales con descuento** sin justificar (puede ser segunda mano / sustituto / acopio de otra obra desviado).
- **Reducción de personal propio** del contratista en la obra (cap obra solo, sin equipo).
- **Reclamos AFIP / ART / IERIC** sobre nómina del contratista (consultar IERIC).

### 2.2 Señales de gestión
- **Rotación del jefe de obra** del contratista en pocos meses.
- **Cambio del director técnico / representante técnico** sin notificación formal.
- **Reuniones de coordinación canceladas** o reprogramadas reiteradamente.
- **RFIs y change orders pendientes** que se acumulan sin respuesta.
- **Plan de obra desactualizado** o el contratista evita actualizarlo.
- **Discrepancias entre lo que dice el jefe de obra y lo que dice el comercial / dueño** del contratista.
- **No entrega de pliegos firmados** (planes de inspección, ATR, planos de coordinación).

### 2.3 Señales de fraude / sobrefacturación
- **Avance certificado > avance físico** verificable (foto + medición).
- **Compra de materiales** certificada sin remito + factura + acopio identificable.
- **Mismas facturas** en distintos certificados.
- **Subcontratistas dicen no haber cobrado** lo que el contratista certificó.
- **Aceleración nominal** del avance sin correlato físico (curva S "milagrosa").
- **Retrabajos repetidos** en mismos rubros (firma del avance, después se rompe, se vuelve a "ejecutar").
- **Notas de crédito y descuentos** opacos en compras de materiales (puede haber rebate al constructor desviado).

### 2.4 Señales laborales (cae sobre el comitente vía art 30 LCT)
- **Telegrama de un operario** del subcontratista al comitente.
- **Ausentismo masivo** de cuadrilla por falta de pago.
- **Accidente sin denuncia ART** del subcontratista.
- **IERIC: nómina declarada < gente que se ve en obra**.
- **Sin recibos firmados** que pueda exhibir el subcontratista al pedírselos.

> Regla práctica: **si ves dos o más señales en simultáneo, activá protocolo de verificación inmediata.**

---

## 3. Sobrefacturación y avance papel vs real

### 3.1 Cómo se materializa
- **Compra de materiales con anticipo** que nunca llegan al acopio o llegan parcial.
- **Trabajo ejecutado al 100%** certificado cuando físicamente está al 60-70%.
- **Items "varios" o "auxiliares"** sin descomposición ni medición.
- **Doble certificación** del mismo item en distintos rubros.
- **Acopio "fantasma"** (declarado pero no presente).
- **Mano de obra certificada** sobre gente que no figura en IERIC.

### 3.2 Cómo detectarlo (auditoría operativa, no contable)
- **Medición física independiente** del certificado mensual por el director de obra y un representante del comitente. Acta + foto + medición real, no firma "tipo timbre".
- **Acopio**: inventario físico mensual con etiquetas / cartelería identificando propiedad.
- **Cruce remito-factura-acopio**: cada item facturado debe tener remito + acopio físico (o instalado verificable).
- **Subcontratistas**: pedirles **recibos firmados** por sus operarios y constancias de cobro al contratista principal.
- **Curva S** de avance físico (no de costo) firmada por dirección de obra.
- **Foto-registro fechado** por sector y semana.

### 3.3 Cómo reaccionar si lo detectás
1. **No firmar el certificado** sobre el item dudoso.
2. **Acta de discrepancia** en libro de obra + nota formal al contratista.
3. **Solicitar evidencia** de respaldo (remitos, facturas, acopio físico).
4. **Si no llega**: reducir el certificado a lo verificable + retención cautelar del importe disputado.
5. **Documentar** (acta + fotos + emails + nota) — todo va a ser prueba si escala.
6. **Asesor legal** desde acá si la diferencia es material (>5-10% del certificado o >2 meses recurrente).

> **Practica profesional**: el comitente que sigue firmando certificados sospechosos, en un juicio posterior queda mal parado — los firmó él. Mejor pelear cada certificado que firmar y reclamar después.

---

## 4. Subcontratistas no pagados y solidaridad art 30 LCT

### 4.1 Marco legal AR (art 30 LCT)
- El **comitente** (que cede o subcontrata trabajos correspondientes a su actividad normal y específica) responde **solidariamente** con el contratista por las obligaciones **laborales y de la seguridad social** de los trabajadores empleados por éste.
- En obra privada el comitente típicamente no es "empleador" pero queda atrapado por art 30 LCT por la **subcontratación** del contratista.
- Aplica también a **cooperativas** o vehículos análogos cuando hay fraude o tercerización encubierta (jurisprudencia consolidada).
- Norma: art 30 LCT + Ley 25.013 + jurisprudencia laboral.

> Ver `../03-laboral/solidaridad-art-30.md`.

### 4.2 Cómo se materializa el reclamo
- **Telegrama** del operario al comitente solicitando regularización + pago.
- **Demanda laboral** contra el contratista + comitente solidariamente.
- **Embargo** sobre la obra o sobre el activo del comitente.
- **Cargos AFIP / ART / IERIC** por aportes no ingresados, solidariamente.

### 4.3 Mecánica preventiva: la retención solidaria
- **Auditoría mensual** del paquete laboral de cada subcontratista (ver §10).
- **Si el subcontratista no entrega documentación al día**: el comitente **retiene** del certificado del contratista principal el importe equivalente a salarios + aportes + ART del mes.
- **Si el subcontratista sigue impago**: el comitente puede pagar directamente al operario (subrogación) o consignar judicialmente.
- **Cláusula contractual** (ver §7) debe habilitar expresamente esta retención.

### 4.4 Si el reclamo ya llegó
1. **Contestar el telegrama** dentro de plazo (24-48h hábiles típicas) con asesor laboral.
2. **No reconocer relación laboral** directa pero no negar la solidaridad sin asesor.
3. **Notificar al contratista** que retiene del próximo certificado.
4. **Intentar pago directo al operario** con quita / acuerdo homologado en SECLO.
5. **Si va a juicio**: armar prueba de buena fe del comitente (auditoría documentada, retenciones, intimaciones al contratista).

---

## 5. Acopio en riesgo

### 5.1 El problema
- Materiales en obra **sin identificación de propiedad** son materia ejecutable.
- Si el contratista quiebra (art 138 Ley 24.522) o tiene un acreedor con embargo, el síndico / oficial puede llevarse el acopio.
- El comitente pagó por adelantado, pero **el material legalmente es del contratista** salvo que se haya documentado la transferencia.

### 5.2 Cómo proteger el acopio
- **Cláusula contractual**: la propiedad del material **se transfiere al comitente al ingreso a obra** (no a la facturación, no a la instalación).
- **Cartelería física** en el acopio: "Propiedad de \[Comitente\] — Fideicomiso XX — Obra YY".
- **Acta de ingreso** firmada por dirección de obra + jefe obra del contratista cada vez que entra material por valor relevante.
- **Inventario mensual** con foto + planilla + firmas.
- **Seguro TRC** que incluya el valor de acopio del comitente.

### 5.3 Si el contratista cae en quiebra
- **Inmediato**: tomar posesión física del acopio con escribano + foto + acta + cartelería.
- **Presentación al síndico**: con respaldo documental (cláusula + actas + inventario + cartelería + facturas) reclamando que el acopio no integra la masa.
- **Cobertura del seguro** si hay daño / sustracción posterior.

---

## 6. Documentación procesal (todo es prueba)

### 6.1 Principio operativo
Lo que no está documentado **no existe** en un juicio. El comitente que pelea con WhatsApp y memoria pierde.

### 6.2 Documentación mínima vivida en obra
- **Libro de órdenes** foliado, en sitio, con firma semanal de director + representante técnico.
- **Parte diario** del cap obra del comitente (separado del parte del contratista).
- **Acta de cada reunión** de coordinación, firmada.
- **Foto-registro semanal** por sector, fechado (georeferenciado idealmente).
- **Certificados firmados** con acta de medición adjunta.
- **Notas formales** (CD / mail con acuse) para cada discrepancia material.
- **RFIs y change orders** con número de orden + plazo de respuesta + status.
- **Telegramas y CDs** archivados originales + escaneados.
- **Backup en nube** de todo.

### 6.3 Documentación específica para juicio futuro
- **Cronograma original** firmado + actualizaciones firmadas.
- **Certificados con discrepancias** marcadas + cómo se resolvieron.
- **Auditorías mensuales** del paquete laboral (AFIP / ART / IERIC) de cada subcontratista.
- **Inventario de acopio** con cartelería + actas.
- **Pericia técnica** preconstituida en momentos críticos (escribano + perito ad hoc verificando estado físico).
- **Cadena de comunicación** completa (CD / email / mensajería profesional, no WhatsApp personal del cap obra).

### 6.4 Práctica profesional clave
- **Escribir el problema** apenas se detecta. Nada queda "en el aire".
- **Acuse de recibo** explícito en cada comunicación al contratista.
- **Plazo razonable** en cada intimación (5-10 días hábiles típicos para subsanar).
- **No firmar nunca** documentos del contratista sin leerlos completos.
- **Pedir versión original** firmada de cada contrato y addendum.

---

## 7. Cláusulas contractuales preventivas

### 7.1 Garantías
- **Caución de fiel cumplimiento** (no aval personal): 5-10% del contrato, vigente hasta recepción definitiva + 6-12 meses. Aseguradora SSN registrada.
- **Caución de anticipo** equivalente al 100% del anticipo financiero.
- **Fondo de reparo**: 5-10% del avance, retenido en cada certificado, liberable post-recepción definitiva (mitad) y post-plazo de garantía (resto).
- **Seguro TRC** (todo riesgo construcción) con suma asegurada actualizada y cobertura del acopio del comitente.

> Ver `../18-seguros/caucion-y-garantias.md` y `../18-seguros/trc-construccion.md`.

### 7.2 Step-in y reemplazo
- **Cláusula de step-in**: ante incumplimiento, mora calificada, abandono o concurso/quiebra del contratista, el comitente puede:
  1. Intimar a subsanar en plazo razonable (10-15 días hábiles).
  2. Vencido el plazo sin subsanar, **resolver el contrato** (art 1083 y 1086 CCyCN, pacto comisorio expreso e implícito).
  3. **Tomar la obra** y continuarla por administración propia o con otro contratista.
  4. **Ejecutar la caución** + apropiarse del acopio + retener pagos pendientes.
- **Procedimiento explícito**: notificación → plazo → resolución → toma + acta de inventario + reemplazo.

### 7.3 Acopio
- **Transferencia de propiedad** al ingreso a obra (no a la facturación).
- **Cartelería e inventario** obligatorios mensuales.
- **Derecho del comitente** a inspeccionar el acopio en cualquier momento.

### 7.4 Subcontratistas
- **Lista cerrada** de subcontratistas aprobados (con derecho de veto del comitente).
- **Entrega mensual** del paquete laboral de cada uno (AFIP F931 + ART nómina + IERIC + recibos firmados).
- **Retención solidaria** habilitada ante incumplimiento.
- **Cláusula de step-in con el subcontratista directo** si el contratista principal lo abandona.

### 7.5 Información y auditoría
- **Auditoría externa** del comitente sobre certificados y compras.
- **Open book** sobre subcontratos críticos.
- **Plan de obra actualizado mensualmente** firmado.

### 7.6 Penalidades y resolución
- **Penalidad por mora** del contratista (por día/semana, con tope 10-15% del contrato).
- **Resolución por incumplimiento** con causa documentada.
- **Indemnidad** del comitente por reclamos de subcontratistas, operarios, AFIP, ART, IERIC.

> Ver `./modalidades-contratacion.md` y `./change-orders-claims.md`.

---

## 8. Step-in: workflow operativo

### 8.1 Cuándo se activa
- Abandono de obra (15-30 días sin avance, sin justificación).
- Mora calificada en hitos críticos.
- Insolvencia manifiesta (concurso, quiebra, embargos).
- Incumplimiento grave reiterado (calidad, plazo, S&H, laboral) tras intimación.
- Fraude documentado.

### 8.2 Pre-step-in (preparación)
1. **Asesor legal y técnico** alineados.
2. **Documentación reunida**: contrato, certificados, actas, comunicaciones, pericia técnica preconstituida.
3. **Equipo alternativo** identificado (contratista de reemplazo, recursos propios).
4. **Plan de transición** (qué se hace los primeros 5-10 días tras la toma).
5. **Seguros** chequeados (TRC, caución, RC).

### 8.3 Activación (día 0)
1. **Intimación** formal (CD) con causa + plazo de subsanación.
2. **Vencido el plazo**, comunicación de resolución contractual + toma de obra.
3. **Acta de toma** con escribano: estado físico, inventario de acopio, herramientas, documentación en obra, personal presente.
4. **Cambio de cerraduras / accesos / cartelería**.
5. **Notificación a aseguradoras** (TRC + caución).
6. **Notificación a subcontratistas** y proveedores: nueva contraparte + condiciones.
7. **Comunicación a la municipalidad / inspectores**: cambio de responsable técnico.

### 8.4 Primeros 30 días
- Recontratar a los subcontratistas críticos en relación directa con el comitente.
- Pagar a subcontratistas con deuda razonable y prueba (evita reclamos art 30 LCT).
- Continuar la obra con plan acelerado.
- Iniciar **ejecución de la caución** ante la aseguradora.
- Cuantificar daños y mayores costos para reclamo posterior.

### 8.5 Riesgos del step-in
- **Contratista cuestiona** la resolución y demanda → si la documentación es floja, juicio largo.
- **Subcontratistas** no quieren continuar (lealtad o miedo).
- **Aseguradora resiste** ejecutar la caución sin sentencia → tiempo + costo.
- **Reclamo del contratista** por trabajos pendientes de certificar.
- **Pérdida de garantías** del contratista original sobre los rubros que ya hizo.

### 8.6 Errores típicos en step-in
- Activar sin documentación firme → contraataque legal.
- No tomar acta de inventario el día 0 → se evapora el acopio.
- Demorar la comunicación a subcontratistas → migran o cobran al original.
- No notificar a la aseguradora → caución se complica.
- No tener equipo alternativo listo → la obra se para igual.

---

## 9. Concurso preventivo y quiebra del contratista

### 9.1 Marco (Ley 24.522)
- **Concurso preventivo**: el contratista busca acuerdo con acreedores.
- **Quiebra**: liquidación, designación de síndico, masa indisponible.
- **Efectos sobre contratos en curso**: el síndico decide continuar o resolver (arts 144-159).
- **Pago anticipado** del comitente puede ser **inoponible** si fue dentro del período de sospecha.

### 9.2 Qué hacer el comitente
- **Verificación de crédito**: si el comitente tiene crédito a favor (por sobreprecios, devolución de anticipo, daños), debe insinuarse en el pasivo concursal en plazo.
- **Continuación del contrato**: pedir al síndico la decisión sobre continuación.
- **Acopio**: reclamar al síndico que no integra la masa (con cláusula + actas + cartelería).
- **Caución**: ejecutarla — la aseguradora no es parte del concurso del tomador.
- **Subcontratistas**: continuar con ellos directo, pagando a partir del concurso (los pagos previos quedan en la masa).

### 9.3 Riesgos específicos
- **Inoponibilidad de actos** del período de sospecha (típicamente últimos 6 meses-2 años antes del concurso): pagos anticipados, dación en pago, garantías nuevas pueden ser revisados.
- **Crédito laboral** de subcontratistas tiene preferencia → presión sobre el comitente vía art 30 LCT.
- **Demora** del proceso concursal puede paralizar la obra meses.

### 9.4 Acción inmediata si el contratista cae
1. **Asesor concursalista** (no es lo mismo que laboralista o civilista).
2. **Acta inmediata** del estado de la obra y acopio.
3. **Ejecución caución** ante la aseguradora.
4. **Cambio de relación** con subcontratistas (directa con el comitente).
5. **Verificación de crédito** dentro de plazo (suele ser 30-60 días desde edicto).
6. **Comunicación a inversores / fiduciantes** si aplica.

---

## 10. Auditoría mensual del paquete del contratista (lista operativa)

### 10.1 Avance
- Certificado mensual con medición física firmada.
- Curva S avance físico (no costo) actualizada.
- Foto-registro por sector.
- Listado de pendientes + retrabajos.
- Cumplimiento de hitos contractuales.

### 10.2 Compras y acopio
- Remitos cruzados con facturas.
- Inventario físico del acopio con cartelería.
- Compras anticipadas con respaldo.

### 10.3 Laboral (por subcontratista)
- AFIP F931 + pago.
- ART vigente con nómina específica + tareas.
- IERIC altas/bajas semanales.
- Convenio aplicado (UOCRA u otro según gremio).
- Recibos firmados por cada operario.
- Acta de capacitación S&H del mes.
- Inspección visual: gente en obra = gente declarada.

### 10.4 Subcontratistas (relación financiera)
- Lista de subcontratistas activos + monto vigente.
- Confirmación de cobro reciente al contratista principal (idealmente recibos).
- Telegramas / reclamos pendientes.

### 10.5 Seguros
- TRC vigente con suma asegurada actualizada.
- Caución vigente.
- RC general + RC profesional del director.

### 10.6 Documental
- Libro de órdenes firmado.
- Actas de reunión.
- RFIs y COs con status.
- Plan de obra actualizado.

> Práctica profesional: usar **checklist firmado por dirección de obra + comitente cada mes**. Si falta un item, no se libera el certificado del mes siguiente.

---

## 11. Cómo reaccionar según fase del problema

### 11.1 Verde (señales aisladas, sin impacto)
- Documentar formalmente la observación.
- Pedir explicación escrita al contratista.
- Aumentar cadencia de auditoría (de mensual a quincenal).
- No intimar formalmente todavía.

### 11.2 Amarillo (varias señales en simultáneo o impacto puntual)
- **Intimación formal** (CD) con plazo de subsanación.
- **Reducción del certificado** del mes a lo verificable.
- **Auditoría laboral** intensiva sobre todos los subcontratistas.
- **Reunión** con dueño del contratista + asesor legal + dirección.
- **Plan de contingencia** preparado (contratistas alternativos identificados).
- **Comunicación a inversores / fiduciantes** si la materialidad lo amerita.

### 11.3 Rojo (incumplimiento grave, fraude, concurso, abandono)
- **Activación step-in** según contrato (ver §8).
- **Ejecución de caución**.
- **Toma de acopio** con escribano.
- **Continuación con subcontratistas** directos.
- **Reclamo de daños** + verificación de crédito si concurso/quiebra.
- **Comunicación a stakeholders** y manejo reputacional.

---

## 12. Matriz decisional: señal → acción → asesor

Para uso operativo del jefe de obra / project manager / fiduciante. Cada fila se resuelve en horas o días, no semanas.

| Señal detectada | Materialidad | Acción inmediata | Asesor a involucrar |
|---|---|---|---|
| Demora pago a 1 subcontratista | Aislada, primera vez | Pedir explicación escrita al contratista + monitoreo semanal | Director de obra |
| Demora pago a 2+ subcontratistas o reincidente | Patrón | Intimación CD + retención solidaria del próximo certificado | Legal civil + laboral |
| Telegrama de operario al comitente | Cualquiera | Contestar dentro de 48h hábiles + retención al subcontratista | Laboral (urgente) |
| Avance papel > avance físico | Discrepancia <5% | Acta de medición + reducción del certificado | Director de obra |
| Avance papel > avance físico | Discrepancia >5% o recurrente | Intimación + pericia preconstituida + reducción retenida | Legal civil + perito |
| Acopio fantasma o desaparecido | Cualquiera | Inventario forzado con escribano + acta + foto | Legal civil + escribano |
| Cambio de director técnico del contratista | Sin notificación formal | Nota formal exigiendo notificación + suspender certificación hasta normalizar | Director de obra |
| Maquinaria propia del contratista desaparece | Cualquiera | Acta + pedido explicación + activar plan B identificado | Legal civil |
| Cambio de subcontratista en gremio crítico | 2da vez en mismo gremio | Pre-mapeo de alternativos para relación directa | Director de obra |
| Adelanto extra "puntual" pedido | Cualquiera | Negar sin caución equivalente + escalar conversación | Legal civil |
| Sobreprecio en compra de materiales | Material > 10-15% mercado | Auditoría de compras + retención + pasar compras a directo del comitente | Auditor + comprador propio |
| Accidente de obrero sin denuncia ART | Cualquiera | Auditoría laboral total + denuncia espontánea ART/SRT + acta | Laboral + S&H |
| Abandono físico de obra | 15+ días sin avance + sin justificación | Intimación CD + plazo 10-15 días + step-in según contrato | Legal civil + escribano |
| Concurso preventivo del contratista | Conocido por edicto o información | Step-in inmediato + verificación de crédito + ejecución caución | Concursalista + civil + laboral |
| Quiebra del contratista | Sentencia conocida | Toma de acopio con escribano + ejecución caución + presentación al síndico | Concursalista + civil + laboral + escribano |
| Fraude documentado (doble certificación, factura repetida) | Cualquiera | Suspender pagos + pericia + denuncia formal | Legal civil + penal (eventual) + perito |
| Inspección municipal con observaciones graves | Cualquiera | Acta + comunicación al contratista + plan de subsanación | Director de obra + legal civil |

> **Regla práctica**: si el problema cruza dos columnas (ej. señal de fraude **y** de insolvencia), aplicar la acción de la columna más severa **siempre**. No promediar.

---

## 13. Errores frecuentes del comitente

- **Firmar certificados sin auditar** → en juicio se le opone su propia firma.
- **No retener fondo de reparo** completo.
- **Caución vencida** o sin renovar.
- **Dar anticipos** sin contracaución equivalente.
- **No exigir** documentación laboral mensual de cada subcontratista.
- **No documentar** discrepancias por escrito en tiempo real.
- **Pagar "afuera"** del circuito (efectivo, sin factura) → expone a UIF + AFIP + pierde prueba.
- **Hacer la vista gorda** ante señales tempranas porque "ya estamos lejos".
- **Cambiar al director de obra** que detecta el problema (síntoma de captura del comitente).
- **No tener plan B** de contratista alternativo identificado.
- **Activar step-in sin documentación** → contraataque legal y juicio largo.
- **Negociar con la aseguradora de caución** sin asesor → suelen demorar / negar ejecución.

---

## 14. Preguntas clave que el comitente debe contestar siempre

- ¿Sé exactamente cuánto avance físico hay vs cuánto certifiqué?
- ¿Los subcontratistas críticos están cobrando del contratista principal?
- ¿La caución está vigente y la suma cubre el saldo de obra?
- ¿Mi cláusula de step-in es activable hoy sin discusión?
- ¿Tengo inventario reciente del acopio con cartelería identificando propiedad?
- ¿La nómina visible en obra coincide con la declarada en IERIC y ART?
- ¿Tengo plan B de contratista alternativo o equipo propio?
- ¿Quién me asesora si esto escala (legal civil + laboral + concursal + perito)?

---

## 15. Cuándo escalar a asesores

### 15.1 Legal civil / comercial
- Cuando hay intimación formal o resolución contractual.
- Cuando se activa step-in.
- Cuando hay reclamo de daños cuantificable.

### 15.2 Laboral
- Cuando llega telegrama de operario.
- Cuando hay accidente sin denuncia del subcontratista.
- Cuando hay reclamo art 30 LCT pendiente o probable.

### 15.3 Concursalista
- Apenas se conoce concurso preventivo o quiebra del contratista.
- Para verificación de crédito y reclamo de acopio.

### 15.4 Técnico / pericial
- Para pericia preconstituida en momentos críticos.
- Para cuantificar daños (mayores costos, retrabajos).
- Para defender la posición del comitente en juicio.

### 15.5 Aseguradora
- Notificación inmediata ante cualquier evento de caución o TRC.
- Coordinación con su área de siniestros.

---

## 16. Resumen ejecutivo accionable

1. **Auditá** cada certificado contra avance físico real, sin excepción.
2. **Retené** fondo de reparo siempre.
3. **Verificá caución** vigente todos los meses.
4. **Mapeá subcontratistas** y su estado de cobro mes a mes.
5. **Documentá** todo formalmente (libro + actas + CDs + fotos).
6. **Acopio identificado** con cartelería + actas + transferencia contractual al ingreso.
7. **Step-in habilitado** en contrato con procedimiento explícito.
8. **Plan B** de contratista o administración propia siempre listo.
9. **Asesor legal + laboral + concursal** disponibles en pre-listo.
10. **Activá** apenas haya 2+ señales en simultáneo, no esperes la "señal definitiva".

---

## 17. Caso especial: cuando el comitente es un fideicomiso al costo

Cuando el desarrollo se gestiona vía fideicomiso al costo, el "comitente" formal del contrato de obra es el **fiduciario**, mientras que los **fiduciantes-beneficiarios** son los comitentes económicos. Esta separación genera patologías específicas que no aparecen en obra con dueño directo.

### 17.1 Configuración típica y conflicto de interés
- El constructor puede ser **el propio fiduciario** (doble rol).
- Una **sociedad vinculada** al fiduciario (mismo grupo económico).
- Un **tercero** contratado por el fiduciario sin licitación documentada.
- En los dos primeros casos: **el fiduciario se autocertifica** → conflicto de interés estructural.

### 17.2 Riesgos específicos en este escenario
- **Asimetría informativa**: los fiduciantes no acceden a la auditoría operativa que sí tendría un dueño directo.
- **Caja única del fiduciario** gestionando múltiples proyectos → riesgo de mezcla y de aportes "prestados" entre obras.
- **Comisión fiduciaria atada al costo de obra**: si hay sobrecosto, la comisión sube → incentivo invertido.
- **Step-in inoperable** desde la perspectiva del fiduciante: contractualmente quien firmó el contrato de obra es el fiduciario, no los fiduciantes.
- **Compras dirigidas a partes vinculadas** sin licitación → sobreprecios trasladados al costo del fideicomiso (que pagan los fiduciantes).

### 17.3 Señales adicionales propias del escenario fiduciario
- Fiduciario evita o demora la convocatoria a asamblea de fiduciantes.
- Cambios de auditor externo o ausencia de auditoría real.
- Rendiciones de cuentas demoradas o agregadas sin desagregar por proyecto.
- Designación de proveedores sin proceso de selección documentado.
- Concentración de pagos significativos a sociedades del grupo del fiduciario.
- Resistencia a entregar respaldo de compras a fiduciantes que lo piden.

### 17.4 Defensa práctica del fiduciante
- **Auditoría externa independiente** prevista en el contrato de fideicomiso, designada por mayoría no controlada por el fiduciario.
- **Comité de control** de fiduciantes con poder de exigir documentación y acceder a obra.
- **Prohibición contractual** de contratar partes vinculadas sin asamblea con mayoría calificada.
- **Mecanismo de reemplazo del fiduciario** sin necesidad de judicialización ante mala gestión documentada (cláusula explícita con causales objetivas).
- **Step-in indirecto**: los fiduciantes gatillan reemplazo del fiduciario, y el fiduciario entrante activa step-in contra el constructor.
- **Cláusula de open book** sobre compras y subcontratos críticos.

### 17.5 Si el fiduciario es el constructor (o lo es una vinculada)
- Exigir contractualmente **dirección de obra independiente** del fiduciario.
- **Comisión fiduciaria fija** (no % del costo), o con tope y ajuste por inflación, no por crecimiento del presupuesto.
- **Auditoría obligatoria de compras y subcontratos** trimestral.
- Si las señales del §2 se detectan, activar la matriz del §12 **vía el reemplazo del fiduciario**, no contra el "constructor" (que es el mismo).

> Ver `../04-impuestos/estructuras-fiscales/fideicomiso-al-costo.md` y `../10-estrategia/gestion-riesgos.md`. El tema completo de patología del fiduciario tendrá archivo propio en próxima iteración de capa experta.

---

## 18. Jurisprudencia AR aplicada (líneas consolidadas)

Lo siguiente son **líneas jurisprudenciales consolidadas** que orientan la práctica, no fallos puntuales para citar en escrito. Cualquier acción legal requiere validación con fallos actualizados de la jurisdicción.

### 18.1 Solidaridad del comitente (art 30 LCT)
- **CSJN "Rodríguez c/ Cía. Embotelladora Argentina" (1993)**: línea original que restringía la solidaridad a actividad "normal y específica".
- **CSJN "Benítez c/ Plataforma Cero" (2009)** y jurisprudencia laboral posterior: la doctrina se amplió, considerando la subcontratación de tareas integrantes del ciclo productivo del comitente.
- **Práctica actual en construcción privada**: los tribunales laborales suelen extender la solidaridad al desarrollador / comitente cuando el constructor subcontrata gremios y no paga aportes / salarios. La auditoría documentada del comitente y las retenciones efectivas reducen pero no siempre eliminan la responsabilidad.
- **Implicancia operativa**: documentar la auditoría laboral mensual (§10.3) es la mejor defensa probatoria.

### 18.2 Vicios redhibitorios (arts 1051-1059 CCyCN)
- **Prescripción de la acción**: 1 año desde la **manifestación del vicio**, no desde la entrega (art 2564 CCyCN).
- **Caducidad de la garantía**: 3 años para inmuebles desde la recepción (art 1055).
- **Habitualista / desarrollador**: no puede excluir contractualmente la responsabilidad por vicios redhibitorios cuando vende a consumidor (art 1056 CCyCN + art 11 Ley 24.240).
- **Implicancia**: cláusulas que pretenden limitar garantía de vicios frente a consumidor se tienen por no escritas (art 37 LDC).

### 18.3 Ruina total o parcial (art 1273 CCyCN)
- **Plazo de la acción**: 10 años desde la recepción de obra.
- **Solidaridad pasiva**: constructor + director de obra + proyectista cuando hay vicios en sus respectivos ámbitos (art 1274).
- **No puede excluirse contractualmente** frente a consumidor.
- **Implicancia operativa**: archivar documentación de obra completa al menos 10 años post-recepción; mantener póliza de RC profesional vigente del director y proyectista por igual plazo.

### 18.4 Resolución contractual y pacto comisorio (arts 1083-1090 CCyCN)
- **Pacto comisorio implícito** (art 1086): existe en toda obligación contractual, salvo pacto en contrario.
- **Procedimiento estándar**: interpelación + plazo razonable de subsanación + comunicación fehaciente de resolución por incumplimiento.
- **Pacto comisorio expreso**: si el contrato lo prevé con causales claras, la resolución opera por la sola declaración con causa documentada.
- **Práctica de tribunales**: descalifican resoluciones precipitadas sin plazo razonable o sin documentación de incumplimiento → recae responsabilidad sobre quien resolvió.
- **Implicancia**: nunca activar step-in sin CD previo + plazo + documentación + escribano para la toma.

### 18.5 Certificados de obra y carga probatoria
- **Doctrina mayoritaria comercial / civil**: el certificado firmado por el comitente implica reconocimiento del avance allí declarado, **salvo prueba** de error, dolo o fraude.
- **Carga probatoria**: revertir un certificado firmado requiere prueba contundente (pericia técnica independiente + comparativa documental + fotografías + testigos).
- **Práctica preventiva**: nunca firmar con "reserva mental" — documentar la observación en el acta de medición y certificar solo el monto verificable. La firma con reserva escrita es defendible; la firma simple no.

### 18.6 Concurso preventivo y quiebra (Ley 24.522)
- **Período de sospecha** (arts 116-119): los actos del contratista en los meses previos al concurso (anticipos extraordinarios, daciones en pago, garantías nuevas a favor del comitente) pueden ser declarados **inoponibles** al concurso.
- **Verificación de crédito**: el comitente con crédito a favor debe insinuarse en plazo legal desde el edicto (típicamente 30-60 días, según el caso).
- **Contratos en curso** (arts 144-159): el síndico decide continuación o resolución dentro del plazo legal.
- **Acopio del comitente**: documentado como propiedad del comitente con cláusula contractual + actas + cartelería, **no integra la masa** (separación patrimonial).
- **Implicancia operativa**: la cláusula de transferencia de propiedad del acopio al ingreso a obra (§5.2, §7.3) es la defensa más sólida ante quiebra.

### 18.7 Defensa del consumidor aplicada
- Ley 24.240 + arts 1092-1122 CCyCN: el adquirente de unidad en pozo es **consumidor**.
- Publicidad (folletos, renders, web) **integra el contrato** (art 8 LDC).
- **Cláusulas abusivas** (art 37 LDC + art 988 CCyCN): se tienen por no escritas. Lista no taxativa incluye exoneración de responsabilidad, limitación de daños, jurisdicción exclusiva del vendedor.
- **Implicancia para el constructor / desarrollador**: el riesgo de reclamos por vicios post-entrega es **mayor** que en obra B2B; la documentación de obra y los seguros de garantía son inversiones defensivas.

> Para profundización por tema, ver archivos específicos planeados en próxima iteración: `legal-vicios-y-ruina-aplicado.md`, `legal-defensa-consumidor-aplicada-re.md`, `legal-jurisprudencia-clave-re.md`.

---

## 19. Reglas operativas para el chat

- **Estable y respondible:** señales tempranas, taxonomía de patologías, cláusulas contractuales preventivas, workflow de step-in, marco art 30 LCT y Ley 24.522 (referencial), checklist de auditoría mensual, errores frecuentes, matriz decisional, líneas jurisprudenciales consolidadas, caso especial fideicomiso al costo.
- **🔴 Volátil:** plazos procesales específicos (varían por jurisdicción y reforma), montos de cauciones / fondos (negociables), prácticas locales en cada provincia (uso de IERIC, ART, escribanos), fallos puntuales y su evolución, regulación CNV/UIF sobre PSAV cuando aplica al fideicomiso.
- **Marco legal citado**: arts 1051-1059, 1083, 1086, 1251-1279, 1273, 1274 CCyCN; art 30 LCT; Ley 24.522 (arts 116-119, 138, 144-159); Ley 24.240 (arts 8, 11, 37); Decreto 911/96. Cualquier acción legal requiere validación con asesor de la jurisdicción.

---

## 20. Anexo A — Plantilla de acta de toma de obra (día 0 step-in)

> Modelo de uso operativo. **Adaptar al caso y validar con asesor legal y escribano antes de usar**. La intervención de escribano público es clave para fecha cierta y oponibilidad procesal posterior.

```
ACTA DE TOMA DE OBRA — PARALIZACIÓN / STEP-IN

Lugar: [CABA / municipio]
Fecha y hora: [dd/mm/aaaa] — [hh:mm]
Obra: [denominación + dirección + nomenclatura catastral + matrícula RPI]
Comitente: [razón social + CUIT + domicilio + representante legal con DNI]
Contratista saliente: [razón social + CUIT + representante]
Director de obra: [nombre + matrícula + colegio profesional]
Escribano interviniente: [nombre + registro + matrícula + foja]
Testigos: [nombres + DNI, si corresponde]

ANTECEDENTES
1. Contrato de obra de fecha [dd/mm/aaaa] entre [Comitente] y [Contratista], obrante en
   [registro/escribanía/instrumento privado con fecha cierta].
2. Intimación cursada por carta documento N° [XX] de fecha [dd/mm/aaaa] por causal
   [abandono / mora calificada / fraude / incumplimiento grave / concurso o quiebra].
3. Vencimiento del plazo de subsanación el [dd/mm/aaaa] sin respuesta o sin subsanación
   suficiente, conforme se documenta.
4. Comunicación de resolución contractual por carta documento N° [XX] de fecha [dd/mm/aaaa]
   con apoyo en cláusula [X] del contrato y arts 1083 / 1086 CCyCN.

ESTADO FÍSICO DE LA OBRA AL MOMENTO DE LA TOMA
- Avance físico estimado por dirección de obra: [XX%] (descripción por rubro en Anexo I).
- Personal presente al momento de la toma: [lista nominal con DNI y empleador] — Anexo II.
- Maquinaria y herramientas en obra: [descripción + n° de serie + propiedad declarada] — Anexo III.
- Materiales en acopio: [inventario detallado con foto-registro y cartelería] — Anexo IV.
- Documentación encontrada en obra: libro de órdenes, planos, RFIs, ATR, planes de inspección
  y ensayo, certificados pendientes, partes diarios — Anexo V.
- Subcontratistas con presencia en obra: [lista con razón social, CUIT y rubro] — Anexo VI.

OBSERVACIONES TÉCNICAS Y DE SEGURIDAD
- Estado de seguridad e higiene (Dec. 911/96): [OK / observaciones puntuales].
- Riesgos inmediatos detectados: [descripción + medidas adoptadas].
- Estado de instalaciones provisorias (energía, agua, sanitarios, vallado): [descripción].

ACCIONES EJECUTADAS EN EL ACTO
- Cambio de cerraduras y accesos.
- Colocación de cartelería identificando nueva dirección y propiedad del acopio.
- Notificación a aseguradoras: [TRC póliza N° XX, Caución póliza N° XX].
- Notificación a subcontratistas presentes: nueva contraparte y condiciones de continuidad.
- Notificación a la municipalidad / inspectores: cambio de responsable técnico.
- Notificación al/los asesor/es legal/es: [legal civil, laboral, concursal según corresponda].

RESERVAS Y DECLARACIONES DEL COMITENTE
- El Comitente se reserva los derechos a reclamar daños por todo concepto: mayores costos,
  retrabajos, lucro cesante, gastos improductivos, intereses, daño moral si correspondiere.
- El Comitente declara que el acopio descripto en Anexo IV es de su exclusiva propiedad
  conforme cláusula [X] del contrato de obra y documentación de respaldo que se acompaña
  (Anexo VII — remitos, facturas, actas de ingreso firmadas).
- Se intimará a la aseguradora [razón social] a la ejecución de la caución N° [X] por la
  suma de [$ XXX], con notificación cursada en este acto.
- En caso de oposición del Contratista saliente, el Comitente se reserva el derecho de
  promover las acciones civiles, comerciales y/o penales que correspondan.

FIRMAS
- Por el Comitente: [firma + aclaración + DNI + cargo].
- Director de obra: [firma + matrícula].
- Escribano público: [firma + sello + foja del libro de protocolo].
- Por el Contratista saliente: [firma o constancia de notificación cursada / negativa a firmar].
- Testigos: [firmas + DNI, si corresponde].

ANEXOS
I    — Avance físico por rubro al día de la toma.
II   — Lista nominal de personal presente.
III  — Maquinaria y herramientas inventariadas.
IV   — Inventario de acopio con foto-registro y cartelería.
V    — Documentación de obra encontrada.
VI   — Subcontratistas activos.
VII  — Respaldo de propiedad del acopio (remitos, facturas, actas de ingreso).
VIII — Foto-registro general (con sello de fecha y hora).
IX   — Comunicaciones previas: contrato, addendas, CDs, mails, actas anteriores.
```

> **Práctica profesional**: el día de la toma debe ser pre-coordinado por el comitente con su asesor legal, escribano, director de obra y equipo alternativo de continuidad. Improvisar el día 0 es la causa principal de step-ins judicializados.

---

**Ver también:**
- `./modalidades-contratacion.md`
- `./change-orders-claims.md`
- `./certificacion-obra.md`
- `./documentacion-obra.md`
- `./gestion-subcontratistas.md`
- `./compras-proveedores.md`
- `./logistica-acopio.md`
- `./garantias-vicios-ruina.md`
- `../03-laboral/solidaridad-art-30.md`
- `../03-laboral/ieric.md`
- `../03-laboral/art-srt.md`
- `../18-seguros/caucion-y-garantias.md`
- `../18-seguros/trc-construccion.md`
- `../02-normativa/ccyc-real-estate.md`
- `../10-estrategia/gestion-riesgos.md`
