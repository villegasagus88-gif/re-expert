"""
Auth request/response schemas with validation.
"""
import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una letra mayúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Debe contener al menos un número")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str = "user"
    plan: str = "free"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    new_password: str | None = Field(None, min_length=8, max_length=128)
    current_password: str | None = Field(None, min_length=1)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una letra mayuscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Debe contener al menos un numero")
        return v

    def model_post_init(self, __context) -> None:
        if self.new_password and not self.current_password:
            raise ValueError("current_password es requerido para cambiar la contrasena")
        if not self.full_name and not self.new_password:
            raise ValueError("Debes enviar al menos full_name o new_password")


# Rebuild model refs
AuthResponse.model_rebuild()
