---
title: "Security Token Offerings inmobiliarios (STO): tokenización y marco regulatorio AR"
topic: "cnv-bcra"
subtopic: "sto"
jurisdiction: "AR"
last_verified: "2026-05-12"
sources:
  - "CNV — RG 994/2024 y resoluciones sobre cripto, valores negociables digitales"
  - "Casos LATAM (BR — CVM, MX — CNBV pilots)"
  - "Casos globales (RealT, Lofty, Fundrise tokens)"
keywords: [sto, security token, security token offering, tokenizacion, token, blockchain, ethereum, cripto, valor negociable digital, vnd, cnv, oferta publica, oferta privada, fractional ownership, propiedad fraccionada, smart contract, psav, defi, rwa, real world asset]
audience: ["developer", "investor", "cto", "abogado", "estructurador"]
confidence: "media"
---

# Security Token Offerings (STO) inmobiliarios

## TL;DR
- STO = emisión de un instrumento financiero (security) en formato **token blockchain** que representa derechos sobre un activo real.
- En real estate: token = porción del flujo o equity de un inmueble / desarrollo / portfolio.
- En AR: marco CNV en construcción; reglas sobre cripto / VND avanzan. Sin un canal formal para STO local masivo aún (mid-2026).
- Casos globales: RealT, Lofty, Fundrise tokens, BlackRock BUIDL, ondo. En LATAM: pilots Brasil (Hashdex, MB) y México.
- Promesa: liquidez, fraccionamiento, distribución global, automatización. Realidad: regulación, custodia, KYC/AML, tecnología siguen siendo barreras.

---

## 1. Conceptos base

### 1.1 Token vs criptomoneda
- **Criptomoneda** (BTC, ETH): activo nativo de su red, sin emisor.
- **Token**: activo emitido sobre una red existente, con emisor identificable.
- **Stablecoin**: token con valor anclado a fiat (USDT, USDC, DAI).
- **Security token**: token que es valor negociable (sujeto a regulación de mercado de capitales).
- **Utility token**: token que da acceso a un servicio (regulación distinta).

### 1.2 Tipos de security token inmobiliario
- **Equity token**: representa porción de equity del SPV dueño del activo.
- **Debt token**: representa porción de deuda emitida por el SPV.
- **Revenue-share token**: derecho a flujo de renta proporcional.
- **Hybrid**: combina.

### 1.3 STO vs IPO vs ICO
- **IPO**: oferta pública tradicional de acciones, con prospecto formal.
- **ICO**: emisión de utility token, sin marco formal — boom 2017, mayor parte hoy considerada ilegal o restringida.
- **STO**: emisión de security token bajo marco regulatorio.

---

## 2. Por qué tokenizar real estate

### 2.1 Promesa
- **Fraccionamiento**: ticket muy bajo (USD 100 puede comprar fracción de inmueble premium).
- **Liquidez**: tokens transables en exchanges secundarios 24/7.
- **Distribución global**: inversor internacional sin fricciones bancarias.
- **Automatización**: smart contract distribuye rentas automáticamente.
- **Transparencia**: registro inmutable en blockchain.

### 2.2 Realidad actual
- Liquidez secundaria muy baja en la mayoría de los casos.
- KYC/AML obligatorio (no es anónimo, restricción para inversor en jurisdicciones específicas).
- Custodia: si pierdo la wallet, perdí el activo.
- Regulación heterogénea por jurisdicción.
- Costos de emisión y operación pueden ser altos.

### 2.3 Casos de uso reales
- Acceso a inmuebles premium con ticket bajo (RealT en Detroit, Lofty multi-ciudad).
- Tokenización de fondos inmobiliarios (BUIDL de BlackRock, Ondo).
- Crowdfunding inmobiliario con secundario activo.

---

## 3. Marco regulatorio AR

### 3.1 CNV — Valor Negociable Digital (VND)
- CNV ha emitido normas sobre cripto activos y VND.
- RG 994/2024 + posteriores: regulación de PSAV (Proveedores de Servicios de Activos Virtuales).
- STO formal en AR: aún no hay un canal masivo, casos piloto.

### 3.2 Caracterización jurídica
- Si el token representa un derecho con expectativa de beneficio sobre un activo subyacente con esfuerzo de terceros: **es valor negociable** y cae bajo CNV.
- Howey test (de origen US) usado como referencia.

### 3.3 Requisitos típicos de oferta pública
- Prospecto.
- Auditoría.
- Calificación.
- Listado en MAE / BYMA o equivalente.
- En STO: el listado podría ser en una plataforma autorizada con DLT integrado.

### 3.4 Oferta privada
- Hasta 35 inversores calificados.
- Menos requisitos.
- En STO: muchos casos arrancan privados.

### 3.5 PSAV — proveedores de servicios de activos virtuales
- Registro en CNV.
- Cumplimiento UIF (Resolución 49/2024).
- KYC / AML obligatorio.
- Permite operar plataformas, exchanges, custodios.

> Ver `./psav-cripto.md`.

### 3.6 BCRA
- Restricciones a operar cripto desde el sistema financiero argentino.
- Bancos: limitaciones.
- Cambio en evolución.

---

## 4. Estructura típica de STO inmobiliario

### 4.1 Vehículo legal
- SPV / sociedad / fideicomiso dueño del inmueble.
- Emisor de los tokens = el SPV o vehículo financiero asociado.
- Tokens representan parte del equity o derecho específico.

### 4.2 Tecnología
- Red blockchain (Ethereum, Polygon, Avalanche, Arbitrum, BSC).
- Smart contract del token (estándar ERC-20, ERC-1400 para security tokens, ERC-3643).
- Whitelisting (solo wallets KYC pueden recibir).
- Función de freeze / claw-back para cumplimiento.

### 4.3 Custodia
- Custodio cualificado (en jurisdicciones reguladas).
- En AR: pendiente de regulación específica.

### 4.4 Distribución de rentas
- Smart contract distribuye rentas automáticamente (mensual, trimestral).
- Stablecoin (USDC, USDT) o fiat off-chain.

### 4.5 Mercado secundario
- Plataforma propia del emisor.
- Exchange autorizado.
- Permite transmitir tokens entre wallets verificadas.

---

## 5. Flujo de un STO

### 5.1 Pre-emisión
1. Estructurar el SPV legalmente.
2. Diseñar el token (tipo, derechos, supply, vesting).
3. Desarrollar smart contracts.
4. Auditar smart contracts (CertiK, OpenZeppelin, Trail of Bits).
5. Prospecto y due diligence legal.
6. Aprobación regulatoria.
7. Onboarding plataforma.

### 5.2 Emisión
1. Whitelisting de inversores (KYC/AML completo).
2. Recaudación (en fiat o stablecoin).
3. Mint y distribución de tokens.
4. Liquidación del SPV (compra del inmueble o aporte).

### 5.3 Operación
1. SPV opera el inmueble (alquila, vende, mantiene).
2. Smart contract distribuye flujos.
3. Reportes on-chain + off-chain.

### 5.4 Exit
1. Venta del inmueble subyacente → distribución.
2. Buyback de tokens por el emisor.
3. Listado en secundario (tokens transferibles).

---

## 6. Casos referenciales

### 6.1 Globales
- **RealT** (US): tokens sobre casas residenciales en Detroit, Cleveland, Chicago. Renta semanal en USDC.
- **Lofty** (US): fraccionado multiciudad, secundario activo.
- **Fundrise iPO Token**: emisión token de equity propio.
- **BlackRock BUIDL**: token de fondo de tesoro (no estrictamente real estate pero modelo aplicable).
- **Ondo Finance**: tokenización de productos financieros sobre RWA.

### 6.2 LATAM
- **Brasil**: marco CVM avanzando, Hashdex, Mercado Bitcoin con productos.
- **México**: CNBV piloto regulatorio.
- **AR**: casos piloto chicos, sin canal masivo.

### 6.3 AR específico
- Emisiones experimentales bajo SPV regulado.
- Stablecoins locales (DAI, USDC) usadas en algunos.
- Falta canal formal de oferta pública STO.

---

## 7. Beneficios y riesgos

### 7.1 Beneficios
- Acceso a inversor minorista global.
- Ticket bajo permite fraccionar inmuebles premium.
- Automatización reduce costos administrativos.
- Liquidez potencial vs inmueble físico.
- Transparencia y trazabilidad.

### 7.2 Riesgos
- Regulatorio cambiante.
- Liquidez secundaria sobre-prometida.
- Custodia (perder wallet = perder activo).
- Hackeo de smart contract.
- Cumplimiento KYC/AML caro.
- Costo de emisión alto vs vehículos tradicionales para activos chicos.
- Concentración de inversores extranjeros = riesgo cambiario y de repatriación.

### 7.3 Riesgo AR específico
- Marco regulatorio en construcción.
- Restricciones de capital (cepo) limitan flujo.
- Bancos con poco apetito.
- Inversor local sofisticado prefiere instrumentos tradicionales por seguridad jurídica.

---

## 8. Cuándo conviene tokenizar

### 8.1 Verde
- Activo grande con muchos inversores potenciales.
- Inversor target principalmente internacional con cripto-fluency.
- Renta predecible (residencial maduro, oficinas estabilizadas).
- Equipo legal y tecnológico capacitado.

### 8.2 Amarillo
- Activo chico (costos fijos no amortizan).
- Inversor local tradicional (no necesita tokens).
- Activo con flujos inciertos.

### 8.3 Rojo
- Sin equipo legal especializado → no se hace.
- Sin claridad regulatoria → no se hace.
- Si el equipo cree que tokenizar resuelve un mal proyecto: no.

---

## 9. Costo estimado de emisión

| Item | Costo aproximado USD |
|---|---|
| Estructuración legal | 30k-150k |
| Smart contract dev + audit | 30k-100k |
| Plataforma propia o licencia | 20k-200k |
| KYC / AML provider | 10k-50k anual |
| Custodio | variable |
| Registración / autorizaciones | 10k-50k |
| Marketing y comercialización | variable |
| **Total típico mínimo** | **100k-500k** |

> Para activos < USD 5M: break-even difícil. STO más razonable desde USD 10-20M+.

---

## 10. Comparación con alternativas tradicionales

| Atributo | FCI cerrado RE | Fideicomiso financiero | STO |
|---|---|---|---|
| Ticket mínimo | USD 1k-50k | USD 1k-50k | USD 10-500 |
| Liquidez secundaria | Media (BYMA) | Baja-media | Variable |
| Costo emisión | Medio | Bajo-medio | Alto |
| Distribución internacional | Limitada | Limitada | Amplia |
| Madurez regulatoria AR | Alta | Alta | Baja |
| Automatización | Manual | Manual | Smart contract |

---

## 11. Tendencias 2025-2026

### 11.1 RWA (Real World Assets)
- Tokenización de RWAs creciendo (BlackRock, Franklin Templeton, Ondo, Maple).
- Real estate dentro del RWA.

### 11.2 DeFi + RWA
- Tokens RE usados como colateral en DeFi.
- Yield combinado on-chain.

### 11.3 Regulación
- MiCA (UE) entra en vigor 2024-2025.
- US: SEC vs CFTC, Trump admin abrió espacio.
- LATAM: marcos similares emergiendo.
- AR: regulación CNV en construcción, ritmo mediano.

### 11.4 Wallet abstraction
- UX mejorando (cuenta sin necesidad de manejo manual de wallet).
- Permite onboarding tradicional con seguridad cripto.

---

## 12. Errores comunes

- Tokenizar para "hacer tokenización" sin caso de negocio claro.
- Subestimar el costo de cumplimiento (KYC/AML, custodia, auditoría).
- Prometer liquidez secundaria sin asegurar mercado.
- No tener prospecto legal sólido (riesgo de calificar mal el token).
- Smart contract sin auditoría externa.
- No considerar el riesgo cambiario para inversor extranjero.
- Considerar el token como "inmune" a marco legal AR.

---

## 13. Reglas operativas para el chat

- **Estable y respondible:** definición STO, estructura típica, beneficios y riesgos, casos referenciales, comparación con vehículos tradicionales, cuándo conviene.
- **🔴 Volátil:** marco regulatorio AR (CNV, BCRA, PSAV) en evolución continua, casos AR concretos, costos exactos, plataformas disponibles.

---

**Importante:** este documento es **informativo, no asesoramiento legal ni financiero**. Toda emisión STO requiere análisis legal y técnico específico, con asesores especializados en CNV y blockchain.

---

**Ver también:**
- `./marco-cnv.md`
- `./oferta-publica.md`
- `./psav-cripto.md`
- `./vehiculos-cnv-re.md`
- `./mep-ccl-cripto.md`
- `../16-uif-blanqueo/uif-pep-onboarding.md`
- `../10-estrategia/estructuras-fondeo-institucional.md`
- `../15-tecnologia-proptech/ai-workflows-developers.md`
