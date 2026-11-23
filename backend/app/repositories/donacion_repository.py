from __future__ import annotations

from typing import Any

from app.core.database import connection_scope, query_all, query_one


class DonacionRevisionError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class DonacionRepository:
    @staticmethod
    def listar() -> list[dict[str, Any]]:
        return query_all(
            """
            SELECT id, nombre_alimento, descripcion, cantidad, unidad,
                   fecha_vencimiento, direccion_recojo, hora_disponible,
                   estado, usuario_negocio_id
            FROM dbo.donaciones ORDER BY id
            """
        )

    @staticmethod
    def buscar_por_id(donacion_id: int) -> dict[str, Any] | None:
        return query_one(
            """
            SELECT id, nombre_alimento, descripcion, cantidad, unidad,
                   fecha_vencimiento, direccion_recojo, hora_disponible,
                   estado, usuario_negocio_id
            FROM dbo.donaciones WHERE id = ?
            """,
            donacion_id,
        )

    @staticmethod
    def crear(donacion: dict[str, Any]) -> dict[str, Any]:
        return query_one(
            """
            INSERT INTO dbo.donaciones
                (nombre_alimento, descripcion, cantidad, unidad, fecha_vencimiento,
                 direccion_recojo, hora_disponible, estado, usuario_negocio_id)
            OUTPUT INSERTED.id, INSERTED.nombre_alimento, INSERTED.descripcion,
                   INSERTED.cantidad, INSERTED.unidad, INSERTED.fecha_vencimiento,
                   INSERTED.direccion_recojo, INSERTED.hora_disponible,
                   INSERTED.estado, INSERTED.usuario_negocio_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            donacion["nombre_alimento"],
            donacion["descripcion"],
            donacion["cantidad"],
            donacion["unidad"],
            donacion["fecha_vencimiento"],
            donacion["direccion_recojo"],
            donacion["hora_disponible"],
            donacion["estado"],
            donacion["usuario_negocio_id"],
        )

    @staticmethod
    def actualizar(donacion_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        columnas = {
            "nombre_alimento",
            "descripcion",
            "cantidad",
            "unidad",
            "fecha_vencimiento",
            "direccion_recojo",
            "hora_disponible",
            "estado",
            "usuario_negocio_id",
        }
        cambios = {campo: valor for campo, valor in datos.items() if campo in columnas}
        if not cambios:
            return DonacionRepository.buscar_por_id(donacion_id)
        asignaciones = ", ".join(f"{campo} = ?" for campo in cambios)
        return query_one(
            f"""
            UPDATE dbo.donaciones SET {asignaciones}
            OUTPUT INSERTED.id, INSERTED.nombre_alimento, INSERTED.descripcion,
                   INSERTED.cantidad, INSERTED.unidad, INSERTED.fecha_vencimiento,
                   INSERTED.direccion_recojo, INSERTED.hora_disponible,
                   INSERTED.estado, INSERTED.usuario_negocio_id
            WHERE id = ?
            """,
            *cambios.values(),
            donacion_id,
        )

    @staticmethod
    def cancelar_atomica(donacion_id: int) -> None:
        with connection_scope() as connection:
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            cursor.execute(
                """
                SELECT id
                FROM dbo.solicitudes WITH (UPDLOCK, HOLDLOCK)
                WHERE donacion_id = ?
                ORDER BY id
                """,
                donacion_id,
            )
            cursor.fetchall()
            cursor.execute(
                "SELECT estado FROM dbo.donaciones WITH (UPDLOCK, HOLDLOCK) WHERE id = ?",
                donacion_id,
            )
            fila = cursor.fetchone()
            if fila is None:
                raise DonacionRevisionError(404, "Donación no encontrada.")
            if fila[0] in {"cancelada", "entregada"}:
                raise DonacionRevisionError(
                    409,
                    f"No se puede cancelar una donación en estado '{fila[0]}'.",
                )
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM dbo.solicitudes s WITH (UPDLOCK, HOLDLOCK)
                LEFT JOIN dbo.entregas e WITH (UPDLOCK, HOLDLOCK)
                  ON e.solicitud_id = s.id
                WHERE s.donacion_id = ?
                  AND (s.estado = N'aprobada'
                       OR e.estado IN (N'aceptada', N'recogida', N'entregada'))
                """,
                donacion_id,
            )
            if int(cursor.fetchone()[0]) > 0:
                raise DonacionRevisionError(
                    409,
                    "Cancele primero las solicitudes aprobadas o complete sus entregas.",
                )
            cursor.execute(
                """
                UPDATE dbo.entregas
                SET estado = N'cancelada'
                WHERE solicitud_id IN (
                    SELECT id FROM dbo.solicitudes
                    WHERE donacion_id = ? AND estado = N'pendiente'
                ) AND estado = N'abierta'
                """,
                donacion_id,
            )
            cursor.execute(
                """
                UPDATE dbo.solicitudes
                SET estado = N'cancelada'
                WHERE donacion_id = ? AND estado = N'pendiente'
                """,
                donacion_id,
            )
            cursor.execute(
                """
                UPDATE dbo.donaciones
                SET estado = N'cancelada'
                WHERE id = ? AND estado IN (N'disponible', N'reservada')
                """,
                donacion_id,
            )
            if cursor.rowcount != 1:
                raise DonacionRevisionError(409, "La donación cambió mientras se procesaba la cancelación.")

    @staticmethod
    def marcar_entregada_atomica(donacion_id: int) -> None:
        with connection_scope() as connection:
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            cursor.execute(
                """
                SELECT id
                FROM dbo.solicitudes WITH (UPDLOCK, HOLDLOCK)
                WHERE donacion_id = ?
                ORDER BY id
                """,
                donacion_id,
            )
            cursor.fetchall()
            cursor.execute(
                "SELECT estado FROM dbo.donaciones WITH (UPDLOCK, HOLDLOCK) WHERE id = ?",
                donacion_id,
            )
            fila = cursor.fetchone()
            if fila is None:
                raise DonacionRevisionError(404, "Donación no encontrada.")
            if fila[0] == "entregada":
                return
            if fila[0] != "reservada":
                raise DonacionRevisionError(
                    409,
                    "La donación solo se puede marcar entregada tras aprobar solicitudes.",
                )
            cursor.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN e.estado = N'entregada' THEN 0 ELSE 1 END)
                FROM dbo.solicitudes s WITH (UPDLOCK, HOLDLOCK)
                LEFT JOIN dbo.entregas e WITH (UPDLOCK, HOLDLOCK)
                  ON e.solicitud_id = s.id
                WHERE s.donacion_id = ? AND s.estado = N'aprobada'
                """,
                donacion_id,
            )
            total, pendientes = cursor.fetchone()
            if not total or pendientes:
                raise DonacionRevisionError(
                    409,
                    "La donación no puede marcarse entregada hasta completar todas sus entregas aprobadas.",
                )
            cursor.execute(
                """
                UPDATE dbo.donaciones
                SET estado = N'entregada'
                WHERE id = ? AND estado = N'reservada'
                """,
                donacion_id,
            )
            if cursor.rowcount != 1:
                raise DonacionRevisionError(409, "La donación cambió mientras se procesaba la entrega.")

    @staticmethod
    def total_aprobado(donacion_id: int) -> int:
        fila = query_one(
            """
            SELECT COALESCE(SUM(cantidad_solicitada), 0) AS total
            FROM dbo.solicitudes
            WHERE donacion_id = ? AND estado = N'aprobada'
            """,
            donacion_id,
        )
        return int(fila["total"]) if fila else 0

    @staticmethod
    def tiene_solicitudes(donacion_id: int) -> bool:
        fila = query_one(
            "SELECT COUNT(*) AS total FROM dbo.solicitudes WHERE donacion_id = ?",
            donacion_id,
        )
        return bool(fila and fila["total"])

    @staticmethod
    def listar_disponibles() -> list[dict[str, Any]]:
        return query_all(
            """
            SELECT id, nombre_alimento, descripcion, cantidad, unidad,
                   fecha_vencimiento, direccion_recojo, hora_disponible,
                   estado, usuario_negocio_id
            FROM dbo.donaciones
            WHERE estado = N'disponible'
              AND fecha_vencimiento >= CONVERT(date, GETDATE())
            ORDER BY id
            """
        )
