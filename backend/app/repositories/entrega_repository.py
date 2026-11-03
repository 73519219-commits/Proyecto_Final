from __future__ import annotations

from typing import Any

from app.data.memoria import entregas


class EntregaRepository:
    @staticmethod
    def listar() -> list[dict[str, Any]]:
        return [entrega.copy() for entrega in entregas]

    @staticmethod
    def buscar_por_id(entrega_id: int) -> dict[str, Any] | None:
        for entrega in entregas:
            if entrega["id"] == entrega_id:
                return entrega.copy()
        return None

    @staticmethod
    def crear(entrega: dict[str, Any]) -> dict[str, Any]:
        nuevo_id = max((item["id"] for item in entregas), default=0) + 1
        entrega_con_id = {"id": nuevo_id, **entrega}
        entregas.append(entrega_con_id)
        return entrega_con_id.copy()

    @staticmethod
    def actualizar(entrega_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        for index, entrega in enumerate(entregas):
            if entrega["id"] == entrega_id:
                entregas[index].update(datos)
                return entregas[index].copy()
        return None

    @staticmethod
    def listar_pendientes() -> list[dict[str, Any]]:
        return [entrega.copy() for entrega in entregas if entrega.get("estado") == "pendiente"]

    @staticmethod
    def listar_por_voluntario(voluntario_id: int) -> list[dict[str, Any]]:
        return [entrega.copy() for entrega in entregas if entrega["voluntario_id"] == voluntario_id]
