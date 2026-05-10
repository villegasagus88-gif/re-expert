"""
Maps service — planificación de rutas.

Si GOOGLE_MAPS_API_KEY está seteada, usa la Routes API (preferred) para
optimizar el orden y obtener tiempos. Sino devuelve un fallback razonable
(orden de entrada con leyenda de "no optimizado").
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


def _has_maps() -> bool:
    return bool(settings.GOOGLE_MAPS_API_KEY)


async def plan_route(
    origin: str, stops: list[str], return_to_origin: bool = False
) -> dict[str, Any]:
    if not stops:
        return {"error": "Tenés que pasar al menos 1 parada."}

    if not _has_maps():
        # Fallback: orden de entrada
        order = list(range(len(stops)))
        items = [{"index": i, "address": stops[i]} for i in order]
        return {
            "ok": True,
            "optimized": False,
            "origin": origin,
            "stops": items,
            "return_to_origin": return_to_origin,
            "note": (
                "Google Maps no está configurada. Devuelvo el orden tal cual; "
                "para optimización real, agregar GOOGLE_MAPS_API_KEY al .env."
            ),
        }

    # Routes API v2 con waypoint optimization
    body = {
        "origin": {"address": origin},
        "destination": {"address": stops[-1] if not return_to_origin else origin},
        "intermediates": [{"address": s} for s in (stops[:-1] if not return_to_origin else stops)],
        "travelMode": "DRIVE",
        "optimizeWaypointOrder": True,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.optimizedIntermediateWaypointIndex",
    }
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    try:
        async with httpx.AsyncClient(timeout=15) as cli:
            r = await cli.post(url, headers=headers, json=body)
            data = r.json()
            if r.status_code >= 400:
                return {"error": "google_maps_error", "detail": data}
        routes = data.get("routes") or []
        if not routes:
            return {"error": "no_route_found", "detail": data}
        rt = routes[0]
        order = rt.get("optimizedIntermediateWaypointIndex", list(range(len(stops) - (0 if return_to_origin else 1))))
        ordered = [stops[i] for i in order]
        if not return_to_origin:
            ordered.append(stops[-1])
        return {
            "ok": True,
            "optimized": True,
            "origin": origin,
            "stops": [{"index": i, "address": addr} for i, addr in enumerate(ordered)],
            "duration_seconds": rt.get("duration"),
            "distance_meters": rt.get("distanceMeters"),
            "return_to_origin": return_to_origin,
        }
    except Exception as e:
        logger.exception("Maps API failed")
        return {"error": str(e)}
