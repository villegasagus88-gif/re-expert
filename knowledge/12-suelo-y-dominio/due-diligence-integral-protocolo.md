---
title: "Due diligence integral pre-compra — protocolo aplicado del experto"
topic: "suelo-dominio"
subtopic: "due-diligence-protocolo"
jurisdiction: "Argentina"
last_verified: "2026-05-12"
sources:
  - "CCyCN — arts. 392, 396, 1009, 1010, 1017, 1051-1059, 1138, 1184, 1273-1279, 1882, 1893, 1902-1905, 1969, 1970, 2564, 2565"
  - "Ley 17.801 — Registro de la Propiedad Inmueble (arts. 22-27 certificados, 23 reserva de prioridad)"
  - "Ley 22.427 — Certificado libre deuda municipal"
  - "Ley 24.522 — Concursos y quiebras (arts. 116-119 período de sospecha)"
  - "Ley 25.246 + Resol. UIF 21/2011, 28/2018, 156/2018 — sujeto obligado escribano/inmobiliaria"
  - "Ley 23.928 + Decreto 70/2023 — libertad pacto moneda"
  - "Ley 26.737 — Tierras rurales"
  - "Ley 24.374 — Regularización dominial (ojo títulos)"
  - "Códigos de Planeamiento Urbano CABA / PBA / provincias"
  - "Ley 25.675 General del Ambiente + leyes provinciales"
  - "Práctica profesional: escribanías, estudios RE, fondos institucionales"
keywords: [due diligence integral, dd integral, dd pre compra, protocolo dd, dd inmueble, comprar inmueble checklist, comprar terreno checklist, riesgos compra, red flags compra, condiciones suspensivas boleto, escrow, contingencias, certificado dominio, certificado catastral, certificado libre deuda, libre deuda municipal, libre deuda arba, libre deuda agip, deuda expensas, inhibiciones, ihi, certificado uif, dd uif, sujeto obligado, sucesion vendedor, condominio vendedor, fideicomiso vendedor, sociedad vendedora, poder vigente, ph reglamento copropiedad, club de campo barrio cerrado dd, dd ambiental, ema pasivo ambiental, dd urbanistica, fot fos zonificacion, plano aprobado, conforme obra, vicios ocultos compra, articulo 1051 ccycn, articulo 1273, ruina vendedor, prescripcion adquisitiva ocupante, prescripcion 20 anos, accion reivindicatoria, evicción, art 1044, art 1051, boleto con seña, retractacion seña, arras confirmatorias, arras penitenciales, escritura traslativa, prioridad registral, 60 dias reserva, expensas extraordinarias, deuda consorcial, certificado abl, certificado obras sanitarias, certificado aysa, edenor edesur edenor sa, gas natural ban, ocupantes precarios, intrusos, comodato verbal, locatario vigente, contrato locacion vigente, plano municipal, plano catastral, dimensiones reales vs titulo, diferencia superficie, sobre o sub edificacion, antecedentes 20 anos]
audience: ["desarrollador", "inversor", "abogado RE", "escribano", "broker", "comprador profesional", "fund manager", "chat"]
confidence: "alta"
---

# Due diligence integral pre-compra — protocolo aplicado

## TL;DR
- DD integral = el protocolo que evita comprar un problema. No es "pedir el informe de dominio". Son **9 capas cruzadas** ejecutadas en orden, con **gates** y condiciones suspensivas en el boleto.
- **Regla de oro:** ninguna seña sin **dominio + libre deuda municipal/provincial + capacidad vendedor + zonificación verificada** confirmados.
- Lo que destruye capital no es la falta de DD: es la DD **incompleta y fuera de orden**. El 80% de los problemas se detectan en las primeras 72 hs si se ejecuta bien.
- Toda DD termina en un **informe** con semáforo verde/amarillo/rojo y **lista de contingencias** que entran como cláusulas del boleto.
- Complementa a `./due-diligence-dominial.md` (capas básicas) con el **protocolo operativo, red flags, errores y plantillas**.

---

## 1. Qué es y qué NO es una DD integral

### 1.1 Es
- Verificación cruzada de **9 capas**: dominial · gravámenes · personas · urbanística · fiscal · técnica · ambiental · contractual · ocupacional.
- Documento **escrito**, firmado por responsable, con conclusiones y semáforo.
- Base para redactar **cláusulas del boleto** (condiciones suspensivas, declaraciones y garantías del vendedor).
- Insumo para **pricing** (descontar contingencias o exigir hold-back).

### 1.2 No es
- Solo el informe de dominio del escribano (eso es 1 de 9 capas).
- Una visita al inmueble + "lo veo limpio".
- Confiar en la "DD que ya hizo el banco" o "que ya hizo el otro comprador caído".
- Algo que se hace después de firmar boleto (entonces ya es tarde: la seña está dada).

### 1.3 Quién la firma
- **Dominial/legal**: escribano + abogado RE (proyectos complejos).
- **Urbanística**: arquitecto matriculado o agrimensor.
- **Técnica/constructiva**: ingeniero estructural + MEP si hay edificio.
- **Fiscal**: contador (esp. si vendedor es sociedad o fideicomiso).
- **Ambiental**: consultor ambiental si terreno con uso previo industrial/agro/depósito.
- **Coordinación**: developer / inversor / abogado líder.

> Práctica profesional: una sola persona "que sabe de todo" es señal de DD pobre. Cada capa tiene su matriculado.

---

## 2. Producto y profundidad — adaptar la DD

### 2.1 Matriz producto × profundidad

| Producto | Dominial | Urbanística | Técnica | Ambiental | Fiscal | Ocupacional |
|---|---|---|---|---|---|---|
| Terreno urbano vacante | Profunda | Profunda | Estudio suelo | Si uso previo riesgoso | Estándar | Verificar intrusos |
| Terreno rural | Profunda + Ley 26.737 | Aptitud y servicios | Geotécnico | Profunda | Profunda | Mediería/arriendos |
| Inmueble usado | Estándar | Verificar conforme obra | Inspección estructural | Estándar | Expensas + deudas | Locatario/ocupante |
| PH / depto | Estándar | Reglamento copropiedad | Estado consorcio | N/A salvo afectación | Expensas extraordinarias | Locatario |
| Inmueble en obra | Profunda | Permisos vigentes | Avance real + planos | Si ZPI o RAMQS | Profunda fideicomiso | N/A |
| Inmueble en sucesión | Profunda + posesión hereditaria | Estándar | Estándar | Estándar | Bienes personales/imp suc | Heredero ocupante |
| Inmueble vendido por SA/SRL | Profunda + DD societaria | Estándar | Estándar | Estándar | Profunda IIBB/gan | Estándar |
| Inmueble fideicomitido | Profunda + fideicomiso | Estándar | Estándar | Estándar | Profunda fiduciario | Estándar |

### 2.2 Tiempos típicos (calendario, no working days)
- DD básica (residencial usado, vendedor PF, libre): **7-15 días corridos**.
- DD media (terreno, edificio chico, sociedad vendedora): **15-30 días**.
- DD compleja (terreno con pasivo ambiental, sucesión, fideicomiso, edificio en obra): **30-60 días**.
- Si te apuran a saltear tiempos = **red flag**.

---

## 3. Secuencia operativa (orden importa)

### 3.1 Fase 0 — Antes de la oferta (24-48 hs)
- Pedir copia simple del título (no compromete a nada).
- Verificar matrícula en sitio del registro (CABA: rpicaba; PBA: rpba) — al menos titular y observaciones.
- Ubicación → cruzar con catastro y zonificación pública.
- Inspección visual del inmueble (fotos, fachada, linderos, accesos).
- Si algo huele raw acá → ni hacer oferta.

### 3.2 Fase 1 — Oferta y reserva (día 0-7)
- **Reserva con condiciones suspensivas explícitas** (no es seña; es retractable si DD falla).
- Pedir documentación al vendedor: título, planos, libre deudas, conforme obra, expensas si PH.
- Plazo de DD pactado: **15-30 días para validar y decidir**.
- Reserva por **monto bajo** (1-2% del precio), depositada en escrow o escribanía neutral, no en mano del vendedor.

> Red flag: vendedor que se niega a entregar documentación sin firmar primero algo más fuerte. La documentación que pide la DD es la **misma** que va a presentar en escritura — si no la tiene, no puede vender.

### 3.3 Fase 2 — DD ejecución (día 7-25)
- Solicitar **certificados oficiales** (no fotocopias):
  - Dominio + inhibiciones del titular (escribano).
  - Catastral (provincia/CABA).
  - Libre deuda municipal (ABL/tasa/derechos).
  - Libre deuda provincial (ARBA inmobiliario, AGIP, Rentas).
  - Libre deuda servicios (Aysa/OSSE, Edenor/Edesur/EPEC, gas, expensas).
- Cruces:
  - Título vs catastro vs plano vs realidad física.
  - Datos del vendedor: DNI, CUIT, estado civil, sociedad conyugal, capacidad.
  - Si sociedad: estatuto, acta de designación, vigencia poder, balance, acreedores.
- **Informe parcial intermedio** (día 15): se decide seguir / renegociar / abandonar.

### 3.4 Fase 3 — Cierre DD (día 20-28)
- Informe final escrito con semáforo.
- Lista de contingencias → entran como cláusulas del boleto.
- Si todo verde → boleto + seña + escritura programada.
- Si amarillo → renegociar precio o hold-back (retención hasta resolver).
- Si rojo → ejecutar retractación de reserva, recuperar dinero.

### 3.5 Fase 4 — Boleto a escritura (día 28-90)
- Verificación nuevamente entre boleto y escritura (gravámenes nuevos que pueden surgir, art. 1893 CCyCN).
- **Reserva de prioridad registral 60 días** (Ley 17.801 art. 24) — el certificado dominial bloquea el dominio mientras corre.
- Inhibiciones del vendedor: certificado vigente al día de escritura.

---

## 4. Capa DOMINIAL — checklist profesional

### 4.1 Documentación mínima a pedir
- Título de propiedad (escritura completa, no solo primera hoja).
- Estudio de **antecedentes de 20 años** (cadena dominial limpia).
- Informe de dominio actualizado.
- Plano de mensura particular y/o regularización registrado.
- Si rural: croquis + matrícula + nomenclatura catastral.

### 4.2 Red flags dominiales
- Título por **Ley 24.374** (regularización) → revisar si terminó el trámite y si hay anotación efectiva en RPI. Si no, el título es precario.
- Título por **prescripción adquisitiva** reciente → verificar sentencia firme y publicidad.
- **Sucesión sin declaratoria inscripta** → vende un "heredero" sin título perfecto.
- **Donación reciente con donante vivo** → riesgo de acción de reducción de herederos forzosos (art. 2453 CCyCN). Pre 2024: 10 años de saneamiento. Reformas: revisar última versión.
- Cadena con saltos no explicados (transmisiones a sociedades offshore, sucesiones múltiples).
- Diferencias entre **superficie de título** y **superficie de mensura** > 5%: investigar.
- Anotaciones marginales no canceladas.
- **Bien de familia / afectación a vivienda** vigente: requiere desafectación previa.

### 4.3 Validación cruzada
- Título ↔ matrícula RPI ↔ partida catastral ↔ nomenclatura municipal ↔ plano ↔ realidad física.
- Si una falla, no es "detalle administrativo": es problema. Resolver antes de seña.

> Ver `./due-diligence-dominial.md`, `./cesion-de-boleto.md`, `./usucapion.md`.

---

## 5. Capa GRAVÁMENES — checklist profesional

### 5.1 Lista obligatoria a verificar
- Hipoteca (vigente, prescripta, cancelada sin inscribir).
- Embargo (ejecutivo, ejecución hipotecaria, ejecución fiscal).
- Inhibición del titular (anotación personal, RPI distinto al del inmueble).
- Anotación de litis (juicio en curso sobre el inmueble).
- Servidumbres reales (paso, vista, acueducto, electroducto, gasoducto).
- Usufructo / uso / habitación.
- Bien de familia / vivienda afectada.
- Concurso / quiebra del titular (registros provinciales y nacional).
- Medidas cautelares en juicio penal / divorcio / alimentos.

### 5.2 Red flags
- Hipoteca antigua sin cancelación inscripta (años pasaron, acreedor desaparecido) → **acción de cancelación** previa, no comprar "con la hipoteca a saldar después".
- Embargo de monto incierto (juicio en curso) → no se sabe cuánto va a costar liberar.
- Servidumbres no inscriptas pero existentes de hecho (pozo del vecino, paso histórico) → revisar in situ y vecinos.
- Inhibición vigente del cónyuge en sociedad conyugal: bloquea venta.

### 5.3 Cómo se levantan
- Cancelación con cheque diferido / pago en escritura simultánea (estructura común).
- **Escrow notarial** para retener fondos hasta inscripción de cancelación.
- Si no se puede levantar antes de escritura → no se compra, o se asume el gravamen con descuento explícito.

---

## 6. Capa PERSONAS (vendedor) — checklist profesional

### 6.1 Persona física
- DNI vigente, datos completos coinciden con título.
- Estado civil al momento de adquirir el inmueble (sociedad conyugal → cónyuge debe prestar asentimiento, art. 470 CCyCN).
- Capacidad: ¿declarado insano, inhabilitado, restringido?
- Inhibición personal vigente.
- Domicilio real.
- Concurso o quiebra personal: art. 116-119 Ley 24.522 (período de sospecha → actos pueden ser revocados).

### 6.2 Sucesión
- Declaratoria de herederos **inscripta en RPI**.
- Posesión hereditaria activada.
- Aceptación de herencia (no rechazo, no aceptación con beneficio que limite).
- Si no todos los herederos firman: **no se puede vender** (condominio hereditario).
- Heredero menor: requiere autorización judicial.
- Cesión de derechos hereditarios previa: inscripta + tracto.

### 6.3 Sociedad (SA, SRL, SAS)
- Estatuto vigente + última asamblea / acta de directorio.
- Acta que autoriza la venta (en SA: directorio si está autorizado, asamblea si no; en SRL/SAS: socios).
- Poder del firmante vigente y suficiente (especial o general con facultad).
- Vigencia societaria (no disuelta, no en quiebra).
- Balance al cierre + IVA/IIBB/gan al día.
- **Operación inhabitual**: venta del único activo de la sociedad → cuidado con UIF y con representación.

### 6.4 Fideicomiso vendedor
- Contrato de fideicomiso completo (no solo síntesis).
- Identidad y vigencia del fiduciario.
- Facultad expresa del fiduciario para vender (art. 1688 CCyCN).
- Beneficiarios y fideicomisarios identificados.
- CUIT del fideicomiso vigente, deudas fiscales del fideicomiso.
- **Práctica profesional**: pedir actas o instrucciones de fiduciantes si el contrato lo exige para enajenar.

### 6.5 Red flags personas
- Vendedor representado por poder amplio sin relación clara con titular.
- Vendedor extranjero sin domicilio fiscal AR (afecta retención).
- Vendedor con cambios de estado civil recientes y no inscriptos.
- Heredero "haciendo vender" sin haber inscripto declaratoria.
- Cónyuge no firmante con conflicto familiar conocido.
- Apuro inusual del vendedor en cerrar (puede ocultar inhibición inminente).

### 6.6 DD UIF (Resol. 21/2011 y modif.)
- Escribano y broker son **sujetos obligados**.
- Identificación de PEPs, origen de fondos, monto operación.
- ROS si supera umbrales o presenta inconsistencias.
- No es "papelerío": una operación reportada complica al comprador para reventas futuras.

> Ver `../02-normativa/uif-prevencion-lavado.md` si existe.

---

## 7. Capa URBANÍSTICA — checklist profesional

### 7.1 Documentación
- Zonificación oficial (código de planeamiento, plan urbano, ordenanza).
- FOT, FOS, alturas, retiros, perfil edilicio.
- Restricciones especiales (área protegida, APH, distritos de protección).
- Plano municipal / aprobado del inmueble construido.
- Conforme final de obra (CFO) o equivalente provincial.
- Habilitación comercial / industrial si aplica.
- Servicios disponibles: agua, cloaca, gas, electricidad, telecomunicaciones.

### 7.2 Red flags urbanísticos
- Zonificación **en proceso de cambio** (consulta pública abierta) → futuro distinto al presente.
- **Construcción sin permiso** ("clandestino") con riesgo de demolición o multa.
- Conforme final ausente → habitación de hecho, pero no de derecho. No financiable.
- Diferencia entre **plano municipal** y **realidad construida** (ampliaciones no declaradas).
- Indicadores en el límite (FOT al 100%, altura máxima alcanzada) → no permite ampliar, no permite el proyecto pensado.
- Servidumbre administrativa no relevada (línea de transporte eléctrico, ducto de gas).
- Inmueble en **traza de obra pública prevista** (ensanche, autovía, expropiación).
- Si rural: ¿zona urbanizable según plan provincial? ¿hay restricciones de subdivisión mínima?

### 7.3 Validación
- Consulta de zonificación municipal: oficial, por escrito.
- Plano municipal vs realidad: medición in situ por arquitecto/agrimensor.
- Visado del Colegio profesional cuando aplique.

> Ver `../00-fundamentos/zonificacion-fot-fos.md`, `./compra-terreno-due-diligence.md` (cuando exista).

---

## 8. Capa FISCAL — checklist profesional

### 8.1 Deudas asociadas al inmueble (siguen al inmueble)
- **Tasa municipal / ABL** (CABA / municipios PBA y otras provincias).
- **Inmobiliario provincial** (ARBA en PBA, AGIP en CABA, equivalentes en provincias).
- **Servicios sanitarios** (AySA, OSSE, EPAS, etc.).
- **Electricidad / gas / cloaca** si hay deuda registrada del inmueble.
- **Expensas comunes y extraordinarias** si PH/country/barrio cerrado.

### 8.2 Impuestos a cargo del **vendedor** (no del comprador) pero impactan operación
- **Ganancias**: PF no habitualista exento si vivienda única (régimen anterior); revisar.
- **ITI** (impuesto a la transferencia de inmuebles) si aplica (régimen aplicable al momento de la operación).
- **Bienes personales** del vendedor.
- **IVA**: si vendedor es sujeto IVA (constructor, desarrollador), parte del precio puede tener IVA discriminado.
- **Sellos** (provincial): generalmente 50/50 vendedor/comprador, depende jurisdicción y costumbre.
- **IIBB** del vendedor si habitualista.

### 8.3 Red flags fiscales
- Deudas históricas de ABL con multas y intereses superiores al precio: caso real, no chiste.
- Vendedor "monotributista" que en realidad es habitualista RE → la AFIP puede recategorizar y reclamar.
- Fideicomiso al costo donde el fiduciario nunca pagó IIBB de la venta de unidades anteriores → riesgo de embargo provincial.
- Operación pactada en USD pero declarada en escritura por monto menor: riesgo del comprador (defraudación fiscal, base imponible futura, dificultades de blanqueo).

### 8.4 Práctica profesional
- Pedir **certificados de libre deuda con vigencia mínima 30 días** al cierre.
- En boleto: cláusula de deuda hasta fecha de posesión a cargo del vendedor, con retención si hay duda.
- Verificar AGIP/ARBA online con CUIT del inmueble (nomenclatura).

> Ver `../04-impuestos/`.

---

## 9. Capa TÉCNICA — checklist profesional

### 9.1 Terreno
- Estudio geotécnico (mínimo 2 sondeos para terreno mediano, más para edificio en altura).
- Cota IGN, riesgo hídrico (mapa de inundación municipal/provincial).
- Suelos contaminados (uso previo).
- Existencia de napa freática alta.
- Vegetación protegida (árboles añosos, especies nativas).

### 9.2 Inmueble construido
- Inspección estructural visual + (si valor alto) sondeo + ensayos.
- Estado de cubierta, fachadas, humedades.
- Instalaciones (eléctrica reglamentaria, gas habilitado, sanitaria operativa).
- Antigüedad: > 30 años → revisar columnas de hormigón, losas, aluminio antiguo.
- Si edificio: estado consorcio (fondos, expensas extraordinarias votadas, juicios contra consorcio).

### 9.3 Red flags técnicos
- Grietas estructurales en columnas, vigas, losas (no fisuras superficiales).
- Humedad de cimientos / capilaridad → costo de reparación alto.
- Aluminosis u hormigones de mala calidad de los 60-70.
- Instalación de gas no certificada (cierre por seguridad).
- Tanque de agua / cloaca compartidos no regulados.
- Edificio con orden de obra municipal pendiente de cumplir.
- Construcción excede plano municipal (sobre-edificación).

### 9.4 Práctica profesional
- En edificio en obra: ver `./../05-construccion/patologia-constructor-en-problemas.md` para señales.
- En usado de alto valor: inspección técnica con informe escrito antes de seña.
- Si vendedor no permite inspección técnica = red flag mayor.

---

## 10. Capa AMBIENTAL — checklist profesional

### 10.1 Cuándo es crítica
- Terreno con uso previo **industrial, depósito, taller, estación de servicio, agro intensivo, frigorífico, curtiembre, textil con tintura**.
- Terreno lindero a fuente de contaminación (relleno, basural, industria).
- Cercanía a cursos de agua / humedales.
- Áreas con normativa especial (RAMQS, ZPI, área protegida, reserva).

### 10.2 Documentación
- **Fase I ambiental** (relevamiento documental + visita): mínimo para terreno con uso previo riesgoso.
- **Fase II** (muestreo suelo y agua) si Fase I detecta indicios.
- Certificado de aptitud ambiental (CAA) si municipio lo exige.
- Habilitaciones ambientales previas del inmueble (si industrial).
- DIA / EIA si proyecto futuro requiere.

### 10.3 Red flags ambientales
- Vendedor que no informa uso previo industrial.
- Tanques enterrados de combustible no removidos / no certificados.
- Pisos de hormigón sobre terreno con manchas oscuras.
- Olores persistentes inexplicables.
- Vegetación que muere en sectores específicos.
- Pozos absorbentes sin clausurar.
- Lindero conocido con pasivo ambiental (estaciones de servicio cerradas, ex-depósitos).

### 10.4 Responsabilidad
- **Ley 25.675 art. 27-30**: el dañador es responsable. Pero el **propietario actual** puede ser obligado a remediar y luego repetir (art. 28).
- **Si el pasivo se descubre después de comprar**: garantía por vicios ocultos contra el vendedor (CCyCN arts. 1051 ss.), pero el plazo de **1 año desde manifestación** + acción contra Estado y vecinos.
- **Práctica profesional**: cláusula de **declaraciones y garantías ambientales** del vendedor + hold-back ambiental específico (5-10% precio retenido 12-24 meses).

> Ver `../09-triple-impacto/` si existen archivos ambientales específicos.

---

## 11. Capa CONTRACTUAL / LEGAL — checklist profesional

### 11.1 Validar
- Moneda: USD, ARS, UVA — pactado claramente (libertad post DNU 70/2023).
- Precio: número, forma de pago, ajuste si en moneda con plazo.
- Seña: arras confirmatorias (art. 1059 CCyCN — no retractable) vs penitenciales (retractable con pérdida).
- Plazo de escrituración: máximo razonable (60-120 días).
- Posesión: ¿al boleto, al pago total, a la escritura?
- Cláusulas de evicción y vicios ocultos (no se pueden renunciar abusivamente).
- Condiciones suspensivas (si falla DD, queda sin efecto sin pérdida).
- Pacto comisorio (art. 1083-1086 CCyCN).
- Cargo de gastos y honorarios (escribano del comprador, sellos 50/50 o según jurisdicción).

### 11.2 Red flags contractuales
- Boleto redactado solo por la escribanía del vendedor sin participación del comprador.
- Cláusula de "lo conozco y acepto en su estado" amplia → renuncia a vicios ocultos.
- Seña a "cuenta del precio" pero sin definir si confirmatoria o penitencial → conflicto.
- Plazo de escrituración indefinido o sujeto a "trámites del vendedor".
- Posesión adelantada sin escritura → comprador queda como tenedor frágil.
- Acreedor del vendedor con preferencia (juicio en curso no declarado).

### 11.3 Cláusulas que **siempre** entran (práctica profesional)
- Declaraciones y garantías del vendedor (titularidad, libre de gravámenes, sin juicios, sin deudas, sin pasivo ambiental, datos veraces).
- Indemnidad por contingencias preexistentes.
- Retención (hold-back) si hay deudas que se cancelan después de escritura.
- Condiciones suspensivas (DD, financiación, aprobación municipal, autorización societaria).
- Cláusula penal por demora en escriturar.

---

## 12. Capa OCUPACIONAL — checklist profesional

### 12.1 Tipos de ocupantes
- Locatario con contrato vigente.
- Locatario verbal / informal.
- Comodatario verbal (familiar).
- Heredero ocupante.
- Intruso / usurpador.
- Empleado / casero con vivienda.
- Vecino que usa parte del terreno.

### 12.2 Red flags
- Inmueble "vacío en papel" pero con habitantes adentro (cuidado en visita de inspección).
- Locación informal sin instrumento → desalojo más complejo.
- Ocupación de más de 10 años → riesgo de prescripción adquisitiva del ocupante (art. 1899 CCyCN).
- Posesión continua del vecino sobre porción del terreno (común en rural y suburbano).
- Empleado doméstico con vivienda → relación laboral con derechos.

### 12.3 Práctica profesional
- Inspección **con acceso al interior**, no solo visual exterior.
- Acta notarial de constatación de ocupantes antes de boleto.
- Cláusula de entrega libre de ocupantes a la escritura, con penalidad.
- Si hay locatario: lectura del contrato vigente, fecha de vencimiento, derecho del comprador a continuarlo o no.

---

## 13. Red flags transversales (señales que cruzan capas)

| Señal | Capa | Severidad | Acción |
|---|---|---|---|
| Vendedor apura el cierre sin razón | Personas + contractual | 🔴 | Pausa DD, profundizar inhibiciones y juicios |
| Precio muy por debajo de mercado | Transversal | 🔴 | Buscar el motivo oculto antes de avanzar |
| Documentación incompleta o "se entrega después" | Dominial + urbanística | 🟠 | Suspender hasta tener todo |
| Pago en efectivo en USD sin pasar por banco | Personas + fiscal | 🔴 | UIF, defraudación, riesgo penal |
| Vendedor representado por poder amplio | Personas | 🟠 | Verificar vigencia, alcance, motivo |
| Vendedor sociedad con balance no presentado | Personas + fiscal | 🟠 | Pedir auditoría reciente |
| Inmueble con conformes pero sin habilitación | Urbanística | 🟠 | Costo de regularización |
| Pasivo ambiental probable (uso previo) | Ambiental | 🔴 | Fase I obligatoria antes de seña |
| Servidumbre no inscripta pero visible | Gravámenes | 🟠 | Regularizar antes o descontar |
| Diferencia superficie título vs catastro > 5% | Dominial | 🟠 | Mensura aclaratoria |
| Sucesión sin inscripción de declaratoria | Personas | 🔴 | No avanzar hasta inscripción |
| Cónyuge no firmante en sociedad conyugal | Personas | 🔴 | Asentimiento art. 470 CCyCN obligatorio |
| Vendedor con inhibición vigente en otra jurisdicción | Personas | 🔴 | Operación nula si no se levanta |
| Ocupante distinto a vendedor sin explicación | Ocupacional | 🟠 | Investigar tipo y derecho |
| Hipoteca antigua sin cancelar | Gravámenes | 🟠 | Cancelación previa a escritura |
| Boleto firmado pero no inscripto en prehorizontalidad (proyecto) | Contractual | 🔴 | Riesgo de cesión posterior y conflicto |
| Operación que toca PEP o monto alto | Personas | 🟠 | DD UIF reforzada |

---

## 14. Cláusulas suspensivas — qué entran en el boleto

### 14.1 Cláusulas estándar (las que faltan se pelean en mediación)
- "El boleto queda sin efecto si la DD revela: (a) gravámenes no informados, (b) deudas mayores a [monto], (c) ocupantes no declarados, (d) restricciones urbanísticas que impidan el destino previsto, (e) pasivo ambiental requirente de remediación, (f) representación insuficiente del vendedor, (g) sucesión no resuelta, (h) certificados de libre deuda no obtenibles."
- "La seña entregada será devuelta al comprador sin pérdida en caso de no cumplirse las condiciones precedentes en el plazo de [días]."

### 14.2 Cláusulas a medida del caso
- Aprobación de zonificación específica para proyecto.
- Aprobación de crédito hipotecario al comprador.
- Aprobación societaria del comprador (si sociedad).
- Levantamiento de embargos específicos antes de fecha X.
- Cumplimiento de hito ambiental (Fase II negativa).
- Habilitación municipal del proyecto en X plazo.

### 14.3 Validez (CCyCN arts. 343-349)
- Las condiciones suspensivas son válidas si están **redactadas con precisión** (no "lo que aparezca").
- Plazo cierto para cumplimiento.
- Consecuencia clara si no se cumple (devolución de seña + sin penalidad).

---

## 15. Informe DD integral — contenido mínimo

### 15.1 Estructura
1. **Identificación**: inmueble, vendedor, comprador, fecha, equipo DD.
2. **Resumen ejecutivo**: semáforo verde / amarillo / rojo + decisión recomendada.
3. **Capa por capa**: 9 capas con findings, evidencia, severidad.
4. **Contingencias detectadas**: listado priorizado (alto / medio / bajo).
5. **Cláusulas sugeridas para boleto**: redacción específica.
6. **Pricing impact**: cuánto descontar o retener por contingencias.
7. **Anexos**: certificados, planos, fotos, dictámenes.
8. **Firmas**: responsable de cada capa + coordinador.

### 15.2 Semáforo
- **🟢 Verde**: avanzar a boleto + seña con cláusulas estándar.
- **🟡 Amarillo**: avanzar con condiciones suspensivas adicionales, hold-back o ajuste precio.
- **🔴 Rojo**: no avanzar / renegociar de cero / esperar saneamiento del vendedor.

### 15.3 Práctica profesional
- El informe DD se **firma** y se **archiva** (no es un mail).
- Si el comprador es fondo / sociedad: el informe va al comité de inversión como input formal.
- Si se desestima la operación: el informe es la prueba de la decisión razonada.

---

## 16. Errores frecuentes

- Hacer DD **después** de la seña ("ya damos para que no se pierda").
- DD "barata": una sola persona, sin matriculados de cada disciplina.
- Confiar en certificados que entrega el vendedor sin pedir los propios.
- No cruzar título con catastro con realidad física.
- Aceptar cláusula de "lo conozco y lo acepto" sin saber qué hay.
- No verificar capacidad del vendedor (sociedad disuelta, persona inhabilitada).
- No identificar la sociedad conyugal del vendedor → escritura nula sin asentimiento.
- Saltarse la inspección física ("vi fotos").
- No leer el reglamento de copropiedad antes de comprar PH.
- No revisar el contrato del fideicomiso vendedor.
- Posesión adelantada sin escritura simultánea → comprador queda en tenencia frágil.
- Pagar con **efectivo grande** sin compliance UIF → ROS y bloqueo.
- Aceptar que la escritura declare un precio menor al real → defraudación fiscal y problemas futuros.
- DD ambiental ignorada en terrenos con uso previo industrial.
- No verificar prehorizontalidad si compra en pozo (Ley 27.444 + CCyCN 2065).

---

## 17. Preguntas clave del experto (al vendedor, al escribano, al equipo)

### 17.1 Al vendedor (directas)
- ¿Cuándo y cómo adquirió el inmueble?
- ¿Hay alguna persona con derecho actual o potencial sobre el inmueble (cónyuge, heredero, locatario, ocupante, acreedor)?
- ¿Conoce alguna deuda activa, juicio en curso o medida cautelar?
- ¿Hubo uso industrial, comercial o agropecuario intensivo en algún momento?
- ¿Existen ampliaciones o modificaciones no declaradas al municipio?
- ¿Por qué vende? (la respuesta da información táctica y a veces revela el problema).

### 17.2 Al escribano
- ¿Cadena dominial limpia 20 años?
- ¿Algún antecedente con observaciones o saltos?
- ¿Riesgo de acción de reducción por donación previa?
- ¿Algún acreedor con preferencia detectado?
- ¿Recomendación de cláusulas adicionales?

### 17.3 Al equipo propio
- ¿Tenemos los 9 frentes cubiertos?
- ¿Alguna capa quedó "porque era confiable"? → revisar.
- ¿El pricing absorbe las contingencias o estamos sub-asegurándonos?
- Si se cae la operación hoy, ¿el reserva se recupera entera?

---

## 18. Cuándo escalar a asesores específicos

| Hallazgo | Asesor a sumar |
|---|---|
| Sucesión compleja, herederos múltiples | Abogado de sucesiones |
| Sociedad vendedora con balance dudoso | Auditor + abogado societario |
| Fideicomiso vendedor con conflicto entre fiduciantes | Abogado fiduciario especializado |
| Pasivo ambiental sospechoso | Consultor ambiental + abogado ambiental |
| Construcción sin permiso o sobre-edificación | Arquitecto matriculado + abogado urbanístico |
| Inhibición / embargo de monto incierto | Abogado litigante |
| Operación con PEP / monto alto | Compliance UIF + abogado penal económico |
| Tierras rurales con Ley 26.737 | Abogado especialista en rural |
| Diferencia título vs catastro > 5% | Agrimensor + escribano |
| Ocupante con > 10 años | Abogado posesorio |

---

## 19. Caso especial: comprando en pozo / boleto a desarrollador

### 19.1 Capas que se intensifican
- **Personas**: ¿quién es el desarrollador / fideicomiso? ¿track record? ¿concurso previo?
- **Dominial**: ¿el terreno está a nombre del fiduciario o de un tercero "que luego transfiere"?
- **Urbanística**: ¿permiso de obra otorgado? ¿hito de avance?
- **Contractual**: prehorizontalidad obligatoria si hay PH a constituir (CCyCN 2070-2072 + Ley 27.444).
- **Patología del constructor**: ver `../05-construccion/patologia-constructor-en-problemas.md`.
- **Garantías**: seguro de caución obligatorio si hay anticipos (Ley 27.444 — vigencia y alcance por jurisdicción).

### 19.2 Red flags específicos
- Fideicomiso recién constituido, sin track record.
- Anticipo > 30% sin caución o sin avance equivalente.
- Boleto sin escribano interviniente.
- Plazo de entrega indefinido o "sujeto a habilitaciones".
- Cláusula de actualización abusiva o sin tope.

### 19.3 Práctica profesional
- Boleto **siempre con escribano** del comprador o neutral.
- Inscripción en prehorizontalidad cuando corresponda.
- Caución obligatoria + verificación de la póliza.
- Seguimiento mensual de avance real (no solo certificación).

---

## 20. Resumen ejecutivo (lo que el chat tiene que recordar)

- **DD integral = 9 capas + secuencia + informe firmado + cláusulas en boleto.**
- **Orden: reserva con condición suspensiva → DD → boleto con cláusulas → escritura.**
- **Nada de seña sin dominio + libre deuda municipal/provincial + capacidad + zonificación verificados.**
- **El informe DD se firma, se archiva y manda al comité.**
- **Semáforo: 🟢 avanzar, 🟡 cláusulas/precio, 🔴 retraer.**
- **Red flags cruzados (apuro vendedor, precio anómalo, doc incompleta, efectivo grande) = bandera roja transversal.**
- **Plazos típicos: 7-30 días según producto. Si te apuran, mal.**
- **Cada capa tiene su matriculado. "Uno que sabe de todo" no existe.**

---

## 21. Reglas operativas para el chat

- **Estable y respondible:** estructura 9 capas, secuencia operativa (fases 0-4), red flags por capa, cláusulas suspensivas estándar, contenido del informe DD, errores frecuentes, preguntas clave, jurisdicción AR + CCyCN.
- **🔴 Volátil — validar antes de citar:** plazos puntuales de cada provincia para certificados, montos de UIF, alícuotas de sellos, normativa ambiental local (CAA, RAMQS), versión vigente de Ley 26.737, último estado de prehorizontalidad y Ley 27.444.
- **Cuando el usuario pregunta "¿qué hago si...?":** primero ubicar la capa (dominial / gravámenes / personas / urbanística / fiscal / técnica / ambiental / contractual / ocupacional), luego dar el paso operativo, luego decir cuándo escalar.
- **Tono:** experto que ya pisó esta cancha, no manual genérico. Decisional, no informativo.
- **Si la pregunta cae 100% en una capa específica:** redirigir al archivo dedicado (`./due-diligence-dominial.md`, `./escritura-y-rpi.md`, etc.) además de responder.

---

**Ver también:**
- `./due-diligence-dominial.md`
- `./boleto-compraventa.md`
- `./escritura-y-rpi.md`
- `./prehorizontalidad.md`
- `./cesion-de-boleto.md`
- `./usucapion.md`
- `./ley-26737-tierras-rurales.md`
- `../05-construccion/patologia-constructor-en-problemas.md`
- `../05-construccion/change-orders-claims.md`
- `../00-fundamentos/zonificacion-fot-fos.md`
- `../02-normativa/` (ley de alquileres, defensa consumidor, UIF)
- `../04-impuestos/` (impuestos al inmueble y a la transferencia)
- `../09-triple-impacto/` (ambiental)
