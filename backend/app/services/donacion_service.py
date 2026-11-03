from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException, status

from app.repositories.donacion_repository import DonacionRepository
from app.schemas.donacion import DonacionCreate, DonacionUpdate


class DonacionService:
    @staticmethod
    def registrar_donacion(datos: DonacionCreate) -> dict[str, Any]:
        if datos.fecha_vencimiento < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de vencimiento no puede ser anterior a hoy.",
            )
        return DonacionRepository.crear(datos.model_dump())

    @staticmethod
    def listar_donaciones() -> list[dict[str, Any]]:
        return DonacionRepository.listar()

    @staticmethod
    def buscar_por_id(donacion_id: int) -> dict[str, Any]:
        donacion = DonacionRepository.buscar_por_id(donacion_id)
        if not donacion:
            raise HTTPException(status_code=404, detail="Donación no encontrada.")
        return donacion

    @staticmethod
    def actualizar_donacion(donacion_id: int, datos: DonacionUpdate) -> dict[str, Any]:
        if not DonacionRepository.buscar_por_id(donacion_id):
            raise HTTPException(status_code=404, detail="Donación no encontrada.")

        cambios = datos.model_dump(exclude_unset=True)
        if "fecha_vencimiento" in cambios and cambios["fecha_vencimiento"] < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de vencimiento no puede ser anterior a hoy.",
            )

        actualizado = DonacionRepository.actualizar(donacion_id, cambios)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo actualizar la donación.")
        return actualizado

    @staticmethod
    def eliminar_donacion(donacion_id: int) -> dict[str, str]:
        if not DonacionRepository.buscar_por_id(donacion_id):
            raise HTTPException(status_code=404, detail="Donación no encontrada.")
        eliminado = DonacionRepository.eliminar(donacion_id)
        if not eliminado:
            raise HTTPException(status_code=400, detail="No se pudo cancelar la donación.")
        return {"mensaje": "Donación cancelada correctamente."}

    @staticmethod
    def listar_disponibles() -> list[dict[str, Any]]:
        return DonacionRepository.listar_disponibles()
