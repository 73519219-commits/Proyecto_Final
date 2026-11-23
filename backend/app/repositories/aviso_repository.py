from __future__ import annotations

from typing import Any

from app.core.database import execute, query_all, query_one


class AvisoRepository:
    @staticmethod
    def crear(
        usuario_destino: int,
        tipo: str,
        mensaje: str,
        referencia_id: int,
    ) -> dict[str, Any] | None:
        return query_one(
            """
            INSERT INTO dbo.avisos
                (usuario_destino, tipo, mensaje, referencia_id, leido)
            OUTPUT INSERTED.id, INSERTED.usuario_destino, INSERTED.tipo,
                   INSERTED.mensaje, INSERTED.referencia_id, INSERTED.leido,
                   INSERTED.created_at
            VALUES (?, ?, ?, ?, 0)
            """,
            usuario_destino,
            tipo,
            mensaje,
            referencia_id,
        )

    @staticmethod
    def listar(usuario_destino: int) -> list[dict[str, Any]]:
        return query_all(
            """
            SELECT id, usuario_destino, tipo, mensaje, referencia_id,
                   leido, created_at
            FROM dbo.avisos
            WHERE usuario_destino = ?
            ORDER BY created_at DESC, id DESC
            """,
            usuario_destino,
        )

    @staticmethod
    def marcar_leido(aviso_id: int, usuario_destino: int) -> dict[str, Any] | None:
        return query_one(
            """
            UPDATE dbo.avisos SET leido = 1
            OUTPUT INSERTED.id, INSERTED.usuario_destino, INSERTED.tipo,
                   INSERTED.mensaje, INSERTED.referencia_id, INSERTED.leido,
                   INSERTED.created_at
            WHERE id = ? AND usuario_destino = ?
            """,
            aviso_id,
            usuario_destino,
        )
