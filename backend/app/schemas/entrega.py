from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class EntregaBase(BaseModel):
    solicitud_id: int
    voluntario_id: int
    fecha_asignacion: date
    fecha_entrega: date | None = None
    estado: Literal["abierta", "aceptada", "recogida", "entregada", "cancelada"] = "abierta"
    observaciones: str | None = Field(default=None, max_length=300)
    tipo_apoyo: Literal["recoger", "trasladar", "ambos"] = "ambos"
    tipo: Literal["recoger", "trasladar", "ambos"] = "ambos"


class EntregaCreate(EntregaBase):
    pass


class EntregaUpdate(BaseModel):
    solicitud_id: int | None = None
    voluntario_id: int | None = None
    fecha_asignacion: date | None = None
    fecha_entrega: date | None = None
    estado: Literal["abierta", "aceptada", "recogida", "entregada", "cancelada"] | None = None
    observaciones: str | None = Field(default=None, max_length=300)
    tipo_apoyo: Literal["recoger", "trasladar", "ambos"] | None = None
    tipo: Literal["recoger", "trasladar", "ambos"] | None = None


class EntregaOut(EntregaBase):
    id: int
    telefono_negocio: str | None = None
    telefono_comedor: str | None = None
    direccion_recojo: str | None = None
    cantidad: int | None = None
    unidad: str | None = None
    hora_disponible: str | None = None


class EntregaEstadoUpdate(BaseModel):
    estado: Literal["abierta", "aceptada", "recogida", "entregada", "cancelada"]
