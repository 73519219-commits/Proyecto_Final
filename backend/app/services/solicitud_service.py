from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException, status

from app.repositories.donacion_repository import DonacionRepository
from app.repositories.solicitud_repository import (
    SolicitudRepository,
    SolicitudRevisionError,
)
from app.repositories.usuario_repository import UsuarioRepository
from app.services.aviso_service import AvisoService
from app.schemas.solicitud import SolicitudCreate, SolicitudUpdate


class SolicitudService:
    @staticmethod
    def filtrar_telefonos(
        solicitudes: list[dict[str, Any]],
        usuario_actual: dict[str, Any],
    ) -> list[dict[str, Any]]:
        resultado: list[dict[str, Any]] = []
        for solicitud in solicitudes:
            visible = solicitud.get("estado") == "aprobada"
            if visible and usuario_actual["rol"] == "admin":
                pass
            elif (
                visible
                and usuario_actual["rol"] == "comedor"
                and solicitud["comedor_id"] == usuario_actual["id"]
            ):
                pass
            elif (
                visible
                and usuario_actual["rol"] == "negocio"
                and solicitud.get("usuario_negocio_id") == usuario_actual["id"]
            ):
                pass
            else:
                solicitud = {
                    **solicitud,
                    "telefono_negocio": None,
                    "telefono_comedor": None,
                }
            resultado.append(solicitud)
        return resultado
    @staticmethod
    def registrar_solicitud(datos: SolicitudCreate) -> dict[str, Any]:
        comedor = UsuarioRepository.buscar_por_id(datos.comedor_id)
        if not comedor or comedor.get("rol") != "comedor" or comedor.get("estado") != "activo":
            raise HTTPException(
                status_code=400,
                detail="La solicitud debe pertenecer a un comedor activo.",
            )
        donacion = DonacionRepository.buscar_por_id(datos.donacion_id)
        if not donacion:
            raise HTTPException(status_code=404, detail="La donación no existe.")
        negocio = UsuarioRepository.buscar_por_id(donacion["usuario_negocio_id"])
        if not negocio or negocio.get("rol") != "negocio" or negocio.get("estado") != "activo":
            raise HTTPException(
                status_code=409,
                detail="La donación no pertenece a un negocio activo.",
            )
        if donacion.get("estado") != "disponible":
            raise HTTPException(status_code=400, detail="La donación no está disponible.")
        fecha_vencimiento = donacion.get("fecha_vencimiento")
        if fecha_vencimiento and str(fecha_vencimiento) < date.today().isoformat():
            raise HTTPException(status_code=400, detail="La donación ya venció.")
        if datos.cantidad_solicitada > donacion["cantidad"]:
            raise HTTPException(
                status_code=400,
                detail="La cantidad solicitada supera la cantidad disponible.",
            )

        creada = SolicitudRepository.crear(datos.model_dump())
        AvisoService.crear(
            donacion["usuario_negocio_id"],
            "solicitud_creada",
            "Un comedor creó una solicitud sobre tu donación.",
            creada["id"],
        )
        return creada

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
        solicitud = SolicitudRepository.buscar_por_id(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        cambios = datos.model_dump(exclude_unset=True)
        if "estado" in cambios or "donacion_id" in cambios or "comedor_id" in cambios:
            raise HTTPException(
                status_code=422,
                detail="No se puede cambiar el estado ni las relaciones de una solicitud por PUT.",
            )
        if solicitud["estado"] != "pendiente":
            raise HTTPException(
                status_code=409,
                detail="Solo se pueden editar solicitudes pendientes.",
            )
        donacion = DonacionRepository.buscar_por_id(solicitud["donacion_id"])
        if not donacion:
            raise HTTPException(status_code=409, detail="La donación asociada ya no existe.")
        cantidad = cambios.get("cantidad_solicitada", solicitud["cantidad_solicitada"])
        if cantidad > donacion["cantidad"]:
            raise HTTPException(
                status_code=400,
                detail="La cantidad solicitada supera la cantidad disponible.",
            )
        actualizado = SolicitudRepository.actualizar(solicitud_id, cambios)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo actualizar la solicitud.")
        return actualizado

    @staticmethod
    def cambiar_estado(solicitud_id: int, estado: str) -> dict[str, Any]:
        solicitud = SolicitudRepository.buscar_por_id(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        if estado == solicitud["estado"]:
            return solicitud
        if estado != "cancelada":
            raise HTTPException(
                status_code=403,
                detail="El estado solo puede cambiar mediante las transiciones del flujo.",
            )
        SolicitudService.cancelar_solicitud(solicitud_id)
        return SolicitudRepository.buscar_por_id(solicitud_id) or {
            **solicitud,
            "estado": "cancelada",
        }

    @staticmethod
    def cancelar_solicitud(solicitud_id: int) -> dict[str, str]:
        solicitud = SolicitudRepository.buscar_por_id(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        if solicitud["estado"] not in {"pendiente", "aprobada"}:
            raise HTTPException(
                status_code=409,
                detail=f"No se puede cancelar una solicitud en estado '{solicitud['estado']}'.",
            )
        try:
            SolicitudRepository.cancelar_atomica(solicitud_id)
        except SolicitudRevisionError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error
        return {"mensaje": "Solicitud cancelada correctamente."}

    @staticmethod
    def listar_por_comedor(comedor_id: int) -> list[dict[str, Any]]:
        return SolicitudRepository.listar_por_comedor(comedor_id)

    @staticmethod
    def listar_por_negocio(negocio_id: int) -> list[dict[str, Any]]:
        return SolicitudRepository.listar_por_negocio(negocio_id)

    @staticmethod
    def aprobar(solicitud_id: int, negocio_id: int, tipo_apoyo: str | None) -> dict[str, Any]:
        solicitud = SolicitudRepository.buscar_por_id(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        if solicitud["estado"] != "pendiente":
            raise HTTPException(status_code=409, detail="La solicitud ya fue revisada.")
        donacion = DonacionRepository.buscar_por_id(solicitud["donacion_id"])
        if not donacion or donacion["usuario_negocio_id"] != negocio_id:
            raise HTTPException(status_code=403, detail="Solo el negocio donante puede aprobar la solicitud.")
        if donacion.get("estado") not in {"disponible", "reservada"}:
            raise HTTPException(status_code=409, detail="La donación no está disponible.")
        fecha_vencimiento = donacion.get("fecha_vencimiento")
        if fecha_vencimiento and str(fecha_vencimiento) < date.today().isoformat():
            raise HTTPException(status_code=400, detail="La donación ya venció.")

        apoyo = tipo_apoyo or solicitud.get("necesita_apoyo") or solicitud.get("tipo_apoyo") or "ambos"
        try:
            SolicitudRepository.aprobar_atomica(solicitud_id, negocio_id, apoyo)
        except SolicitudRevisionError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error
        AvisoService.crear(
            solicitud["comedor_id"],
            "solicitud_aprobada",
            "Tu solicitud fue aprobada por el negocio.",
            solicitud_id,
        )
        return SolicitudRepository.buscar_por_id(solicitud_id) or solicitud

    @staticmethod
    def rechazar(solicitud_id: int, negocio_id: int) -> dict[str, Any]:
        solicitud = SolicitudRepository.buscar_por_id(solicitud_id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        if solicitud["estado"] != "pendiente":
            raise HTTPException(status_code=409, detail="La solicitud ya fue revisada.")
        donacion = DonacionRepository.buscar_por_id(solicitud["donacion_id"])
        if not donacion or donacion["usuario_negocio_id"] != negocio_id:
            raise HTTPException(status_code=403, detail="Solo el negocio donante puede rechazar la solicitud.")
        try:
            SolicitudRepository.rechazar_atomica(solicitud_id, negocio_id)
        except SolicitudRevisionError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error
        rechazada = SolicitudRepository.buscar_por_id(solicitud_id)
        if not rechazada:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
        AvisoService.crear(
            solicitud["comedor_id"],
            "solicitud_rechazada",
            "Tu solicitud fue rechazada por el negocio.",
            solicitud_id,
        )
        return rechazada
