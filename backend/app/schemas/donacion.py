from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class DonacionBase(BaseModel):
    nombre_alimento: str = Field(..., min_length=2)
    descripcion: str = Field(..., min_length=5)
    cantidad: int = Field(..., gt=0)
    unidad: str = Field(..., min_length=1)
    fecha_vencimiento: date
    direccion_recojo: str = Field(..., min_length=5)
    hora_disponible: str = Field(..., min_length=3)
    estado: Literal["disponible", "reservada", "cancelada", "entregada"] = "disponible"
    usuario_negocio_id: int


class DonacionCreate(DonacionBase):
    pass


class DonacionUpdate(BaseModel):
    nombre_alimento: str | None = Field(default=None, min_length=2)
    descripcion: str | None = Field(default=None, min_length=5)
    cantidad: int | None = Field(default=None, gt=0)
    unidad: str | None = Field(default=None, min_length=1)
    fecha_vencimiento: date | None = None
    direccion_recojo: str | None = Field(default=None, min_length=5)
    hora_disponible: str | None = Field(default=None, min_length=3)
    estado: Literal["disponible", "reservada", "cancelada", "entregada"] | None = None
    usuario_negocio_id: int | None = None


class DonacionOut(DonacionBase):
    id: int
