from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.seguridad import get_current_user, require_roles
from app.schemas.solicitud import (
    SolicitudAprobacionUpdate,
    SolicitudCreate,
    SolicitudEstadoUpdate,
    SolicitudOut,
    SolicitudUpdate,
)
from app.services.solicitud_service import SolicitudService

router = APIRouter(prefix="/api/solicitudes", tags=["solicitudes"])


@router.get("/", response_model=list[SolicitudOut])
def listar_solicitudes(usuario_actual: dict = Depends(get_current_user)):
    if usuario_actual["rol"] == "admin":
        lista = SolicitudService.listar_solicitudes()
    elif usuario_actual["rol"] == "comedor":
        lista = SolicitudService.listar_por_comedor(usuario_actual["id"])
    elif usuario_actual["rol"] == "negocio":
        lista = SolicitudService.listar_por_negocio(usuario_actual["id"])
    else:
        raise HTTPException(status_code=403, detail="No tiene permisos para consultar solicitudes.")
    return SolicitudService.filtrar_telefonos(lista, usuario_actual)


@router.post("/", response_model=SolicitudOut, status_code=status.HTTP_201_CREATED)
def crear_solicitud(solicitud: SolicitudCreate, usuario_actual: dict = Depends(require_roles(["admin", "comedor"]))):
    if usuario_actual["rol"] == "comedor" and solicitud.comedor_id != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="Un comedor solo puede crear solicitudes para sí mismo.")
    creada = SolicitudService.registrar_solicitud(solicitud)
    return SolicitudService.filtrar_telefonos([creada], usuario_actual)[0]


@router.put("/{solicitud_id}", response_model=SolicitudOut)
def actualizar_solicitud(solicitud_id: int, datos: SolicitudUpdate, usuario_actual: dict = Depends(get_current_user)):
    solicitud = SolicitudService.buscar_por_id(solicitud_id)
    if usuario_actual["rol"] != "admin" and solicitud["comedor_id"] != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="No puede modificar esta solicitud.")
    if datos.estado in {"aprobada", "rechazada"}:
        raise HTTPException(status_code=403, detail="Solo el negocio donante puede aprobar o rechazar solicitudes.")
    actualizado = SolicitudService.actualizar_solicitud(solicitud_id, datos)
    return SolicitudService.filtrar_telefonos([actualizado], usuario_actual)[0]


@router.patch("/{solicitud_id}/estado", response_model=SolicitudOut)
def cambiar_estado_solicitud(
    solicitud_id: int,
    cambio: SolicitudEstadoUpdate,
    usuario_actual: dict = Depends(get_current_user),
):
    if cambio.estado in {"aprobada", "rechazada"}:
        raise HTTPException(status_code=403, detail="Solo el negocio donante puede aprobar o rechazar solicitudes.")
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo el administrador puede intervenir otros estados.")
    return SolicitudService.cambiar_estado(solicitud_id, cambio.estado)


@router.post("/{solicitud_id}/aprobar", response_model=SolicitudOut)
def aprobar_solicitud(
    solicitud_id: int,
    datos: SolicitudAprobacionUpdate,
    usuario_actual: dict = Depends(require_roles(["negocio"])),
):
    aprobada = SolicitudService.aprobar(solicitud_id, usuario_actual["id"], datos.tipo_apoyo)
    return SolicitudService.filtrar_telefonos([aprobada], usuario_actual)[0]


@router.post("/{solicitud_id}/rechazar", response_model=SolicitudOut)
def rechazar_solicitud(
    solicitud_id: int,
    usuario_actual: dict = Depends(require_roles(["negocio"])),
):
    return SolicitudService.rechazar(solicitud_id, usuario_actual["id"])


@router.delete("/{solicitud_id}")
def cancelar_solicitud(
    solicitud_id: int,
    usuario_actual: dict = Depends(get_current_user),
):
    solicitud = SolicitudService.buscar_por_id(solicitud_id)
    if usuario_actual["rol"] != "admin" and solicitud["comedor_id"] != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="No puede cancelar esta solicitud.")
    return SolicitudService.cancelar_solicitud(solicitud_id)
