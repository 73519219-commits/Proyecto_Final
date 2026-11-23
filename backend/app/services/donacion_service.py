from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException, status

from app.repositories.donacion_repository import (
    DonacionRepository,
    DonacionRevisionError,
)
from app.schemas.donacion import DonacionCreate, DonacionUpdate
from app.repositories.usuario_repository import UsuarioRepository


class DonacionService:
    @staticmethod
    def registrar_donacion(datos: DonacionCreate) -> dict[str, Any]:
        if datos.fecha_vencimiento < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de vencimiento no puede ser anterior a hoy.",
            )
        negocio = UsuarioRepository.buscar_por_id(datos.usuario_negocio_id)
        if not negocio or negocio.get("rol") != "negocio" or negocio.get("estado") != "activo":
            raise HTTPException(
                status_code=400,
                detail="La donación debe pertenecer a un negocio activo.",
            )
        if datos.estado != "disponible":
            raise HTTPException(
                status_code=422,
                detail="Una donación nueva debe comenzar en estado disponible.",
            )
        return DonacionRepository.crear(datos.model_dump(mode="json"))

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
        donacion = DonacionRepository.buscar_por_id(donacion_id)
        if not donacion:
            raise HTTPException(status_code=404, detail="Donación no encontrada.")

        cambios = datos.model_dump(exclude_unset=True, mode="json")
        estado = cambios.pop("estado", None)
        propietario = cambios.get("usuario_negocio_id")
        if propietario is not None and propietario != donacion["usuario_negocio_id"]:
            if DonacionRepository.tiene_solicitudes(donacion_id):
                raise HTTPException(
                    status_code=409,
                    detail="No se puede transferir una donación que ya tiene solicitudes.",
                )
            negocio = UsuarioRepository.buscar_por_id(propietario)
            if not negocio or negocio.get("rol") != "negocio" or negocio.get("estado") != "activo":
                raise HTTPException(
                    status_code=400,
                    detail="La donación debe pertenecer a un negocio activo.",
                )

        if "cantidad" in cambios:
            total_aprobado = DonacionRepository.total_aprobado(donacion_id)
            if cambios["cantidad"] < total_aprobado:
                raise HTTPException(
                    status_code=409,
                    detail="La cantidad no puede ser menor que la suma de solicitudes aprobadas.",
                )
        if (
            "fecha_vencimiento" in cambios
            and cambios["fecha_vencimiento"] < date.today().isoformat()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de vencimiento no puede ser anterior a hoy.",
            )

        if estado is not None:
            if cambios:
                raise HTTPException(
                    status_code=422,
                    detail="Actualice los datos de la donación y su estado en operaciones separadas.",
                )
            if estado == "cancelada":
                DonacionService.eliminar_donacion(donacion_id)
                return DonacionRepository.buscar_por_id(donacion_id) or {
                    **donacion,
                    "estado": "cancelada",
                }
            if estado == "entregada":
                try:
                    DonacionRepository.marcar_entregada_atomica(donacion_id)
                except DonacionRevisionError as error:
                    raise HTTPException(
                        status_code=error.status_code,
                        detail=error.detail,
                    ) from error
                return DonacionRepository.buscar_por_id(donacion_id) or {
                    **donacion,
                    "estado": "entregada",
                }
            if estado != donacion["estado"]:
                raise HTTPException(
                    status_code=409,
                    detail="El estado de la donación solo cambia mediante el flujo de solicitudes y entregas.",
                )

        if not cambios:
            return donacion
        actualizado = DonacionRepository.actualizar(donacion_id, cambios)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo actualizar la donación.")
        return actualizado

    @staticmethod
    def eliminar_donacion(donacion_id: int) -> dict[str, str]:
        try:
            DonacionRepository.cancelar_atomica(donacion_id)
        except DonacionRevisionError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error
        return {"mensaje": "Donación cancelada correctamente."}

    @staticmethod
    def listar_disponibles() -> list[dict[str, Any]]:
        return DonacionRepository.listar_disponibles()
