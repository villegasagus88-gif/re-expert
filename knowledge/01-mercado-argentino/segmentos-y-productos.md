---
title: "Segmentos y productos inmobiliarios en Argentina"
topic: "mercado"
subtopic: "segmentos"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "Colliers, Cushman & Wakefield, JLL, CBRE — reportes trimestrales AR"
  - "AEV, CEDU — informes sectoriales"
keywords: [segmentos, residencial, oficinas, retail, logistica, industrial, hoteleria, alquiler temporario, build to rent, coliving, senior living, multifamily]
audience: ["desarrollador", "inversor", "chat"]
confidence: "alta"
---

# Segmentos y productos del mercado AR

## TL;DR
- 7 grandes segmentos con dinámica propia: residencial, oficinas, retail, logística/industrial, hotelería, alquiler temporario, usos especiales.
- Cada segmento tiene **producto típico**, **comprador/inquilino tipo**, **rango de cap rate**, **plazo y riesgo**.
- En AR el residencial domina volumen, pero logística e industrial son los de mejor cap rate.
- 🔴 Cap rates y vacancia varían trimestre a trimestre — ver `./benchmarks.md` y derivar a fuente.

## 1. Residencial

### 1.1 Multifamily / departamentos
- Producto dominante en CABA y centros urbanos.
- Tipologías: monoambiente, 1, 2, 3, 4 ambientes; lofts, dúplex, penthouse.
- Mix típico CABA: 40% 1amb, 35% 2amb, 25% 3+amb (varía por barrio).
- Comprador: inversor minorista (renta) + usuario final.
- Cap rate bruto típico: bajo en CABA por sobreprecio del USD.

### 1.2 Unifamiliar / barrios cerrados / countries
- AMBA Norte/Oeste, Córdoba, Rosario, Mendoza, Pilar, Nordelta, Puertos.
- Producto: lote + casa por construcción o llave en mano.
- Comprador: familia, mudanza por calidad de vida.
- Plazo de venta más largo que departamento.

### 1.3 Vivienda asequible / social
- Procrear, programas provinciales, ley 14.449 PBA (hábitat).
- Mercado con subsidio estatal o financiamiento blando.

### 1.4 Build-to-rent (BTR) / multifamily institucional
- Edificio entero diseñado para renta, mantenido por operador.
- Aún incipiente en AR; pioneros: IRSA, fondos privados.
- Cap rate objetivo mayor a venta minorista por estabilidad de flujo.

### 1.5 Co-living / student housing / senior living
- Co-living: unidades compactas + amenities compartidos.
- Student housing: cerca de universidades (UBA, UCA, UTDT, UCC, UNL).
- Senior living: aún muy incipiente en AR; oportunidad demográfica.

## 2. Oficinas

### 2.1 Clase A
- Catalinas Norte, Puerto Madero, Polo Dot, Libertador Norte, GBA Norte (Olivos, Vicente López).
- Inquilinos: corporativos, multinacionales.
- Cap rate típico: 7-10% USD (varía).

### 2.2 Clase B y C
- Microcentro, barrios consolidados.
- Vacancia alta post-pandemia + work from home.
- Oportunidad: reconversión a residencial (CABA tiene incentivos).

## 3. Retail

### 3.1 Shopping
- Operadores: IRSA (Alto Palermo, Abasto, etc.), Cencosud, Inversora Catedral.
- Renta vinculada a facturación del locatario.

### 3.2 Street comercial
- Avenidas comerciales, calles peatonales.
- Caída por e-commerce + alquiler temporario.

### 3.3 Strip centers / vecinales
- Crecimiento en GBA, segmento subatendido.

## 4. Logística e industrial

### 4.1 Logística clase A
- Parques: Polo Industrial Pilar, Ezeiza, Tortuguitas, Garín.
- Demanda: e-commerce (Mercado Libre, Amazon), 3PL.
- Vacancia históricamente baja, cap rates atractivos.

### 4.2 Industrial
- Polos: La Matanza, San Martín, Tres de Febrero, Pilar.
- Producto: nave industrial 1.000-20.000 m².

### 4.3 Última milla / urbano
- Mini-depósitos en CABA por last-mile.

## 5. Hotelería

- Clases: 5*, 4*, 3*, hostels, alquiler temporario.
- Operadores nacionales (Alvear, Faena) e internacionales (Hilton, Marriott, Hyatt).
- Modelo: propietario + operador (gestión) o mixto.
- Métrica clave: RevPAR (revenue per available room).
- Recuperación post-pandemia desigual; turismo receptivo se beneficia con tipo de cambio.

## 6. Alquiler temporario

- Plataformas: Airbnb, Booking, Vrbo, ML Alquileres Temporarios.
- Regulación CABA: Ley 6.255 — registro obligatorio.
- Impacto: encareció alquileres tradicionales en zonas turísticas (Palermo, Recoleta, Bariloche).
- Discusión política activa; potencial regulación más restrictiva.

## 7. Usos especiales

- **Data centers** — incipiente, alto consumo eléctrico.
- **Self storage** — crecimiento en CABA y GBA Norte.
- **Vivienda corporativa** (corporate housing) — relocaciones.
- **Coworking** (WeWork, Selina, locales) — segmento aplanado post-pandemia.

## 8. Matriz de decisión rápida

| Producto | Cap rate USD | Plazo desarrollo | Liquidez de salida | Capital mínimo |
|---|---|---|---|---|
| Depto. CABA pozo | Bajo (renta) | 24-36m | Alta | Bajo |
| Depto. CABA terminado | Bajo (renta) / medio (USD) | 0 | Alta | Medio |
| Barrio cerrado lote | n/a | 0-12m | Media | Medio |
| Logística clase A | Alto | 18-30m | Media | Alto |
| Oficina clase A | Medio-alto | 36-48m | Media | Muy alto |
| Hotel | Variable | 36-60m | Baja | Muy alto |
| Alquiler temporario | Alto | 0 | Alta | Bajo |

> 🔴 Cap rates exactos varían trimestralmente. Para valor actual ver reportes de Colliers / Cushman / JLL / CBRE.

## 9. Reglas operativas para el chat

- **Estable:** definición de cada segmento, producto típico, drivers, lógica de cap rate vs riesgo, players por segmento.
- **🔴 Volátil:** cap rate específico, vacancia actual, precio m² actual, RevPAR.
- Si la pregunta es de viabilidad de un segmento → marco general + variables a definir + derivar a un broker comercial (Colliers, Cushman, JLL, CBRE) o cámara sectorial.

## Ver también
- `./benchmarks.md`
- `./players-y-actores.md`
- `../07-comercial/mix-tipologias.md`
- `../10-estrategia/modelos-negocio.md`
