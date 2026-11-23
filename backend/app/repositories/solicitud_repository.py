from __future__ import annotations

from typing import Any
from datetime import date

from app.core.database import connection_scope, query_all, query_one


class SolicitudRevisionError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class SolicitudRepository:
    @staticmethod
    def listar() -> list[dict[str, Any]]:
        return query_all(
            """
            SELECT s.id, s.donacion_id, s.comedor_id, s.cantidad_solicitada,
                   s.tipo_apoyo, s.necesita_apoyo, s.estado,
                   d.usuario_negocio_id,
                   CASE WHEN s.estado = N'aprobada'
                        THEN negocio.telefono ELSE NULL END AS telefono_negocio,
                   CASE WHEN s.estado = N'aprobada'
                        THEN comedor.telefono ELSE NULL END AS telefono_comedor
            FROM dbo.solicitudes s
            JOIN dbo.donaciones d ON d.id = s.donacion_id
            JOIN dbo.usuarios negocio ON negocio.id = d.usuario_negocio_id
            JOIN dbo.usuarios comedor ON comedor.id = s.comedor_id
            ORDER BY s.id
            """
        )

    @staticmethod
    def buscar_por_id(solicitud_id: int) -> dict[str, Any] | None:
        return query_one(
            """
            SELECT s.id, s.donacion_id, s.comedor_id, s.cantidad_solicitada,
                   s.tipo_apoyo, s.necesita_apoyo, s.estado,
                   d.usuario_negocio_id,
                   CASE WHEN s.estado = N'aprobada'
                        THEN negocio.telefono ELSE NULL END AS telefono_negocio,
                   CASE WHEN s.estado = N'aprobada'
                        THEN comedor.telefono ELSE NULL END AS telefono_comedor
            FROM dbo.solicitudes s
            JOIN dbo.donaciones d ON d.id = s.donacion_id
            JOIN dbo.usuarios negocio ON negocio.id = d.usuario_negocio_id
            JOIN dbo.usuarios comedor ON comedor.id = s.comedor_id
            WHERE s.id = ?
            """,
            solicitud_id,
        )

    @staticmethod
    def crear(solicitud: dict[str, Any]) -> dict[str, Any]:
        return query_one(
            """
            INSERT INTO dbo.solicitudes
                (donacion_id, comedor_id, cantidad_solicitada, tipo_apoyo, necesita_apoyo, estado)
            OUTPUT INSERTED.id, INSERTED.donacion_id, INSERTED.comedor_id,
                   INSERTED.cantidad_solicitada, INSERTED.tipo_apoyo, INSERTED.necesita_apoyo, INSERTED.estado
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            solicitud["donacion_id"],
            solicitud["comedor_id"],
            solicitud["cantidad_solicitada"],
            solicitud["tipo_apoyo"],
            solicitud["necesita_apoyo"],
            solicitud["estado"],
        )

    @staticmethod
    def actualizar(solicitud_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        columnas = {"donacion_id", "comedor_id", "cantidad_solicitada", "tipo_apoyo", "necesita_apoyo", "estado"}
        cambios = {campo: valor for campo, valor in datos.items() if campo in columnas}
        if not cambios:
            return SolicitudRepository.buscar_por_id(solicitud_id)
        asignaciones = ", ".join(f"{campo} = ?" for campo in cambios)
        return query_one(
            f"""
            UPDATE dbo.solicitudes SET {asignaciones}
            OUTPUT INSERTED.id, INSERTED.donacion_id, INSERTED.comedor_id,
                   INSERTED.cantidad_solicitada, INSERTED.tipo_apoyo, INSERTED.necesita_apoyo, INSERTED.estado
            WHERE id = ?
            """,
            *cambios.values(),
            solicitud_id,
        )

    @staticmethod
    def rechazar_atomica(solicitud_id: int, negocio_id: int) -> None:
        with connection_scope() as connection:
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            cursor.execute(
                """
                SELECT s.estado, d.usuario_negocio_id
                FROM dbo.solicitudes s WITH (UPDLOCK, HOLDLOCK)
                JOIN dbo.donaciones d WITH (UPDLOCK, HOLDLOCK)
                  ON d.id = s.donacion_id
                WHERE s.id = ?
                """,
                solicitud_id,
            )
            fila = cursor.fetchone()
            if fila is None:
                raise SolicitudRevisionError(404, "Solicitud no encontrada.")
            if fila[0] != "pendiente":
                raise SolicitudRevisionError(409, "La solicitud ya fue revisada.")
            if fila[1] != negocio_id:
                raise SolicitudRevisionError(
                    403,
                    "Solo el negocio donante puede rechazar la solicitud.",
                )
            cursor.execute(
                """
                UPDATE dbo.solicitudes
                SET estado = N'rechazada'
                WHERE id = ? AND estado = N'pendiente'
                """,
                solicitud_id,
            )
            if cursor.rowcount != 1:
                raise SolicitudRevisionError(409, "La solicitud ya fue revisada.")

    @staticmethod
    def aprobar_atomica(
        solicitud_id: int,
        negocio_id: int,
        tipo_apoyo: str,
    ) -> None:
        with connection_scope() as connection:
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            cursor.execute(
                """
                SELECT s.id, s.donacion_id, s.comedor_id,
                       s.cantidad_solicitada, s.estado,
                       d.cantidad, d.fecha_vencimiento,
                       d.usuario_negocio_id, d.estado AS estado_donacion
                FROM dbo.solicitudes s WITH (UPDLOCK, HOLDLOCK)
                JOIN dbo.donaciones d WITH (UPDLOCK, HOLDLOCK)
                  ON d.id = s.donacion_id
                WHERE s.id = ?
                """,
                solicitud_id,
            )
            fila = cursor.fetchone()
            if fila is None:
                raise SolicitudRevisionError(404, "Solicitud no encontrada.")

            columnas = [descripcion[0] for descripcion in cursor.description]
            solicitud = dict(zip(columnas, fila, strict=True))
            if solicitud["estado"] != "pendiente":
                raise SolicitudRevisionError(409, "La solicitud ya fue revisada.")
            if solicitud["usuario_negocio_id"] != negocio_id:
                raise SolicitudRevisionError(
                    403,
                    "Solo el negocio donante puede aprobar la solicitud.",
                )
            if solicitud["estado_donacion"] not in {"disponible", "reservada"}:
                raise SolicitudRevisionError(
                    409,
                    "La donación no está disponible.",
                )
            fecha_vencimiento = solicitud.get("fecha_vencimiento")
            if fecha_vencimiento and str(fecha_vencimiento) < date.today().isoformat():
                raise SolicitudRevisionError(
                    400,
                    "La donación ya venció.",
                )

            cursor.execute(
                """
                SELECT COALESCE(SUM(cantidad_solicitada), 0) AS total_aprobado
                FROM dbo.solicitudes WITH (HOLDLOCK)
                WHERE donacion_id = ? AND estado = N'aprobada'
                """,
                solicitud["donacion_id"],
            )
            fila_total = cursor.fetchone()
            total_aprobado = int(fila_total[0]) if fila_total else 0
            cantidad_solicitada = int(solicitud["cantidad_solicitada"])
            cantidad_donacion = int(solicitud["cantidad"])
            if total_aprobado + cantidad_solicitada > cantidad_donacion:
                raise SolicitudRevisionError(
                    400,
                    "La suma aprobada supera la cantidad disponible de la donación.",
                )

            cursor.execute(
                """
                UPDATE dbo.solicitudes
                SET estado = N'aprobada',
                    tipo_apoyo = ?,
                    necesita_apoyo = ?
                WHERE id = ?
                """,
                tipo_apoyo,
                tipo_apoyo,
                solicitud_id,
            )

            cursor.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM dbo.entregas
                    WHERE solicitud_id = ?
                )
                BEGIN
                    INSERT INTO dbo.entregas
                        (solicitud_id, voluntario_id, fecha_asignacion,
                         fecha_entrega, estado, observaciones, tipo_apoyo, tipo)
                    VALUES (?, NULL, ?, NULL, N'abierta',
                            N'Misión creada al aprobar la solicitud.', ?, ?)
                END
                """,
                solicitud_id,
                solicitud_id,
                date.today(),
                tipo_apoyo,
                tipo_apoyo,
            )

            cursor.execute(
                """
                UPDATE dbo.donaciones
                SET estado = N'reservada'
                WHERE id = ?
                """,
                solicitud["donacion_id"],
            )

    @staticmethod
    def cancelar_atomica(solicitud_id: int) -> None:
        with connection_scope() as connection:
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            cursor.execute(
                """
                SELECT s.id, s.donacion_id, s.estado,
                       d.estado AS estado_donacion
                FROM dbo.solicitudes s WITH (UPDLOCK, HOLDLOCK)
                JOIN dbo.donaciones d WITH (UPDLOCK, HOLDLOCK)
                  ON d.id = s.donacion_id
                WHERE s.id = ?
                """,
                solicitud_id,
            )
            fila = cursor.fetchone()
            if fila is None:
                raise SolicitudRevisionError(404, "Solicitud no encontrada.")

            columnas = [descripcion[0] for descripcion in cursor.description]
            solicitud = dict(zip(columnas, fila, strict=True))
            if solicitud["estado"] not in {"pendiente", "aprobada"}:
                raise SolicitudRevisionError(
                    409,
                    f"No se puede cancelar una solicitud en estado '{solicitud['estado']}'.",
                )

            cursor.execute(
                """
                SELECT TOP 1 id, estado
                FROM dbo.entregas WITH (UPDLOCK, HOLDLOCK)
                WHERE solicitud_id = ?
                ORDER BY id
                """,
                solicitud_id,
            )
            fila_entrega = cursor.fetchone()
            entrega = None
            if fila_entrega is not None:
                entrega = {
                    "id": fila_entrega[0],
                    "estado": fila_entrega[1],
                }
                if entrega["estado"] == "entregada":
                    raise SolicitudRevisionError(
                        409,
                        "No se puede cancelar una solicitud cuya entrega fue completada.",
                    )

            cursor.execute(
                """
                UPDATE dbo.solicitudes
                SET estado = N'cancelada'
                WHERE id = ?
                """,
                solicitud_id,
            )

            if entrega is not None:
                cursor.execute(
                    """
                    UPDATE dbo.entregas
                    SET estado = N'cancelada'
                    WHERE id = ? AND estado IN
                        (N'abierta', N'aceptada', N'recogida')
                    """,
                    entrega["id"],
                )

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM dbo.solicitudes WITH (HOLDLOCK)
                WHERE donacion_id = ? AND estado = N'aprobada'
                """,
                solicitud["donacion_id"],
            )
            fila_total = cursor.fetchone()
            aprobadas_restantes = int(fila_total[0]) if fila_total else 0
            if (
                aprobadas_restantes == 0
                and solicitud["estado_donacion"] not in {"cancelada", "entregada"}
            ):
                cursor.execute(
                    """
                    UPDATE dbo.donaciones
                    SET estado = N'disponible'
                    WHERE id = ?
                    """,
                    solicitud["donacion_id"],
                )

    @staticmethod
    def listar_por_comedor(comedor_id: int) -> list[dict[str, Any]]:
        return query_all(
            """
            SELECT s.id, s.donacion_id, s.comedor_id, s.cantidad_solicitada,
                   s.tipo_apoyo, s.necesita_apoyo, s.estado,
                   d.usuario_negocio_id,
                   CASE WHEN s.estado = N'aprobada'
                        THEN negocio.telefono ELSE NULL END AS telefono_negocio,
                   CASE WHEN s.estado = N'aprobada'
                        THEN comedor.telefono ELSE NULL END AS telefono_comedor
            FROM dbo.solicitudes s
            JOIN dbo.donaciones d ON d.id = s.donacion_id
            JOIN dbo.usuarios negocio ON negocio.id = d.usuario_negocio_id
            JOIN dbo.usuarios comedor ON comedor.id = s.comedor_id
            WHERE s.comedor_id = ? ORDER BY s.id
            """,
            comedor_id,
        )

    @staticmethod
    def listar_por_negocio(negocio_id: int) -> list[dict[str, Any]]:
        return query_all(
            """
            SELECT s.id, s.donacion_id, s.comedor_id,
                   s.cantidad_solicitada, s.tipo_apoyo, s.necesita_apoyo, s.estado,
                   d.usuario_negocio_id,
                   CASE WHEN s.estado = N'aprobada'
                        THEN negocio.telefono ELSE NULL END AS telefono_negocio,
                   CASE WHEN s.estado = N'aprobada'
                        THEN comedor.telefono ELSE NULL END AS telefono_comedor
            FROM dbo.solicitudes s
            JOIN dbo.donaciones d ON d.id = s.donacion_id
            JOIN dbo.usuarios negocio ON negocio.id = d.usuario_negocio_id
            JOIN dbo.usuarios comedor ON comedor.id = s.comedor_id
            WHERE d.usuario_negocio_id = ? ORDER BY s.id
            """,
            negocio_id,
        )
