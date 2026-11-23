from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.core.database import query_one

router = APIRouter(tags=["estado"])


@router.get("/api/health/database")
def estado_base_de_datos() -> dict[str, str]:
    result = query_one("SELECT DB_NAME() AS database_name")
    if result is None or result["database_name"] != settings.database.name:
        raise RuntimeError("SQL Server devolvió una base de datos inesperada.")
    return {"status": "ok", "database": str(result["database_name"]), "provider": "SQL Server"}
