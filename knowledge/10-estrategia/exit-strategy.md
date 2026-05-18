---
title: "Exit strategy — salida de proyectos inmobiliarios en AR"
topic: "estrategia"
subtopic: "exit"
jurisdiction: "Argentina"
last_verified: "2026-05-15"
sources:
  - "CCyCN (cesión, dación en pago, disolución contratos asociativos)"
  - "Ley 24.522 (concursos y quiebras)"
  - "Ley 19.550 / LGS (sociedades)"
  - "RG AFIP varias (régimen impositivo de exits)"
  - "Práctica RE AR: M&A de fideicomisos y SPVs"
keywords: [exit, exit strategy, salida proyecto, salida inversor, venta proyecto, M&A fideicomiso, venta SPV, venta sociedad, disolucion fideicomiso, liquidacion proyecto, refinanciacion, BTR pivot, cesion derechos, dacion en pago, venta secundaria, salida ordenada, sell out, sell down, drag along, tag along, ROFR, ROFO, put option, call option, redemption, recompra cuotas, concurso preventivo, exit fiscal, impuesto exit, ganancias venta UF, IVA venta inmueble, exit waterfall, hurdle rate, promote, carry]
audience: ["developer", "inversor", "asset manager", "abogado RE", "chat"]
confidence: "alta"
priority: "obligatorio"
---

# Exit strategy — salidas de proyectos RE AR

> Catálogo de salidas posibles, cuándo conviene cada una, impacto
> fiscal y cláusulas contractuales que las facilitan. Pensar el
> exit **antes de entrar** es la diferencia entre liquidez y
> trampa.

## TL;DR

- **Exit ≠ una sola opción.** Hay al menos 10 vías de salida de un proyecto RE; la elección depende del **vehículo, del estado de la obra, del mercado y del inversor**.
- **Diseñar el exit en el día 1** (cláusulas de drag-along, tag-along, ROFR, put/call) ahorra años de pelea cuando aparece la oportunidad o el problema.
- **Exit ordenado siempre vence al exit forzado.** Concurso, liquidación judicial y venta de apremio destruyen valor (-30% a -60% del fair value).
- **El vehículo manda el costo fiscal.** Misma operación puede pagar 0% a 35% según se haya estructurado fideicomiso al costo / fideicomiso financiero / SAS / SA.

---

## 1. Mapa de salidas

| # | Salida | Estado proyecto | Quién decide | Liquidez |
|---|---|---|---|---|
| 1 | Venta de UFs en pozo (pre-venta) | Pre-obra / obra | Developer | Lenta, en cuotas |
| 2 | Venta de UFs terminadas | Terminado | Developer | Lenta |
| 3 | Venta del SPV/fideicomiso completo | Cualquiera | Inversores | Rápida si hay comprador |
| 4 | Pivot a renta (BTR) | Terminado | Inversores | Nula inmediata, recurrente |
| 5 | Refinanciación con nuevo equity | Cualquiera | Inversores | Parcial |
| 6 | Crowdfunding / tokenización secundaria | Terminado | Inversores | Variable |
| 7 | Cesión de boleto / derechos | Pre-escritura | Comprador secundario | Inmediata |
| 8 | Permuta inversa (devolver tierra, salir) | Pre-obra | Aportante de tierra | Inmediata |
| 9 | Dación en pago a acreedores | Crisis | Developer | No es liquidez (extingue deuda) |
| 10 | Disolución ordenada del fideicomiso | Terminado | Fiduciante | Lenta |
| 11 | Concurso preventivo | Crisis | Developer | Última opción |
| 12 | Quiebra / liquidación | Default | Acreedores | Destrucción de valor |

---

## 2. Las salidas comerciales (1, 2, 7)

### 2.1 Venta de UFs en pozo (pre-venta)
- **Cuándo:** desde la aprobación municipal hasta avance ~70%.
- **Ventaja:** financia la obra con el dinero del comprador (cuotas).
- **Desventaja:** precio descontado vs terminado (15-30% típico), riesgo de incumplimiento del developer activa LDC.
- **Estructuración fiscal:** suele ir vía fideicomiso al costo (sin renta para el fiduciante, sólo aporte y recibe UFs); o venta directa (genera ITI / cedular según el caso).

### 2.2 Venta de UFs terminadas
- **Cuándo:** posterior a entrega final.
- **Ventaja:** precio pleno, ciclo de venta más corto.
- **Desventaja:** capital atrapado más tiempo, costo financiero alto en AR.
- **Fiscal:** PF habitualista → IVA + ganancias 35%; PF no habitualista → ITI 1.5% o cedular 15%; PJ → IVA + ganancias.

### 2.3 Cesión de boleto / derechos
- **Cuándo:** comprador originario o inversor minorista quiere salir antes de la escritura.
- **Marco:** CCyCN art. 1614 ss (cesión de derechos).
- **Requisitos:** boleto que no prohíba cesión + notificación al developer + fee de cesión si está pactado.
- **Fiscal:** la diferencia entre lo que pagó el cedente y lo que recibe está alcanzada por ganancias (renta tributable) — no es vivienda única exenta porque aún no hay título.

---

## 3. Salida del vehículo entero (3, 5)

### 3.1 Venta del SPV / fideicomiso completo (M&A)
- **Cuándo:** otro fondo o developer institucional compra el vehículo en lugar de las UFs una por una.
- **Mecánica:** transferencia de cuotapartes / acciones del SPV → no se transfieren los inmuebles unidad por unidad → ahorro fiscal y procedimental enorme.
- **Ventaja:** liquidez inmediata + plusvalía gravada como "acciones" no como "inmueble" (régimen distinto, en general más favorable).
- **Desventaja:** comprador hace due diligence profundo (contingencias laborales, fiscales, regulatorias) → descuento por riesgo de pasivo oculto.
- **Drivers de descuento típicos:** vicios ocultos, juicios laborales abiertos, impuestos pendientes, no-conformidades urbanísticas.

### 3.2 Refinanciación con nuevo equity
- **Cuándo:** inversores originales quieren liquidez parcial, el proyecto sigue.
- **Mecánica:** nuevo inversor entra al cap table; los originales cobran parcial (cash-out) y diluyen.
- **Ejemplo AR:** fideicomiso con 10 inversores 10% cada uno; 5 quieren salir → entra un fondo institucional que compra esos 5 puntos al fair value menos discount.

---

## 4. Pivot estratégico (4, 6)

### 4.1 Pivot a build-to-rent (BTR)
- **Cuándo:** el mercado de venta está frío pero el de alquiler aguanta.
- **Mecánica:** terminar el edificio + alquilar todo en bloque + mantener como activo de renta.
- **Resultado:** convierte un activo "para vender" en uno "para rentar" → cambia el ciclo de capital.
- **Implicancia fiscal:** régimen de rentas pasivas (locación) en lugar de ganancia por venta.

> Ver `./build-to-rent-ar.md`.

### 4.2 Crowdfunding / tokenización secundaria
- **Cuándo:** liquidez parcial post-entrega para inversores chicos.
- **Marco AR 2026:** régimen CNV PFC (plataformas de financiamiento colectivo) + experimentación con tokens.
- **Limitaciones AR:** mercado secundario aún incipiente; spreads altos.

> Ver `../15-tecnologia-proptech/tokenizacion.md` (si existe).

---

## 5. Salidas de crisis (9, 10, 11, 12)

### 5.1 Dación en pago (CCyCN art. 942)
- **Cuándo:** developer no puede pagar a un acreedor; le da UFs en lugar de dinero.
- **Mecánica:** extingue deuda contra entrega del bien.
- **Riesgos:** acreedor puede no querer UFs (las vende a descuento); fisco puede impugnar si fue para defraudar.
- **Acreedor típico:** constructor, financista de obra, dueño del terreno con saldo de precio.

### 5.2 Disolución ordenada del fideicomiso
- **Cuándo:** todas las UFs entregadas + obligaciones cumplidas + el fideicomiso terminó su objeto.
- **Mecánica:** rendición de cuentas del fiduciario → distribución del remanente → cierre registral.
- **Trampa típica:** quedan UFs sin vender → distribución en especie a fiduciantes (cada uno se queda con UFs proporcionales).

### 5.3 Concurso preventivo
- **Cuándo:** el SPV no puede pagar, hay posibilidad de reorganización.
- **Marco:** Ley 24.522.
- **Ventajas para el developer:** suspende ejecuciones, congela intereses, ordena negociación con acreedores en clases.
- **Costo:** reputacional alto; futuros proyectos con esa marca son más caros de financiar.
- **Compradores con boleto:** quedan en el régimen de oponibilidad si tienen fecha cierta + posesión + ≥25% pagado; si no → quirografarios.

### 5.4 Quiebra
- **Cuándo:** concurso fracasa o se va directo (a pedido propio o de acreedor).
- **Efecto:** liquidación de activos por la justicia.
- **Destrucción de valor:** típicamente -40% a -60% vs fair value. Procesos largos (3-7 años).
- **Es el último recurso.**

> Ver `../02-normativa/litigios-tipicos-re.md` §5 para detalle procesal.

---

## 6. Cláusulas contractuales que habilitan exits

| Cláusula | Qué hace | Cuándo usarla |
|---|---|---|
| **Drag-along** | Mayoría que vende arrastra a minoría a vender en mismas condiciones | Pacto con inversor mayoritario que quiere liquidez sin ser bloqueado por minorías |
| **Tag-along** | Minoría puede sumarse a venta de mayoría | Protección del minoritario |
| **ROFR (Right of First Refusal)** | Otros socios tienen derecho a igualar oferta de tercero | Mantener cap table cerrado |
| **ROFO (Right of First Offer)** | Otros socios pueden ofertar antes de que se busque tercero | Versión más amigable de ROFR |
| **Put option** | Inversor puede obligar al SPV/socio a recomprar sus cuotas a fórmula | Liquidez programada al inversor minoritario |
| **Call option** | Sponsor puede obligar a inversor a vender al sponsor a fórmula | Sponsor consolida control |
| **Redemption / recompra programada** | El SPV recompra cuotas en fechas predefinidas | Fideicomisos con horizonte fijo |
| **Lock-up** | Prohibición de vender durante X meses | Estabilidad inicial |
| **Cláusula resolutoria por hito** | Si no se cumple hito (permiso, financiación), se disuelve sin penalidad | Proyectos con riesgo regulatorio alto |
| **Drag por incumplimiento** | Default de un socio activa el arrastre a venta forzada | Gobernanza dura |

---

## 7. Waterfall y promote en el exit

El exit es el momento donde se ejecuta la **cascada de distribución** (waterfall):

1. **Devolución de capital** a inversores (preferred return típicamente 8-10% anual).
2. **Pago de deuda** (senior, mezzanine).
3. **Catch-up del sponsor** (algunos modelos).
4. **Promote / carry** del sponsor (20-30% sobre lo que supera el hurdle).
5. **Distribución pro-rata final** al resto del capital.

> Ver `../06-financiero/waterfall-inversores.md`.

**Tensión típica en exits:** sponsor quiere acelerar para cobrar promote; inversores quieren maximizar precio aunque tarde. → Por eso las cláusulas de plazo, hurdle y aprobación importan.

---

## 8. Impacto fiscal del exit por vehículo

| Vehículo | Salida típica | Tributación |
|---|---|---|
| **PF, vivienda única** | Venta directa | ITI 1.5% + exención si reemplaza vivienda (CDI 5 años) |
| **PF, no habitualista** | Venta directa | Cedular 15% sobre ganancia (resultado real con ajuste) |
| **PF, habitualista** | Venta directa | Ganancias 35% sobre renta + IVA si construyó/recicló |
| **PJ (SA, SRL)** | Venta directa | Ganancias 25-35% (escala) + IVA en obras propias |
| **SAS** | Venta directa / venta de acciones | Igual PJ; venta de acciones tributa cedular 15% |
| **Fideicomiso ordinario** | Venta directa | Como PJ (responsable inscripto) |
| **Fideicomiso al costo** | Distribución de UFs a fiduciantes | Sin renta en el fideicomiso (aporte y recupero); IVA puede aplicar |
| **Fideicomiso financiero** | Venta de certificados / títulos | Régimen de oferta pública con tratamiento diferenciado |

> Ver `../04-impuestos/` para detalle por figura.

---

## 9. Patologías de exit

### 9.1 Inversor minoritario bloquea exit favorable
- **Sin drag-along** → un 5% puede frenar venta del 95%.
- **Mitigación:** drag desde día 1.

### 9.2 Sponsor acelera venta para cobrar promote
- **Síntoma:** el sponsor presiona vender en mercado deprimido.
- **Mitigación:** hurdle alto + aprobación calificada de inversores para venta antes de plazo.

### 9.3 Exit por debajo del fair value por urgencia
- **Síntoma:** vencimientos de deuda fuerzan venta acelerada → descuento de mercado del 20-40%.
- **Mitigación:** refinanciación previa + buffer de liquidez + line of credit.

### 9.4 Pasivos ocultos descubiertos en DD post-cierre
- **Síntoma:** comprador del SPV descubre juicios laborales o fiscales no declarados → retiene precio diferido o reclama.
- **Mitigación:** representations & warranties (R&W) + escrow + póliza R&W insurance.

### 9.5 Fideicomiso "zombi"
- **Síntoma:** terminó la obra pero el fideicomiso no se disuelve por trámites pendientes (subdivisión, planos finales, escrituración).
- **Mitigación:** roadmap de cierre con responsable y fecha por hito; auditoría de close-out.

### 9.6 Concurso "creativo" para licuar pasivos
- **Síntoma:** developer usa concurso para licuar a compradores con boleto.
- **Marco:** jurisprudencia tiende a proteger al consumidor con boleto + posesión + pago ≥25%.
- **Mitigación del comprador:** verificar en término + tercería + apoyo de defensoría del consumidor.

---

## 10. Checklist de salida (developer)

Antes de iniciar el exit:
- [ ] Estado de obligaciones legales (LDC, vicios, posventa).
- [ ] Estado fiscal (sin deudas / con plan de pago).
- [ ] Pasivos laborales auditados (ART, F931, Ley 22.250).
- [ ] R&W + escrow definidos.
- [ ] Cap table actualizado + cláusulas de drag/tag listas.
- [ ] Valuación independiente (broker institucional + tasador).
- [ ] Estructura fiscal del exit modelada con asesor.
- [ ] Comunicación a inversores: timing, fairness opinion, waterfall esperado.

---

## 🔴 Datos volátiles vs 🟢 estables

**🔴 Volátil:**
- Tasas de tributación (alícuotas de ganancias, IVA, cedular).
- Costo de capital del comprador del SPV (afecta valuación).
- Apetito del mercado por M&A inmobiliario.

**🟡 Semivolátil:**
- Régimen del cedular sobre venta de inmuebles.
- Topes y procedimientos del concurso.

**🟢 Estable — respuesta directa:**
- Mapa de salidas posibles.
- Cláusulas contractuales que las habilitan.
- Patologías estructurales.
- Lógica del waterfall.

---

## Ver también
- `../02-normativa/litigios-tipicos-re.md` — qué pasa cuando el exit ordenado falla.
- `../06-financiero/waterfall-inversores.md` — cascada de distribución.
- `./joint-venture.md` — gobernanza inicial que define el exit.
- `./build-to-rent-ar.md` — pivot a renta como exit.
- `./permuta.md` — permuta inversa como salida.
- `../04-impuestos/` — costo fiscal por figura.
- `../07-comercial/patologias-comerciales.md` — patologías comerciales que afectan el exit.
