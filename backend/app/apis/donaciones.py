from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.seguridad import get_current_user, require_roles
from app.schemas.donacion import DonacionCreate, DonacionOut, DonacionUpdate
from app.services.donacion_service import DonacionService

router = APIRouter(prefix="/api/donaciones", tags=["donaciones"])


@router.get("/", response_model=list[DonacionOut])
def listar_donaciones(usuario_actual: dict = Depends(get_current_user)):
    if usuario_actual["rol"] == "negocio":
        return [donacion for donacion in DonacionService.listar_donaciones() if donacion["usuario_negocio_id"] == usuario_actual["id"]]
    if usuario_actual["rol"] == "admin":
        return DonacionService.listar_donaciones()
    if usuario_actual["rol"] in {"comedor", "voluntario"}:
        return DonacionService.listar_disponibles()
    raise HTTPException(status_code=403, detail="Rol no autorizado.")


@router.get("/disponibles", response_model=list[DonacionOut])
def listar_disponibles(usuario_actual: dict = Depends(get_current_user)):
    if usuario_actual["rol"] not in {"admin", "comedor", "voluntario"}:
        raise HTTPException(status_code=403, detail="No tiene permisos para consultar donaciones disponibles.")
    return DonacionService.listar_disponibles()


@router.post("/", response_model=DonacionOut, status_code=status.HTTP_201_CREATED)
def crear_donacion(
    donacion: DonacionCreate,
    usuario_actual: dict = Depends(require_roles(["admin", "negocio"])),
):
    if usuario_actual["rol"] == "negocio" and donacion.usuario_negocio_id != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="Un negocio solo puede registrar sus propias donaciones.")
    return DonacionService.registrar_donacion(donacion)


@router.put("/{donacion_id}", response_model=DonacionOut)
def actualizar_donacion(
    donacion_id: int,
    datos: DonacionUpdate,
    usuario_actual: dict = Depends(get_current_user),
):
    donacion = DonacionService.buscar_por_id(donacion_id)
    if usuario_actual["rol"] != "admin" and donacion["usuario_negocio_id"] != usuario_actual["id"]:
        raise HTTPException(status_code=403, detail="Solo puede editar sus propias donaciones.")
    return DonacionService.actualizar_donacion(donacion_id, datos)
