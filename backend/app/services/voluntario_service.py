from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.repositories.entrega_repository import EntregaRepository, EntregaRevisionError
from app.repositories.solicitud_repository import SolicitudRepository, SolicitudRevisionError
from app.repositories.donacion_repository import DonacionRepository
from app.schemas.entrega import EntregaCreate, EntregaUpdate
from app.services.aviso_service import AvisoService


class VoluntarioService:
    @staticmethod
    def filtrar_telefonos(
        entregas: list[dict[str, Any]],
        usuario_actual: dict[str, Any],
    ) -> list[dict[str, Any]]:
        resultado: list[dict[str, Any]] = []
        for entrega in entregas:
            visible = False
            if usuario_actual["rol"] == "admin":
                visible = entrega.get("estado") in {"aceptada", "recogida", "entregada"}
            elif usuario_actual["rol"] == "comedor":
                visible = entrega.get("comedor_id") == usuario_actual["id"]
            elif usuario_actual["rol"] == "negocio":
                visible = entrega.get("usuario_negocio_id") == usuario_actual["id"]
            elif usuario_actual["rol"] == "voluntario":
                visible = (
                    entrega.get("voluntario_id") == usuario_actual["id"]
                    and entrega.get("estado") in {"aceptada", "recogida", "entregada"}
                )
            if not visible:
                entrega = {
                    **entrega,
                    "telefono_negocio": None,
                    "telefono_comedor": None,
                }
            resultado.append(entrega)
        return resultado
    @staticmethod
    def obtener_entrega(entrega_id: int) -> dict[str, Any]:
        entrega = EntregaRepository.buscar_por_id(entrega_id)
        if not entrega:
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        return entrega

    @staticmethod
    def listar_entregas() -> list[dict[str, Any]]:
        return EntregaRepository.listar()

    @staticmethod
    def listar_pendientes() -> list[dict[str, Any]]:
        return EntregaRepository.listar_pendientes()

    @staticmethod
    def listar_asignadas() -> list[dict[str, Any]]:
        return [entrega for entrega in EntregaRepository.listar() if entrega.get("estado") in {"aceptada", "recogida"}]

    @staticmethod
    def listar_abiertas(voluntario_id: int) -> list[dict[str, Any]]:
        return EntregaRepository.listar_abiertas(voluntario_id)

    @staticmethod
    def listar_avisos(usuario_id: int) -> list[dict[str, Any]]:
        from app.services.aviso_service import AvisoService

        return AvisoService.listar(usuario_id)

    @staticmethod
    def aceptar_entrega(entrega_id: int, voluntario_id: int) -> dict[str, Any]:
        try:
            EntregaRepository.aceptar_atomica(entrega_id, voluntario_id)
        except EntregaRevisionError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error
        actualizado = EntregaRepository.buscar_por_id(entrega_id)
        if not actualizado:
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        entrega = actualizado
        solicitud = SolicitudRepository.buscar_por_id(entrega["solicitud_id"])
        if solicitud:
            AvisoService.crear(
                solicitud["comedor_id"], "mision_aceptada",
                "Un voluntario aceptó la misión y está en ruta.",
                entrega_id,
            )
            donacion = DonacionRepository.buscar_por_id(solicitud["donacion_id"])
            if donacion and entrega.get("tipo_apoyo") in {"recoger", "ambos"}:
                AvisoService.crear(
                    donacion["usuario_negocio_id"], "mision_aceptada",
                    "Un voluntario aceptó la misión y está en ruta al negocio.",
                    entrega_id,
                )
        return actualizado

    @staticmethod
    def rechazar_entrega(entrega_id: int, voluntario_id: int) -> dict[str, str]:
        entrega = EntregaRepository.buscar_por_id(entrega_id)
        if not entrega:
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        if entrega["estado"] != "abierta":
            raise HTTPException(status_code=409, detail="La misión ya no está abierta.")
        if not EntregaRepository.rechazar(entrega_id, voluntario_id):
            raise HTTPException(status_code=400, detail="No se pudo registrar el pase.")
        return {"mensaje": "Misión pasada correctamente."}

    @staticmethod
    def cambiar_estado_controlado(
        entrega_id: int, estado: str
    ) -> dict[str, Any]:
        entrega = EntregaRepository.buscar_por_id(entrega_id)
        if not entrega:
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        transiciones = {
            "recogida": {"aceptada"},
            "entregada": {"recogida"},
            "cancelada": {"abierta", "aceptada", "recogida"},
        }
        if estado not in transiciones or entrega["estado"] not in transiciones[estado]:
            raise HTTPException(status_code=409, detail="Transición de estado no válida.")
        if estado == "cancelada":
            try:
                SolicitudRepository.cancelar_atomica(entrega["solicitud_id"])
            except SolicitudRevisionError as error:
                raise HTTPException(
                    status_code=error.status_code,
                    detail=error.detail,
                ) from error
        else:
            try:
                EntregaRepository.cambiar_estado_atomico(
                    entrega_id,
                    entrega["estado"],
                    estado,
                )
            except EntregaRevisionError as error:
                raise HTTPException(
                    status_code=error.status_code,
                    detail=error.detail,
                ) from error
        actualizado = EntregaRepository.buscar_por_id(entrega_id)
        if not actualizado:
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        solicitud = SolicitudRepository.buscar_por_id(entrega["solicitud_id"])
        if solicitud:
            donacion = DonacionRepository.buscar_por_id(solicitud["donacion_id"])
            if estado == "recogida":
                AvisoService.crear(
                    solicitud["comedor_id"],
                    "entrega_recogida",
                    "La misión fue recogida por el voluntario.",
                    entrega_id,
                )
                if donacion:
                    AvisoService.crear(
                        donacion["usuario_negocio_id"],
                        "entrega_recogida",
                        "La misión fue recogida por el voluntario.",
                        entrega_id,
                    )
            if estado == "entregada":
                AvisoService.crear(
                    solicitud["comedor_id"],
                    "entrega_entregada",
                    "La entrega fue marcada y requiere tu confirmación de recepción.",
                    entrega_id,
                )
        return actualizado

    @staticmethod
    def actualizar_estado(entrega_id: int, estado: str) -> dict[str, Any]:
        return VoluntarioService.cambiar_estado_controlado(entrega_id, estado)

    @staticmethod
    def registrar_entrega(datos: EntregaCreate) -> dict[str, Any]:
        return EntregaRepository.crear(datos.model_dump())

    @staticmethod
    def listar_por_voluntario(voluntario_id: int) -> list[dict[str, Any]]:
        return EntregaRepository.listar_por_voluntario(voluntario_id)

    @staticmethod
    def listar_por_comedor(comedor_id: int) -> list[dict[str, Any]]:
        return EntregaRepository.listar_por_comedor(comedor_id)

    @staticmethod
    def actualizar_entrega(entrega_id: int, datos: EntregaUpdate) -> dict[str, Any]:
        if not EntregaRepository.buscar_por_id(entrega_id):
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        cambios = datos.model_dump(exclude_unset=True)
        actualizado = EntregaRepository.actualizar(entrega_id, cambios)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo editar la entrega.")
        return actualizado
