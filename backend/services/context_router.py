"""
Context Router — clasifica la pregunta del usuario a uno o más dominios del
KnowledgeBase y selecciona los archivos relevantes.

Dominios soportados (alineados a la estructura `knowledge/` del repo):
    fundamentos, mercado, normativa, laboral, impuestos, construccion,
    financiero, comercial, macro, triple-impacto, estrategia, tasacion,
    suelo-dominio, arquitectura, costos, tecnologia, uif, cnv-bcra,
    seguros, casos, meta, general

`select_context_for_message` devuelve texto listo para inyectar en el
system prompt, con un budget de tokens configurable.
"""
from __future__ import annotations

import logging
import unicodedata
from typing import Literal

from services.knowledge_base_service import _tokenize, knowledge_base

logger = logging.getLogger(__name__)

Domain = Literal[
    "fundamentos",
    "mercado",
    "normativa",
    "laboral",
    "impuestos",
    "construccion",
    "financiero",
    "comercial",
    "macro",
    "triple-impacto",
    "estrategia",
    "tasacion",
    "suelo-dominio",
    "arquitectura",
    "costos",
    "tecnologia",
    "uif",
    "cnv-bcra",
    "seguros",
    "casos",
    "meta",
    "general",
]

# Mapa dominio lógico -> prefijo de carpeta en el bucket `knowledge/`.
# Se usa para filtrar docs por su `domain` (primer segmento del path).
DOMAIN_TO_FOLDER: dict[Domain, str] = {
    "fundamentos": "00-fundamentos",
    "mercado": "01-mercado-argentino",
    "normativa": "02-normativa",
    "laboral": "03-laboral",
    "impuestos": "04-impuestos",
    "construccion": "05-construccion",
    "financiero": "06-financiero",
    "comercial": "07-comercial",
    "macro": "08-macro-argentina",
    "triple-impacto": "09-triple-impacto",
    "estrategia": "10-estrategia",
    "tasacion": "11-tasacion",
    "suelo-dominio": "12-suelo-y-dominio",
    "arquitectura": "13-arquitectura-ingenieria",
    "costos": "14-costos-presupuesto",
    "tecnologia": "15-tecnologia-proptech",
    "uif": "16-uif-blanqueo",
    "cnv-bcra": "17-cnv-bcra",
    "seguros": "18-seguros",
    "casos": "19-casos-de-estudio",
    "meta": "_meta",
    "general": "",  # sin filtro
}

# Orden = prioridad en empates.
ALL_DOMAINS: tuple[Domain, ...] = tuple(DOMAIN_TO_FOLDER.keys())

# Keywords por dominio (sin acentos, minúsculas). Cobertura amplia para
# que cualquiera de los términos típicos del usuario mande al dominio correcto.
_RAW_KEYWORDS: dict[Domain, tuple[str, ...]] = {
    "fundamentos": (
        "developer", "desarrollador", "rol", "teoria", "ciclo", "factibilidad",
        "triple impacto", "que hace un developer", "como funciona",
    ),
    "mercado": (
        "mercado", "panorama", "segmento", "segmentos", "producto", "productos",
        "zonas", "barrios", "players", "actores", "portales", "zonaprop",
        "argenprop", "mercadolibre", "absorcion", "demanda", "oferta",
        "competencia", "benchmarks", "rendimiento", "cap rate",
    ),
    "normativa": (
        "normativa", "ley", "leyes", "codigo", "codigos", "reglamento",
        "ordenanza", "ph", "propiedad horizontal", "urbanistico",
        "urbanismo", "edificacion", "ccyc", "ccycn", "civil", "comercial",
        "8912", "6099", "6100", "alquiler", "alquileres", "27551", "dnu 70",
        "defensa consumidor", "ambiental", "25675", "zonificacion",
        "fot", "fos", "habilitacion", "permiso", "permisos",
        # Cláusulas contractuales aplicadas (capa experta)
        "clausulas boleto", "clausulas contrato", "clausulas locacion obra",
        "clausulas mandato", "clausula reserva", "pacto comisorio",
        "condicion suspensiva", "condicion resolutoria",
        "declaraciones y garantias", "indemnidad", "hold back",
        "arras confirmatorias", "arras penitenciales", "sena confirmatoria",
        "sena penitencial", "art 1059", "art 1083", "art 1086", "art 1184",
        "evicion", "eviccion", "art 1044", "libre de gravamenes",
        "clausula ajuste moneda", "clausula uva", "clausula dolar mep",
        "clausula cer", "fuerza mayor", "hardship", "renegociacion",
        "clausula penal", "resolucion automatica", "carta documento",
        "telegrama colacionado", "arbitraje", "mediacion 26589",
        "fiador codeudor", "mandato sin representacion",
        "mandato con representacion", "cesion derechos", "art 1614",
        "contrato cmar", "contrato gerenciamiento", "clausulas de oro",
        "clausula abusiva", "clausulas abusivas", "abusiva", "abusivas",
        "art 1117", "art 37 ley 24240",
        "open listing", "exclusiva broker", "doble corretaje",
        # Defensa del consumidor aplicada (capa experta)
        "consumidor real estate", "consumidor inmueble", "consumidor pozo",
        "consumidor inmobiliaria", "vendedor profesional",
        "proveedor real estate", "art 8 informacion", "art 11 garantia",
        "art 17 vicios", "art 36 financieras", "art 52 bis",
        "dano punitivo", "daño punitivo", "dano directo", "art 40 lda",
        "art 1092", "art 1099", "art 1100", "publicidad enganhosa",
        "publicidad enganosa", "render publicitario", "oferta vinculante",
        "m2 publicitario", "coprec", "ley 26361", "ley 26993",
        "halabi", "mosca", "ledesma", "cooperativa obrera",
        "contrato adhesion", "no entrega en plazo",
        "demora obra consumidor", "relacion de consumo inmueble",
    ),
    "laboral": (
        "laboral", "lct", "ley 20744", "uocra", "cct", "76/75", "ieric",
        "art", "srt", "riesgos trabajo", "solidaridad", "art 30",
        "modalidades", "dependencia", "autonomo", "contrato trabajo",
        "jornal", "jornales", "convenio", "personal obra",
        # Patología laboral aplicada (capa experta)
        "fraude laboral", "trabajo no registrado", "en negro obra",
        "art 30 lct", "solidaridad laboral", "art 29 lct", "art 29 bis",
        "intermediacion", "tercerizacion fraudulenta",
        "contratista cascara", "empresa cascara", "empresa vacia",
        "rodriguez 1993", "benitez 2009", "vizzoti", "aquino",
        "art trucha", "art sin cobertura", "alta temprana",
        "libreta aportes construccion", "fondo cese laboral",
        "art 17 ley 22250", "comitente solidario", "developer demandado",
        "fideicomiso demandado laboral", "accidente obra", "muerte obrero",
        "decreto 911 96", "resolucion srt 51", "aviso de obra srt",
        "programa de seguridad construccion", "examen preocupacional",
        "rgrl", "oec", "telegrama laboral", "ros laboral",
        "ley 27742", "regularizacion espontanea", "art 11 ley 24013",
        "art 80 lct", "art 132 bis", "ley 27348", "comisiones medicas",
        "subcontratista", "subcontratistas", "subcontratista fraude",
        "subcontratista no registrado", "principal y solidario",
        "en negro", "trabajadores en negro", "obrero en negro",
    ),
    "impuestos": (
        "impuesto", "impuestos", "iva", "ganancias", "bienes personales",
        "cedular", "monotributo", "fideicomiso", "sas", "sociedad",
        "condominio", "leasing", "iibb", "ingresos brutos", "sellos",
        "abl", "tsg", "inmobiliario", "derechos construccion", "plusvalia",
        "afip", "agip", "arba", "dgr", "tributario", "fiscal",
        "estructuras fiscales", "vehiculo fiscal", "iti",
        # Árbol de decisión venta inmueble (capa experta)
        "venta inmueble impuestos", "arbol decision venta",
        "vendedor persona fisica", "vivienda unica exencion",
        "vivienda unica reemplazo", "iti 1.5",
        "impuesto transferencia inmuebles", "cedular inmuebles",
        "cedular 15", "ley 27430", "inmueble desde 2018",
        "habitualista inmobiliario", "iva venta inmueble",
        "iva obra propia", "iva empresa constructora",
        "sellos venta inmueble", "coti afip",
        "codigo oferta transferencia", "retencion vendedor extranjero",
        "beneficiario del exterior", "cdi argentina",
        "monotributista venta inmueble", "fideicomiso al costo venta",
        "dividendos fideicomiso", "retencion ganancias 35",
        "moratoria afip", "defraudacion fiscal", "prescripcion afip",
        "donacion vs venta", "donacion inmueble",
        # Patología fideicomiso aplicada (capa experta)
        "patologia fideicomiso", "fideicomiso al costo problemas",
        "fideicomiso construccion problemas", "fraude fiduciario",
        "autocontratacion fiduciario", "fiduciario constructor mismo",
        "sobrecosto fideicomiso", "cost overrun fideicomiso",
        "dilucion fiduciantes", "aumento unidades fideicomiso",
        "desafectacion cuotas", "mora fiduciante", "default fiduciante",
        "ejecucion cuotas fideicomiso", "fiduciario en problemas",
        "fiduciario quiebra", "fiduciario remocion", "art 1685",
        "art 1685 ccycn", "patrimonio fiduciario separado",
        "fraude pauliana fideicomiso", "asamblea fiduciantes",
        "comite fiduciantes", "salida fiduciante",
        "auditoria fideicomiso", "fiduciario profesional",
        "fiduciario institucional", "resol uif 30 2017",
        "autocontratacion", "fiduciario", "fiduciante", "fiduciantes",
        "rendicion cuentas fiduciario", "remocion fiduciario",
        "transmision posicion fiduciante", "fideicomisario",
        "cesion cuotaparte", "fideicomiso testamentario",
        "multiproyecto fideicomiso",
    ),
    "construccion": (
        "construccion", "obra", "rubros", "modalidad contratacion",
        "ajuste alzado", "costo + honorarios", "llave en mano",
        "certificacion", "redeterminacion", "fondo reparo", "vicios",
        "ruina", "garantias construccion", "higiene seguridad",
        "decreto 911", "final de obra", "documentacion obra",
        "rendimiento", "rendimientos", "demolicion", "rcd",
        # Patología constructor (capa experta)
        "constructor en problemas", "contratista en problemas",
        "contratista quiebra", "contratista concurso", "abandono obra",
        "abandono de obra", "mora contratista", "default contratista",
        "sobrefacturacion", "sobreprecio", "certificacion inflada",
        "sobre certificacion", "avance papel", "avance real",
        "fraude obra", "step in", "step-in", "reemplazo contratista",
        "retencion solidaria", "garantia fiel cumplimiento",
        "claims preventivos", "telegrama intimacion constructor",
        "paralizacion obra", "parada de obra", "art 1083 obra",
        "art 1086 obra", "locacion de obra", "interdicto obra",
        "embargo obra", "acopio en riesgo", "propiedad materiales",
        "subcontratista no pagado",
        # Posventa / vicios aplicado (capa experta)
        "posventa", "posventa inmueble", "posventa patologica",
        "reclamo posventa", "vicios ocultos", "vicios redhibitorios",
        "vicio oculto", "vicio manifiesto", "art 1051", "art 1054",
        "art 1057", "art 1059", "art 1273", "10 anos ruina",
        "ruina decenal", "solidaridad ruina", "proyectista responsable",
        "director tecnico responsable", "fabricantes elementos esenciales",
        "garantia constructor", "1 ano manifestacion vicio",
        "prescripcion vicios 3 anos", "manifestacion del vicio",
        "fisuras", "fisuras inmueble", "humedad", "humedades",
        "humedad inmueble", "capilaridad", "filtracion", "filtraciones",
        "asentamiento diferencial", "aluminosis",
        "oxidacion hierro", "hormigon defectuoso", "carpinteria",
        "ascensor falla", "ph reglamento posventa",
        "expensas extraordinarias posventa", "fondo de garantia",
        "hold back postventa", "seguro decenal", "seguro post obra",
        "redhibitoria", "quanti minoris", "accion redhibitoria",
        "accion quanti minoris", "accion cumplimiento posventa",
        "perito de parte", "dictamen vicios", "reparacion vs restitucion",
        "recepcion provisoria", "recepcion definitiva",
        "observaciones recepcion", "plan inspeccion ensayo",
        "ensayos no destructivos", "defensa constructor posventa",
        "defensa developer posventa", "art 1275",
        "ruina por causa externa", "exoneracion constructor",
    ),
    "financiero": (
        "financiamiento", "financiacion", "credito", "creditos", "hipoteca",
        "hipotecario", "prestamo", "cuota", "cuotas", "tasa", "tasas",
        "interes", "rentabilidad", "roi", "tir", "van", "npv", "irr",
        "payback", "retorno", "inversion", "capital", "flujo", "caja",
        "cashflow", "yield", "uva", "apalancamiento", "leverage", "ltv",
        "ltc", "dscr", "estructura capital", "capital stack",
        "waterfall", "preferred", "carry", "promote", "metrica",
        "metricas", "equity multiple", "sensibilidad", "monte carlo",
        "fci", "fondo comun", "hipoteca uva",
    ),
    "comercial": (
        "comercial", "comercializacion", "marketing", "ventas", "venta",
        "pricing", "precio lanzamiento", "pozo", "preventa", "ladder",
        "mix", "tipologias", "embudo", "lead", "leads", "conversion",
        "posventa", "segmentacion", "persona", "personas comprador",
        "crm", "tokko", "hubspot", "whatsapp", "meta ads", "google ads",
        "seo", "portal", "portales", "tasacion previa", "customer journey",
        "booking", "reserva", "seña", "boleto", "escritura",
    ),
    "macro": (
        "macro", "macroeconomia", "inflacion", "fx", "dolar", "mep", "ccl",
        "blue", "brecha", "tasa bcra", "politica monetaria",
        "politica fiscal", "deficit", "deuda publica", "indec",
        "bcra", "ipc", "icc", "cer", "ciclos", "escenarios", "riesgo pais",
        "embi",
    ),
    "triple-impacto": (
        "triple impacto", "esg", "sustentable", "sustentabilidad",
        "leed", "edge", "breeam", "well", "iram", "huella carbono",
        "embodied carbon", "net zero", "circular", "circulacion",
        "circular construction", "ndc", "acuerdo paris",
        "eficiencia energetica", "accesibilidad", "b corp", "iris",
        "etiquetado", "27520",
    ),
    "estrategia": (
        "estrategia", "modelo negocio", "modelos producto", "bts", "btr",
        "multifamily", "coliving", "alquiler temporario", "senior living",
        "student housing", "logistica", "oficinas", "industrial",
        "hotel", "retail", "joint venture", "jv", "permuta", "riesgos",
        "gestion riesgos", "decision framework", "fondeo institucional",
        "club deal", "family office", "ppp", "distrito tecnologico",
        "distrito audiovisual", "distrito diseno", "distrito artes",
        "distrito deportivo", "puerto madero",
    ),
    "tasacion": (
        "tasacion", "valuacion", "tasador", "comparativo", "residual",
        "capitalizacion", "tribunal tasaciones", "ttn", "cpau", "cpic",
        "normas profesionales tasacion", "metodo residual", "fair value",
    ),
    "suelo-dominio": (
        "suelo", "dominio", "due diligence", "informe dominio", "certificado",
        "boleto", "compraventa", "1170", "cesion", "escritura", "rpi",
        "17801", "prehorizontalidad", "2070", "usucapion", "prescripcion",
        "expropiacion", "21499", "tierras rurales", "26737", "rntr",
        # DD integral protocolo (capa experta)
        "due diligence integral", "dd integral", "dd pre compra",
        "protocolo dd", "comprar inmueble checklist",
        "comprar terreno checklist", "red flags compra",
        "condiciones suspensivas boleto", "escrow",
        "certificado libre deuda", "libre deuda municipal",
        "libre deuda arba", "libre deuda agip", "deuda expensas",
        "inhibiciones", "ihi", "certificado uif compra", "dd uif",
        "sucesion vendedor", "condominio vendedor",
        "fideicomiso vendedor", "sociedad vendedora", "poder vigente",
        "reglamento copropiedad", "ocupantes precarios", "intrusos",
        "comodato verbal", "locatario vigente", "plano municipal",
        "plano catastral", "diferencia superficie", "sobre edificacion",
        "sub edificacion", "antecedentes 20 anos",
        # Compra terreno DD (capa experta)
        "compra terreno", "dd terreno", "zonificacion verificar",
        "altura permitida", "perfil edilicio", "aph",
        "area proteccion historica", "expropiacion futura",
        "ensanche calle", "derecho de via", "servidumbres",
        "servidumbre administrativa", "servidumbre paso",
        "servidumbre acueducto", "zona seguridad frontera",
        "ley 23554", "decreto 887 fronteras", "aptitud agronomica",
        "estudio suelos", "sondeo spt", "spt", "capacidad portante",
        "napa freatica", "agua subterranea", "riesgo hidrico",
        "cota ign", "drenaje", "suelos contaminados",
        "pasivo ambiental", "fase 1 ambiental", "fase 2 ambiental",
        "phase 1 esa", "phase 2 esa", "eia",
        "evaluacion impacto ambiental", "dia declaracion impacto",
        "audiencia publica ambiental", "ley 24051",
        "residuos peligrosos", "tanques enterrados",
        "estacion servicio", "agroquimicos", "frigorificos",
        "bosques nativos", "ley 26331", "otbn", "humedales",
        "linea ribera", "factibilidad agua", "factibilidad cloaca",
        "factibilidad gas", "factibilidad red", "cesion publica",
        "transferencia capacidad constructiva", "mensura",
        "subdivision parcela", "loteo", "urbanizacion privada",
        "agrimensor matriculado", "plano subdivision", "npi",
        # Cadena dominial trampas (capa experta)
        "cadena dominial", "estudio de titulos", "saneamiento titulo",
        "titulo perfecto", "titulo imperfecto", "titulo precario",
        "saltos cadena dominial", "tracto sucesivo", "tracto abreviado",
        "art 33 ley 17801", "declaratoria herederos no inscripta",
        "herederos no firmantes", "cesion hereditaria",
        "sucesion en tramite", "accion de reduccion", "art 2453",
        "donacion previa", "donacion saneada", "10 anos donacion",
        "ley 24374", "regularizacion dominial",
        "titulo 24374", "usucapion sentencia inscripta",
        "sociedad disuelta cadena", "fiduciario sin facultades",
        "fiduciario vencido", "gravamen no cancelado",
        "hipoteca prescripta inscripta", "bien de familia inscripto",
        "art 244", "vivienda afectada", "transmision por subasta",
        "subasta judicial titulo", "tercero adquirente buena fe",
        "art 392", "fraude pauliana", "art 338",
        "concurso vendedor periodo sospecha", "art 116 lcq",
        "title insurance", "seguro titulo", "offshore cadena",
        "beneficiario final", "multipropiedad ph",
    ),
    "arquitectura": (
        "arquitectura", "ingenieria", "programa", "anteproyecto",
        "proyecto ejecutivo", "honorarios", "cirsoc", "hormigon armado",
        "acero", "mamposteria", "estudio suelos", "spt", "cpt",
        "geotecnia", "fundaciones", "pilotes", "platea", "sismicidad",
        "inpres", "103", "instalaciones", "electrica", "sanitaria",
        "gas", "hvac", "incendio", "aea 90364", "aysa", "enargas",
        "metrogas", "edenor", "edesur", "bim", "revit", "ifc", "lod",
        "eficiencia planta", "factor k",
    ),
    "costos": (
        "costo", "costos", "presupuesto", "presupuestos", "apu",
        "analisis precios unitarios", "computo metrico", "estructura costos",
        "hard cost", "soft cost", "indirectos", "gerenciamiento",
        "curva s", "cronograma", "gantt", "indice", "indices costo",
        "icc", "cac", "ipc", "uva", "contingencia", "imprevistos",
        "buffer", "earned value", "evm", "cpi", "spi", "desvio",
        "control presupuestario", "redeterminacion", "m2", "metro cuadrado",
    ),
    "tecnologia": (
        "proptech", "tecnologia", "ia", "inteligencia artificial",
        "avm", "lead scoring", "chatbot", "generativa", "automatizacion",
        "zapier", "make", "n8n", "webhook", "scraping", "datos",
        "bi", "dashboard", "tokenizacion", "blockchain", "smart contract",
        "security token", "gemelo digital", "iot", "vr", "ar", "metaverso",
        "drone", "robotica", "frontier",
    ),
    "uif": (
        "uif", "blanqueo", "25246", "lavado", "lavado activos", "kyc",
        "ddc", "origen fondos", "perfil cliente", "pep", "persona expuesta",
        "ros", "sujeto obligado", "21/2018", "28/2018", "escribano",
        "inmobiliaria", "beneficiario final", "27260", "27743",
        "sinceramiento", "blanqueos",
    ),
    "cnv-bcra": (
        "cnv", "26831", "27440", "vehiculos cnv", "ff", "fideicomiso financiero",
        "fci cerrado", "on", "obligaciones negociables", "cedear", "reit",
        "oferta publica", "prospecto", "road show", "ipo", "securitizacion",
        "cepo", "mulc", "decreto 609", "comunicacion bcra", "mep", "ccl",
        "contado con liquidacion", "al30", "gd30", "stablecoin", "psav",
        "cripto", "usdt", "usdc", "27739", "1010/2024",
    ),
    "seguros": (
        "seguro", "seguros", "ssn", "20091", "17418", "22400", "productor",
        "trc", "todo riesgo construccion", "car", "ear", "leg 2", "leg 3",
        "responsabilidad civil", "rc", "rc obra", "rc cruzada", "rc profesional",
        "e&o", "art", "24557", "decreto 911", "caucion", "garantia",
        "anticipo", "fondo reparo", "hogar", "consorcio", "copropiedad",
        "integral", "edificio",
    ),
    "casos": (
        "caso", "casos", "caso estudio", "caso de estudio", "ejemplo concreto",
        "edificio residencial amba", "oficinas puerto madero",
        "btr multifamily amba", "logistica zona este", "hotel boutique recoleta",
        "barrio cerrado pba", "club de campo", "suburban", "case study",
    ),
    "meta": (
        # `meta` no se rutea por keywords del user — siempre se incluye como
        # baseline obligatorio. Lo dejamos vacío para que `classify_query` no
        # lo elija nunca como dominio principal.
    ),
    "general": (
        # `general` es fallback explícito.
    ),
}


def _normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# Pre-normalize keyword sets al import.
DOMAIN_KEYWORDS: dict[Domain, frozenset[str]] = {
    domain: frozenset(_normalize(kw) for kw in kws)
    for domain, kws in _RAW_KEYWORDS.items()
}


def _count_matches(message_norm: str, message_tokens: set[str], kws: frozenset[str]) -> int:
    """
    Cuenta cuántas keywords del dominio aparecen en el mensaje.

    - Keywords single-word: matchean si el token está en el set tokenizado del
      mensaje (rápido, exacto).
    - Keywords multi-word (con espacios): matchean como substring sobre el
      mensaje normalizado (sin acentos, lowercase). Esto destraba frases
      como "cap rate", "net zero", "distrito tecnologico", "customer journey".
    """
    if not kws:
        return 0
    count = 0
    for kw in kws:
        if " " in kw:
            if kw in message_norm:
                count += 1
        elif kw in message_tokens:
            count += 1
    return count


# ============================================================
# Budgets de tokens
# ============================================================
# Heurística: 1 token ≈ 4 chars en español/inglés mezclados.
CHARS_PER_TOKEN = 4

# Budget total del contexto de KB inyectado al system prompt.
# Realista para que el chat tenga info útil sin reventar latencia/costo.
# 14k tokens ≈ 56k chars ≈ 50-60 KB de markdown.
MAX_CONTEXT_TOKENS = 14000
MAX_CONTEXT_CHARS = MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN

# Dentro de ese total, reservamos una porción para el baseline obligatorio
# del `_meta/` (reglas, índice, glosario, flujos por intención). El resto va
# a docs dinámicos.
META_BUDGET_CHARS = 32000  # ≈ 8000 tokens — incluye flujos por intención
DYNAMIC_BUDGET_CHARS = MAX_CONTEXT_CHARS - META_BUDGET_CHARS


# ============================================================
# Multi-domain classification
# ============================================================
def classify_query(message: str) -> Domain:
    """
    Devuelve el dominio con más matches de keywords.
    'meta' y 'general' nunca ganan por scoring — son baseline / fallback.
    Desempates: orden de `ALL_DOMAINS`.
    """
    tokens = set(_tokenize(message))
    if not tokens:
        return "general"
    message_norm = _normalize(message)

    best: Domain = "general"
    best_score = 0
    for domain in ALL_DOMAINS:
        if domain in ("general", "meta"):
            continue
        score = _count_matches(message_norm, tokens, DOMAIN_KEYWORDS[domain])
        if score > best_score:
            best_score = score
            best = domain

    return best if best_score > 0 else "general"


def classify_query_multi(message: str, top_n: int = 3) -> list[Domain]:
    """
    Devuelve hasta `top_n` dominios con matches > 0, ordenados por score desc.
    Útil para preguntas que tocan varios temas (ej: "fideicomiso al costo" =>
    impuestos + estrategia + comercial).
    """
    tokens = set(_tokenize(message))
    if not tokens:
        return []
    message_norm = _normalize(message)

    scored: list[tuple[Domain, int]] = []
    for domain in ALL_DOMAINS:
        if domain in ("general", "meta"):
            continue
        score = _count_matches(message_norm, tokens, DOMAIN_KEYWORDS[domain])
        if score > 0:
            scored.append((domain, score))

    scored.sort(key=lambda x: (-x[1], ALL_DOMAINS.index(x[0])))
    return [d for d, _ in scored[:top_n]]


def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


# ============================================================
# Selección de contexto para una pregunta
# ============================================================
async def select_context_for_message(
    message: str,
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> tuple[Domain, str]:
    """
    Compatible con el contrato anterior: devuelve `(domain, context_text)`.

    El context_text combina:
      1. Baseline _meta obligatorio (instrucciones-chat, politica-datos,
         indice-rapido, glosario, fuentes-oficiales) — siempre.
      2. Top-K docs del/los dominio(s) relevantes a la query.

    Si la búsqueda dinámica falla, devuelve solo el meta baseline.
    Si todo falla, devuelve "".
    """
    domain = classify_query(message)
    max_chars = max_tokens * CHARS_PER_TOKEN

    parts: list[str] = []
    remaining = max_chars

    # 1) Baseline meta — siempre intentamos cargarlo.
    # La query baseline prioriza las reglas operativas + routing del chat:
    # instrucciones, política de datos, índice rápido, flujos por intención.
    # `anti-patterns.md` queda fuera del baseline por tamaño (22KB compite con
    # flows-por-intencion 31KB en un budget de 32KB) — se carga dinámicamente
    # cuando la query del usuario contiene red flags (su frontmatter tiene
    # buenas keywords para que el ranking lo levante con boost 3×).
    try:
        meta_ctx = await knowledge_base.get_context(
            query="reglas instrucciones politica datos indice glosario flujos intencion routing",
            domain="_meta",
            max_chars=min(META_BUDGET_CHARS, remaining),
            top_k=8,
        )
    except Exception as e:
        logger.warning("Context router: meta baseline falló (%s)", e)
        meta_ctx = ""

    if meta_ctx:
        parts.append(meta_ctx)
        remaining -= len(meta_ctx)

    # 2) Contexto dinámico — uno o varios dominios.
    if remaining > 0:
        domains_multi = classify_query_multi(message, top_n=2)
        # Si nada matcheó, dejamos `domain=None` para búsqueda cross-bucket.
        target_folders: list[str | None]
        if domains_multi:
            target_folders = [DOMAIN_TO_FOLDER[d] for d in domains_multi]
        else:
            target_folders = [None]

        per_domain_budget = remaining // max(1, len(target_folders))

        for folder in target_folders:
            try:
                dyn_ctx = await knowledge_base.get_context(
                    query=message,
                    domain=folder if folder else None,
                    max_chars=per_domain_budget,
                    top_k=5,
                )
            except Exception as e:
                logger.warning("Context router: dynamic load falló (%s)", e)
                dyn_ctx = ""

            if dyn_ctx:
                parts.append(dyn_ctx)
                remaining -= len(dyn_ctx)
                if remaining <= 0:
                    break

    context = "\n\n---\n\n".join(p for p in parts if p)

    # Safety net por si acumulamos más de la cuenta.
    if len(context) > max_chars:
        context = context[:max_chars]

    return domain, context
