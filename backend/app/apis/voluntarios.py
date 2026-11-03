from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.seguridad import get_current_user, require_roles
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.entrega import EntregaCreate, EntregaEstadoUpdate, EntregaOut, EntregaUpdate
from app.services.voluntario_service import VoluntarioService

router = APIRouter(prefix="/api/voluntarios", tags=["voluntarios"])


@router.get("/entregas", response_model=list[EntregaOut])
def listar_entregas(usuario_actual: dict = Depends(get_current_user)):
    if usuario_actual["rol"] == "admin":
        return VoluntarioService.listar_entregas()
    if usuario_actual["rol"] == "voluntario":
        return VoluntarioService.listar_por_voluntario(usuario_actual["id"])
    raise HTTPException(status_code=403, detail="Solo los voluntarios o el administrador pueden consultar entregas.")


@router.post("/entregas/{entrega_id}/aceptar", response_model=EntregaOut)
def aceptar_entrega(
    entrega_id: int,
    usuario_actual: dict = Depends(require_roles(["admin", "voluntario"])),
):
    entrega = VoluntarioService.obtener_entrega(entrega_id)
    if usuario_actual["rol"] == "voluntario" and entrega.get("voluntario_id") not in (None, 0, usuario_actual["id"]):
        raise HTTPException(status_code=403, detail="No puede aceptar una entrega asignada a otro voluntario.")
    if usuario_actual["rol"] == "voluntario":
        return VoluntarioService.aceptar_entrega(entrega_id, usuario_actual["id"])
    return VoluntarioService.aceptar_entrega(entrega_id, 0)


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
    return VoluntarioService.actualizar_estado(entrega_id, cambio.estado)
