from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.seguridad import get_current_user, require_roles
from app.schemas.solicitud import SolicitudCreate, SolicitudEstadoUpdate, SolicitudOut, SolicitudUpdate
from app.services.solicitud_service import SolicitudService

router = APIRouter(prefix="/api/solicitudes", tags=["solicitudes"])


@router.get("/", response_model=list[SolicitudOut])
def listar_solicitudes(usuario_actual: dict = Depends(get_current_user)):
    if usuario_actual["rol"] == "admin":
        return SolicitudService.listar_solicitudes()
    if usuario_actual["rol"] == "comedor":
        return SolicitudService.listar_por_comedor(usuario_actual["id"])
    raise HTTPException(status_code=403, detail="No tiene permisos para consultar solicitudes.")


@router.post("/", response_model=SolicitudOut, status_code=status.HTTP_201_CREATED)
def crear_solicitud(solicitud: SolicitudCreate, usuario_actual: dict = Depends(require_roles(["admin", "comedor"]))):
    if usuario_actual["rol"] == "comedor" and solicitud.comedor_id != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="Un comedor solo puede crear solicitudes para sí mismo.")
    return SolicitudService.registrar_solicitud(solicitud)


@router.put("/{solicitud_id}", response_model=SolicitudOut)
def actualizar_solicitud(solicitud_id: int, datos: SolicitudUpdate, usuario_actual: dict = Depends(get_current_user)):
    solicitud = SolicitudService.buscar_por_id(solicitud_id)
    if usuario_actual["rol"] != "admin" and solicitud["comedor_id"] != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="No puede modificar esta solicitud.")
    return SolicitudService.actualizar_solicitud(solicitud_id, datos)


@router.patch("/{solicitud_id}/estado", response_model=SolicitudOut)
def cambiar_estado_solicitud(
    solicitud_id: int,
    cambio: SolicitudEstadoUpdate,
    usuario_actual: dict = Depends(get_current_user),
):
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo el administrador puede cambiar el estado de la solicitud.")
    return SolicitudService.cambiar_estado(solicitud_id, cambio.estado)
