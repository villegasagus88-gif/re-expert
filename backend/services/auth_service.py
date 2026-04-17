"""
Auth service - proxies to Supabase Auth with business logic.

Supabase handles: password hashing (bcrypt), JWT generation, email uniqueness.
We handle: input validation, rate limiting, error translation, profile enrichment.
"""
import httpx
from fastapi import HTTPException, status

from config.settings import settings

SUPABASE_AUTH_URL = f"{settings.SUPABASE_URL}/auth/v1"
HEADERS = {
    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}


async def register_user(email: str, password: str, full_name: str) -> dict:
    """
    Register a new user via Supabase Auth Admin API.

    Returns dict with access_token, refresh_token, and user data.
    Raises HTTPException on failure (409 for duplicate email, etc.).
    """
    async with httpx.AsyncClient(timeout=10) as client:
        # Create user via Supabase Admin API
        resp = await client.post(
            f"{SUPABASE_AUTH_URL}/admin/users",
            headers=HEADERS,
            json={
                "email": email,
                "password": password,
                "email_confirm": True,  # Auto-confirm since we validate on our end
                "user_metadata": {"full_name": full_name},
            },
        )

        if resp.status_code == 422:
            body = resp.json()
            msg = body.get("msg", body.get("message", ""))
            if "already" in msg.lower() or "duplicate" in msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una cuenta con este email",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg or "Error de validación",
            )

        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error al comunicarse con el servicio de autenticación",
            )

        user_data = resp.json()

        # Now sign in to get JWT tokens
        sign_in_resp = await client.post(
            f"{SUPABASE_AUTH_URL}/token?grant_type=password",
            headers={"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )

        if sign_in_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Usuario creado pero error al generar sesión",
            )

        session = sign_in_resp.json()

        return {
            "access_token": session["access_token"],
            "refresh_token": session["refresh_token"],
            "user": {
                "id": user_data["id"],
                "email": user_data["email"],
                "full_name": user_data.get("user_metadata", {}).get("full_name"),
                "role": "user",
                "plan": "free",
            },
        }


async def login_user(email: str, password: str) -> dict:
    """
    Login via Supabase Auth. Returns tokens + user data.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{SUPABASE_AUTH_URL}/token?grant_type=password",
            headers={"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )

        if resp.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error al comunicarse con el servicio de autenticación",
            )

        session = resp.json()
        user = session.get("user", {})

        return {
            "access_token": session["access_token"],
            "refresh_token": session["refresh_token"],
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("user_metadata", {}).get("full_name"),
                "role": user.get("app_metadata", {}).get("role", "user"),
                "plan": "free",
            },
        }


async def update_profile(
    user_id: str,
    email: str,
    full_name: str | None = None,
    current_password: str | None = None,
    new_password: str | None = None,
) -> None:
    """
    Update user profile. If changing password, validates current password
    first by attempting a sign-in with Supabase.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        # If changing password, verify current password via sign-in
        if new_password and current_password:
            verify_resp = await client.post(
                f"{SUPABASE_AUTH_URL}/token?grant_type=password",
                headers={"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Content-Type": "application/json"},
                json={"email": email, "password": current_password},
            )
            if verify_resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Contrasena actual incorrecta",
                )

        # Build the update payload for Supabase Admin API
        update_data: dict = {}
        if new_password:
            update_data["password"] = new_password
        if full_name is not None:
            update_data["user_metadata"] = {"full_name": full_name}

        if update_data:
            resp = await client.put(
                f"{SUPABASE_AUTH_URL}/admin/users/{user_id}",
                headers=HEADERS,
                json=update_data,
            )
            if resp.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Error al actualizar perfil en el servicio de autenticacion",
                )


async def refresh_session(refresh_token: str) -> dict:
    """
    Exchange a refresh_token for a new access_token + refresh_token.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{SUPABASE_AUTH_URL}/token?grant_type=refresh_token",
            headers={"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Content-Type": "application/json"},
            json={"refresh_token": refresh_token},
        )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado",
            )

        session = resp.json()
        user = session.get("user", {})

        return {
            "access_token": session["access_token"],
            "refresh_token": session["refresh_token"],
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("user_metadata", {}).get("full_name"),
                "role": user.get("app_metadata", {}).get("role", "user"),
                "plan": "free",
            },
        }
