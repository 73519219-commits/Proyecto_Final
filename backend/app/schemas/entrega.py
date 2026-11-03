from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class EntregaBase(BaseModel):
    solicitud_id: int
    voluntario_id: int
    fecha_asignacion: date
    fecha_entrega: date | None = None
    estado: Literal["pendiente", "asignada", "en_transito", "entregada", "cancelada"] = "pendiente"
    observaciones: str | None = Field(default=None, max_length=300)


class EntregaCreate(EntregaBase):
    pass


class EntregaUpdate(BaseModel):
    solicitud_id: int | None = None
    voluntario_id: int | None = None
    fecha_asignacion: date | None = None
    fecha_entrega: date | None = None
    estado: Literal["pendiente", "asignada", "en_transito", "entregada", "cancelada"] | None = None
    observaciones: str | None = Field(default=None, max_length=300)


class EntregaOut(EntregaBase):
    id: int


class EntregaEstadoUpdate(BaseModel):
    estado: Literal["pendiente", "asignada", "en_transito", "entregada", "cancelada"]
