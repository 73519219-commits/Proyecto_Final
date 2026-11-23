from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.seguridad import get_current_user, require_roles
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.solicitud_repository import SolicitudRepository
from app.repositories.donacion_repository import DonacionRepository
from app.schemas.entrega import EntregaCreate, EntregaEstadoUpdate, EntregaOut, EntregaUpdate
from app.services.voluntario_service import VoluntarioService

router = APIRouter(prefix="/api/voluntarios", tags=["voluntarios"])


@router.get("/entregas", response_model=list[EntregaOut])
def listar_entregas(usuario_actual: dict = Depends(get_current_user)):
    if usuario_actual["rol"] == "admin":
        lista = VoluntarioService.listar_entregas()
    if usuario_actual["rol"] == "voluntario":
        lista = VoluntarioService.listar_por_voluntario(usuario_actual["id"])
    elif usuario_actual["rol"] == "comedor":
        lista = VoluntarioService.listar_por_comedor(usuario_actual["id"])
    else:
        if usuario_actual["rol"] != "admin":
            raise HTTPException(status_code=403, detail="Solo los voluntarios o el administrador pueden consultar entregas.")
    return VoluntarioService.filtrar_telefonos(lista, usuario_actual)


@router.get("/entregas/abiertas", response_model=list[EntregaOut])
def listar_entregas_abiertas(
    usuario_actual: dict = Depends(require_roles(["voluntario"])),
):
    if not usuario_actual.get("disponible"):
        raise HTTPException(status_code=403, detail="Active su disponibilidad para ver misiones.")
    lista = VoluntarioService.listar_abiertas(usuario_actual["id"])
    return VoluntarioService.filtrar_telefonos(lista, usuario_actual)


@router.get("/avisos")
def listar_avisos(usuario_actual: dict = Depends(get_current_user)):
    return VoluntarioService.listar_avisos(usuario_actual["id"])


@router.post("/entregas/{entrega_id}/aceptar", response_model=EntregaOut)
def aceptar_entrega(
    entrega_id: int,
    usuario_actual: dict = Depends(require_roles(["voluntario"])),
):
    entrega = VoluntarioService.obtener_entrega(entrega_id)
    if usuario_actual["rol"] == "voluntario" and not usuario_actual.get("disponible"):
        raise HTTPException(status_code=403, detail="Debe activar su disponibilidad para aceptar misiones.")
    if usuario_actual["rol"] == "voluntario" and entrega.get("voluntario_id") not in (None, 0, usuario_actual["id"]):
        raise HTTPException(status_code=403, detail="No puede aceptar una entrega asignada a otro voluntario.")
    aceptada = VoluntarioService.aceptar_entrega(entrega_id, usuario_actual["id"])
    return VoluntarioService.filtrar_telefonos([aceptada], usuario_actual)[0]


@router.post("/entregas/{entrega_id}/pasar")
def pasar_entrega(
    entrega_id: int,
    usuario_actual: dict = Depends(require_roles(["voluntario"])),
):
    return VoluntarioService.rechazar_entrega(entrega_id, usuario_actual["id"])


@router.post("/entregas/{entrega_id}/recogido", response_model=EntregaOut)
def marcar_recogido(
    entrega_id: int,
    usuario_actual: dict = Depends(require_roles(["voluntario"])),
):
    entrega = VoluntarioService.obtener_entrega(entrega_id)
    if entrega.get("voluntario_id") != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="Solo el voluntario asignado puede marcar el recojo.")
    actualizada = VoluntarioService.cambiar_estado_controlado(entrega_id, "recogida")
    return VoluntarioService.filtrar_telefonos([actualizada], usuario_actual)[0]


@router.post("/entregas/{entrega_id}/entregado", response_model=EntregaOut)
def marcar_entregado(
    entrega_id: int,
    usuario_actual: dict = Depends(require_roles(["comedor"])),
):
    entrega = VoluntarioService.obtener_entrega(entrega_id)
    solicitud = SolicitudRepository.buscar_por_id(entrega["solicitud_id"])
    if not solicitud or solicitud["comedor_id"] != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="Solo el comedor receptor puede confirmar la entrega.")
    actualizada = VoluntarioService.cambiar_estado_controlado(entrega_id, "entregada")
    return VoluntarioService.filtrar_telefonos([actualizada], usuario_actual)[0]


@router.post("/entregas/{entrega_id}/confirmar", response_model=EntregaOut)
def confirmar_entrega(
    entrega_id: int,
    usuario_actual: dict = Depends(require_roles(["comedor"])),
):
    entrega = VoluntarioService.obtener_entrega(entrega_id)
    solicitud = SolicitudRepository.buscar_por_id(entrega["solicitud_id"])
    if not solicitud or solicitud["comedor_id"] != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="Solo el comedor receptor puede confirmar la recepción.")
    actualizada = VoluntarioService.cambiar_estado_controlado(entrega_id, "entregada")
    return VoluntarioService.filtrar_telefonos([actualizada], usuario_actual)[0]


@router.patch("/entregas/{entrega_id}/estado", response_model=EntregaOut)
def cambiar_estado_entrega(
    entrega_id: int,
    cambio: EntregaEstadoUpdate,
    usuario_actual: dict = Depends(get_current_user),
):
    if usuario_actual["rol"] != "admin" and usuario_actual["rol"] != "voluntario":
        raise HTTPException(status_code=403, detail="No tiene permisos para actualizar entregas.")
    entrega = VoluntarioService.obtener_entrega(entrega_id)
    if usuario_actual["rol"] == "voluntario" and entrega.get("voluntario_id") != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="Solo puede cambiar el estado de sus entregas asignadas.")
    if usuario_actual["rol"] == "voluntario" and cambio.estado == "entregada":
        raise HTTPException(status_code=403, detail="El comedor debe confirmar la entrega.")
    actualizada = VoluntarioService.actualizar_estado(entrega_id, cambio.estado)
    return VoluntarioService.filtrar_telefonos([actualizada], usuario_actual)[0]
