from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SolicitudBase(BaseModel):
    donacion_id: int
    comedor_id: int
    cantidad_solicitada: int = Field(..., gt=0)
    tipo_apoyo: Literal["recoger", "trasladar", "ambos"] = "ambos"
    necesita_apoyo: Literal["recoger", "trasladar", "ambos"] = "ambos"
    estado: Literal["pendiente", "aprobada", "rechazada", "cancelada"] = "pendiente"


class SolicitudCreate(SolicitudBase):
    estado: Literal["pendiente"] = "pendiente"


class SolicitudUpdate(BaseModel):
    donacion_id: int | None = None
    comedor_id: int | None = None
    cantidad_solicitada: int | None = Field(default=None, gt=0)
    tipo_apoyo: Literal["recoger", "trasladar", "ambos"] | None = None
    necesita_apoyo: Literal["recoger", "trasladar", "ambos"] | None = None
    estado: Literal["pendiente", "aprobada", "rechazada", "cancelada"] | None = None


class SolicitudOut(SolicitudBase):
    id: int
    telefono_negocio: str | None = None
    telefono_comedor: str | None = None


class SolicitudEstadoUpdate(BaseModel):
    estado: Literal["pendiente", "aprobada", "rechazada", "cancelada"]


class SolicitudAprobacionUpdate(BaseModel):
    tipo_apoyo: Literal["recoger", "trasladar", "ambos"] | None = None
    necesita_apoyo: Literal["recoger", "trasladar", "ambos"] | None = None
