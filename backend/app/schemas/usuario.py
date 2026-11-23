from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validar_longitud_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar 72 bytes en UTF-8.")
    return password


class UsuarioBase(BaseModel):
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    correo: EmailStr
    telefono: str = Field(..., min_length=6, max_length=30)
    direccion: str = Field(..., min_length=5, max_length=250)
    rol: Literal["admin", "negocio", "comedor", "voluntario"]
    disponible: bool = False
    estado: Literal["activo", "inactivo"] = "activo"

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


RolDto = Literal["admin", "negocio", "comedor", "voluntario"]


class UsuarioCreate(UsuarioBase):
    rol: Literal["negocio", "comedor", "voluntario"]
    password: str = Field(..., min_length=6)

    @field_validator("password")
    @classmethod
    def validar_password(cls, password: str) -> str:
        return _validar_longitud_password(password)


class UsuarioUpdate(BaseModel):
    nombres: str | None = Field(default=None, min_length=2, max_length=100)
    apellidos: str | None = Field(default=None, min_length=2, max_length=100)
    correo: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)
    telefono: str | None = Field(default=None, min_length=6, max_length=30)
    direccion: str | None = Field(default=None, min_length=5, max_length=250)
    rol: Literal["admin", "negocio", "comedor", "voluntario"] | None = None
    estado: Literal["activo", "inactivo"] | None = None
    disponible: bool | None = None

    @field_validator("password")
    @classmethod
    def validar_password(cls, password: str | None) -> str | None:
        return _validar_longitud_password(password) if password is not None else None


class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str = Field(..., min_length=6)


class UsuarioOut(UsuarioBase):
    id: int


class UsuarioLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
