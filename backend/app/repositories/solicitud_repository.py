from __future__ import annotations

from typing import Any

from app.data.memoria import solicitudes


class SolicitudRepository:
    @staticmethod
    def listar() -> list[dict[str, Any]]:
        return [solicitud.copy() for solicitud in solicitudes]

    @staticmethod
    def buscar_por_id(solicitud_id: int) -> dict[str, Any] | None:
        for solicitud in solicitudes:
            if solicitud["id"] == solicitud_id:
                return solicitud.copy()
        return None

    @staticmethod
    def crear(solicitud: dict[str, Any]) -> dict[str, Any]:
        nuevo_id = max((item["id"] for item in solicitudes), default=0) + 1
        solicitud_con_id = {"id": nuevo_id, **solicitud}
        solicitudes.append(solicitud_con_id)
        return solicitud_con_id.copy()

    @staticmethod
    def actualizar(solicitud_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        for index, solicitud in enumerate(solicitudes):
            if solicitud["id"] == solicitud_id:
                solicitudes[index].update(datos)
                return solicitudes[index].copy()
        return None

    @staticmethod
    def eliminar(solicitud_id: int) -> bool:
        for index, solicitud in enumerate(solicitudes):
            if solicitud["id"] == solicitud_id:
                solicitudes[index]["estado"] = "cancelada"
                return True
        return False

    @staticmethod
    def listar_por_comedor(comedor_id: int) -> list[dict[str, Any]]:
        return [solicitud.copy() for solicitud in solicitudes if solicitud["comedor_id"] == comedor_id]
