from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException, status

from app.repositories.donacion_repository import DonacionRepository
from app.repositories.solicitud_repository import SolicitudRepository
from app.schemas.solicitud import SolicitudCreate, SolicitudUpdate


class SolicitudService:
    @staticmethod
    def registrar_solicitud(datos: SolicitudCreate) -> dict[str, Any]:
        donacion = DonacionRepository.buscar_por_id(datos.donacion_id)
        if not donacion:
            raise HTTPException(status_code=404, detail="La donación no existe.")
        if donacion.get("estado") != "disponible":
            raise HTTPException(status_code=400, detail="La donación no está disponible.")
        if donacion.get("fecha_vencimiento") and donacion["fecha_vencimiento"] < str(date.today()):
            raise HTTPException(status_code=400, detail="La donación ya venció.")
        if datos.cantidad_solicitada > donacion["cantidad"]:
            raise HTTPException(
                status_code=400,
                detail="La cantidad solicitada supera la cantidad disponible.",
            )

        return SolicitudRepository.crear(datos.model_dump())

    @staticmethod
    def listar_solicitudes() -> list[dict[str, Any]]:
        return SolicitudRepository.listar()

    @staticmethod
    def buscar_por_id(solicitud_id: int) -> dict[str, Any]:
        solicitud = SolicitudRepository.buscar_por_id(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        return solicitud

    @staticmethod
    def actualizar_solicitud(solicitud_id: int, datos: SolicitudUpdate) -> dict[str, Any]:
        if not SolicitudRepository.buscar_por_id(solicitud_id):
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        cambios = datos.model_dump(exclude_unset=True)
        actualizado = SolicitudRepository.actualizar(solicitud_id, cambios)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo actualizar la solicitud.")
        return actualizado

    @staticmethod
    def cambiar_estado(solicitud_id: int, estado: str) -> dict[str, Any]:
        solicitud = SolicitudRepository.buscar_por_id(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        solicitud["estado"] = estado
        actualizado = SolicitudRepository.actualizar(solicitud_id, solicitud)
        return actualizado

    @staticmethod
    def cancelar_solicitud(solicitud_id: int) -> dict[str, str]:
        if not SolicitudRepository.buscar_por_id(solicitud_id):
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        cancelada = SolicitudRepository.eliminar(solicitud_id)
        if not cancelada:
            raise HTTPException(status_code=400, detail="No se pudo cancelar la solicitud.")
        return {"mensaje": "Solicitud cancelada correctamente."}

    @staticmethod
    def listar_por_comedor(comedor_id: int) -> list[dict[str, Any]]:
        return SolicitudRepository.listar_por_comedor(comedor_id)
