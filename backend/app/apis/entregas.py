from fastapi import APIRouter, Depends, HTTPException

from app.core.seguridad import get_current_user
from app.repositories.entrega_repository import EntregaRepository
from app.services.voluntario_service import VoluntarioService


router = APIRouter(prefix="/api/entregas", tags=["entregas"])


@router.get("/abiertas")
def listar_abiertas(usuario_actual: dict = Depends(get_current_user)):
    rol = usuario_actual["rol"]
    if rol not in {"voluntario", "comedor", "negocio", "admin"}:
        raise HTTPException(status_code=403, detail="Rol no autorizado.")
    if rol == "voluntario" and not usuario_actual.get("disponible"):
        raise HTTPException(status_code=403, detail="El voluntario no está disponible.")
    if rol == "voluntario":
        entregas = EntregaRepository.listar_abiertas(usuario_actual["id"])
    elif rol == "comedor":
        entregas = EntregaRepository.listar_abiertas_para_comedor(usuario_actual["id"])
    elif rol == "negocio":
        entregas = EntregaRepository.listar_abiertas_para_negocio(usuario_actual["id"])
    else:
        entregas = EntregaRepository.listar_abiertas_para(None)
    return VoluntarioService.filtrar_telefonos(entregas, usuario_actual)
