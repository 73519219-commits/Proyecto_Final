from __future__ import annotations

from typing import Any

from app.repositories.aviso_repository import AvisoRepository


class AvisoService:
    @staticmethod
    def crear(
        usuario_destino: int,
        tipo: str,
        mensaje: str,
        referencia_id: int,
    ) -> dict[str, Any] | None:
        return AvisoRepository.crear(usuario_destino, tipo, mensaje, referencia_id)

    @staticmethod
    def listar(usuario_destino: int) -> list[dict[str, Any]]:
        return AvisoRepository.listar(usuario_destino)

    @staticmethod
    def marcar_leido(aviso_id: int, usuario_destino: int) -> dict[str, Any] | None:
        return AvisoRepository.marcar_leido(aviso_id, usuario_destino)
