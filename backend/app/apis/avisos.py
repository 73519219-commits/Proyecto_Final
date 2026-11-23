from fastapi import APIRouter, Depends, HTTPException

from app.core.seguridad import get_current_user
from app.schemas.aviso import AvisoOut
from app.services.aviso_service import AvisoService


router = APIRouter(prefix="/api/avisos", tags=["avisos"])


@router.get("/", response_model=list[AvisoOut])
def listar_mis_avisos(usuario_actual: dict = Depends(get_current_user)):
    return AvisoService.listar(usuario_actual["id"])


@router.patch("/{aviso_id}/leer", response_model=AvisoOut)
def leer_aviso(aviso_id: int, usuario_actual: dict = Depends(get_current_user)):
    aviso = AvisoService.marcar_leido(aviso_id, usuario_actual["id"])
    if not aviso:
        raise HTTPException(status_code=404, detail="Aviso no encontrado.")
    return aviso
