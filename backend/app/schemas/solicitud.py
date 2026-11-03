from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SolicitudBase(BaseModel):
    donacion_id: int
    comedor_id: int
    cantidad_solicitada: int = Field(..., gt=0)
    estado: Literal["pendiente", "aprobada", "rechazada", "cancelada"] = "pendiente"


class SolicitudCreate(SolicitudBase):
    pass


class SolicitudUpdate(BaseModel):
    donacion_id: int | None = None
    comedor_id: int | None = None
    cantidad_solicitada: int | None = Field(default=None, gt=0)
    estado: Literal["pendiente", "aprobada", "rechazada", "cancelada"] | None = None


class SolicitudOut(SolicitudBase):
    id: int


class SolicitudEstadoUpdate(BaseModel):
    estado: Literal["pendiente", "aprobada", "rechazada", "cancelada"]
