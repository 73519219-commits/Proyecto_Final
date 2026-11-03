from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException, status

from app.repositories.entrega_repository import EntregaRepository
from app.schemas.entrega import EntregaCreate, EntregaUpdate


class VoluntarioService:
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
        return [entrega for entrega in EntregaRepository.listar() if entrega.get("estado") in {"asignada", "en_transito"}]

    @staticmethod
    def aceptar_entrega(entrega_id: int, voluntario_id: int) -> dict[str, Any]:
        entrega = EntregaRepository.buscar_por_id(entrega_id)
        if not entrega:
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        if entrega.get("estado") == "entregada":
            raise HTTPException(status_code=400, detail="La entrega ya fue completada.")

        entrega["voluntario_id"] = voluntario_id
        entrega["estado"] = "asignada"
        entrega["fecha_asignacion"] = str(date.today())
        actualizado = EntregaRepository.actualizar(entrega_id, entrega)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo aceptar la entrega.")
        return actualizado

    @staticmethod
    def actualizar_estado(entrega_id: int, estado: str) -> dict[str, Any]:
        entrega = EntregaRepository.buscar_por_id(entrega_id)
        if not entrega:
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        entrega["estado"] = estado
        actualizado = EntregaRepository.actualizar(entrega_id, entrega)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo cambiar el estado.")
        return actualizado

    @staticmethod
    def registrar_entrega(datos: EntregaCreate) -> dict[str, Any]:
        return EntregaRepository.crear(datos.model_dump())

    @staticmethod
    def listar_por_voluntario(voluntario_id: int) -> list[dict[str, Any]]:
        return EntregaRepository.listar_por_voluntario(voluntario_id)

    @staticmethod
    def actualizar_entrega(entrega_id: int, datos: EntregaUpdate) -> dict[str, Any]:
        if not EntregaRepository.buscar_por_id(entrega_id):
            raise HTTPException(status_code=404, detail="Entrega no encontrada.")
        cambios = datos.model_dump(exclude_unset=True)
        actualizado = EntregaRepository.actualizar(entrega_id, cambios)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo editar la entrega.")
        return actualizado
