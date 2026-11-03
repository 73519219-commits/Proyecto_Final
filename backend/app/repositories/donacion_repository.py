from __future__ import annotations

from typing import Any

from app.data.memoria import donaciones


class DonacionRepository:
    @staticmethod
    def listar() -> list[dict[str, Any]]:
        return [donacion.copy() for donacion in donaciones]

    @staticmethod
    def buscar_por_id(donacion_id: int) -> dict[str, Any] | None:
        for donacion in donaciones:
            if donacion["id"] == donacion_id:
                return donacion.copy()
        return None

    @staticmethod
    def crear(donacion: dict[str, Any]) -> dict[str, Any]:
        nuevo_id = max((item["id"] for item in donaciones), default=0) + 1
        donacion_con_id = {"id": nuevo_id, **donacion}
        donaciones.append(donacion_con_id)
        return donacion_con_id.copy()

    @staticmethod
    def actualizar(donacion_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        for index, donacion in enumerate(donaciones):
            if donacion["id"] == donacion_id:
                donaciones[index].update(datos)
                return donaciones[index].copy()
        return None

    @staticmethod
    def eliminar(donacion_id: int) -> bool:
        for index, donacion in enumerate(donaciones):
            if donacion["id"] == donacion_id:
                donaciones[index]["estado"] = "cancelada"
                return True
        return False

    @staticmethod
    def listar_disponibles() -> list[dict[str, Any]]:
        return [donacion.copy() for donacion in donaciones if donacion.get("estado") == "disponible"]
