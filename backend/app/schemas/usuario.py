from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    nombres: str = Field(..., min_length=2)
    apellidos: str = Field(..., min_length=2)
    correo: EmailStr
    telefono: str = Field(..., min_length=6)
    direccion: str = Field(..., min_length=5)
    rol: Literal["admin", "negocio", "comedor", "voluntario"]
    estado: Literal["activo", "inactivo"] = "activo"

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6)


class UsuarioUpdate(BaseModel):
    nombres: str | None = Field(default=None, min_length=2)
    apellidos: str | None = Field(default=None, min_length=2)
    correo: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)
    telefono: str | None = Field(default=None, min_length=6)
    direccion: str | None = Field(default=None, min_length=5)
    rol: Literal["admin", "negocio", "comedor", "voluntario"] | None = None
    estado: Literal["activo", "inactivo"] | None = None


class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str = Field(..., min_length=6)


class UsuarioOut(UsuarioBase):
    id: int


class UsuarioLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
