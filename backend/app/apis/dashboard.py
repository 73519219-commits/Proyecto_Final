from fastapi import APIRouter, Depends

from app.core.seguridad import get_current_user
from app.repositories.dashboard_repository import DashboardRepository


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/resumen")
def resumen(usuario_actual: dict = Depends(get_current_user)):
    return DashboardRepository.resumen(usuario_actual)
