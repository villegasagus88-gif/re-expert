"""
Schemas de facturación.

Lo único que el frontend manda de una tarjeta es el **token** que generó el SDK
de Mercado Pago en el navegador. No hay —ni puede haber— un schema con número
de tarjeta, vencimiento o código de seguridad: esos datos van del navegador
directo a MP y nunca pasan por este backend.
"""
from pydantic import BaseModel, Field


class CardTokenRequest(BaseModel):
    """Token de un solo uso devuelto por el SDK de Mercado Pago."""

    card_token: str = Field(..., min_length=8, max_length=128)


class CardTokenOpcional(BaseModel):
    """
    Token opcional: hace falta sólo si hay una suscripción viva que apuntar a
    otra tarjeta (MP exige el código de seguridad para generarlo). Sin
    suscripción, cambiar la tarjeta principal es sólo una preferencia nuestra.
    """

    card_token: str | None = Field(None, min_length=8, max_length=128)
