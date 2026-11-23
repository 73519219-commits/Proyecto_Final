from __future__ import annotations

from datetime import date
from typing import Any

from app.repositories.aviso_repository import AvisoRepository
from app.core.database import connection_scope, execute, query_all, query_one


class EntregaRevisionError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class EntregaRepository:
    @staticmethod
    def aceptar_atomica(entrega_id: int, voluntario_id: int) -> None:
        with connection_scope() as connection:
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            cursor.execute(
                """
                SELECT rol, estado, disponible
                FROM dbo.usuarios WITH (UPDLOCK, HOLDLOCK)
                WHERE id = ?
                """,
                voluntario_id,
            )
            voluntario = cursor.fetchone()
            if voluntario is None:
                raise EntregaRevisionError(404, "Voluntario no encontrado.")
            if voluntario[0] != "voluntario" or voluntario[1] != "activo":
                raise EntregaRevisionError(403, "Solo un voluntario activo puede aceptar misiones.")
            if not voluntario[2]:
                raise EntregaRevisionError(403, "Debe activar su disponibilidad para aceptar misiones.")

            cursor.execute(
                """
                SELECT estado, voluntario_id
                FROM dbo.entregas WITH (UPDLOCK, HOLDLOCK)
                WHERE id = ?
                """,
                entrega_id,
            )
            entrega = cursor.fetchone()
            if entrega is None:
                raise EntregaRevisionError(404, "Entrega no encontrada.")
            if entrega[0] != "abierta" or entrega[1] not in (None, voluntario_id):
                raise EntregaRevisionError(409, "La misión ya no está disponible.")

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM dbo.entregas WITH (UPDLOCK, HOLDLOCK)
                WHERE voluntario_id = ? AND estado IN (N'aceptada', N'recogida')
                """,
                voluntario_id,
            )
            if int(cursor.fetchone()[0]) > 0:
                raise EntregaRevisionError(409, "El voluntario ya tiene una misión activa.")

            cursor.execute(
                """
                UPDATE dbo.entregas
                SET voluntario_id = ?, estado = N'aceptada', fecha_asignacion = ?
                WHERE id = ? AND estado = N'abierta'
                  AND (voluntario_id IS NULL OR voluntario_id = ?)
                """,
                voluntario_id,
                date.today(),
                entrega_id,
                voluntario_id,
            )
            if cursor.rowcount != 1:
                raise EntregaRevisionError(409, "La misión ya no está disponible.")

    @staticmethod
    def cambiar_estado_atomico(
        entrega_id: int,
        estado_actual: str,
        estado_nuevo: str,
    ) -> None:
        with connection_scope() as connection:
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            cursor.execute(
                """
                SELECT s.donacion_id, s.estado
                FROM dbo.solicitudes s WITH (UPDLOCK, HOLDLOCK)
                JOIN dbo.entregas e ON e.solicitud_id = s.id
                WHERE e.id = ?
                """,
                entrega_id,
            )
            referencia = cursor.fetchone()
            if referencia is None:
                raise EntregaRevisionError(404, "Entrega no encontrada.")
            donacion_id, estado_solicitud = referencia
            cursor.execute(
                "SELECT id FROM dbo.donaciones WITH (UPDLOCK, HOLDLOCK) WHERE id = ?",
                donacion_id,
            )
            if cursor.fetchone() is None:
                raise EntregaRevisionError(404, "Donación no encontrada.")
            if estado_nuevo == "entregada" and estado_solicitud != "aprobada":
                raise EntregaRevisionError(
                    409,
                    "Solo una solicitud aprobada puede completar una entrega.",
                )
            cursor.execute(
                """
                UPDATE dbo.entregas
                SET estado = ?,
                    fecha_entrega = CASE WHEN ? = N'entregada'
                                         THEN CONVERT(date, GETDATE())
                                         ELSE fecha_entrega END
                WHERE id = ? AND estado = ?
                """,
                estado_nuevo,
                estado_nuevo,
                entrega_id,
                estado_actual,
            )
            if cursor.rowcount != 1:
                raise EntregaRevisionError(409, "La entrega cambió mientras se procesaba la operación.")

            if estado_nuevo == "entregada":
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM dbo.solicitudes s WITH (UPDLOCK, HOLDLOCK)
                    LEFT JOIN dbo.entregas e WITH (UPDLOCK, HOLDLOCK)
                      ON e.solicitud_id = s.id
                    WHERE s.donacion_id = ? AND s.estado = N'aprobada'
                      AND (e.id IS NULL OR e.estado NOT IN (N'entregada', N'cancelada'))
                    """,
                    donacion_id,
                )
                pendientes = int(cursor.fetchone()[0])
                if pendientes == 0:
                    cursor.execute(
                        """
                        UPDATE dbo.donaciones
                        SET estado = N'entregada'
                        WHERE id = ? AND estado = N'reservada'
                        """,
                        donacion_id,
                    )

    @staticmethod
    def _select() -> str:
        return """
            SELECT e.id, e.solicitud_id, COALESCE(e.voluntario_id, 0) AS voluntario_id,
                   e.fecha_asignacion, e.fecha_entrega, e.estado, e.observaciones,
                   e.tipo_apoyo, e.tipo,
                   s.comedor_id,
                   d.usuario_negocio_id,
                   d.direccion_recojo,
                   d.cantidad,
                   d.unidad,
                   d.hora_disponible,
                   CASE WHEN s.estado = N'aprobada'
                        THEN negocio.telefono ELSE NULL END AS telefono_negocio,
                   CASE WHEN s.estado = N'aprobada'
                        THEN comedor.telefono ELSE NULL END AS telefono_comedor
            FROM dbo.entregas e
            JOIN dbo.solicitudes s ON s.id = e.solicitud_id
            JOIN dbo.donaciones d ON d.id = s.donacion_id
            JOIN dbo.usuarios negocio ON negocio.id = d.usuario_negocio_id
            JOIN dbo.usuarios comedor ON comedor.id = s.comedor_id
        """

    @staticmethod
    def listar() -> list[dict[str, Any]]:
        return query_all(f"{EntregaRepository._select()} ORDER BY id")

    @staticmethod
    def buscar_por_id(entrega_id: int) -> dict[str, Any] | None:
        return query_one(
            f"{EntregaRepository._select()} WHERE e.id = ?",
            entrega_id,
        )

    @staticmethod
    def crear(entrega: dict[str, Any]) -> dict[str, Any]:
        return query_one(
            """
            INSERT INTO dbo.entregas
                (solicitud_id, voluntario_id, fecha_asignacion,
                 fecha_entrega, estado, observaciones, tipo_apoyo, tipo)
            OUTPUT INSERTED.id, INSERTED.solicitud_id,
                   COALESCE(INSERTED.voluntario_id, 0) AS voluntario_id,
                   INSERTED.fecha_asignacion, INSERTED.fecha_entrega,
                   INSERTED.estado, INSERTED.observaciones, INSERTED.tipo_apoyo, INSERTED.tipo
            VALUES (?, NULLIF(?, 0), ?, ?, ?, ?, ?, ?)
            """,
            entrega["solicitud_id"],
            entrega["voluntario_id"],
            entrega["fecha_asignacion"],
            entrega["fecha_entrega"],
            entrega["estado"],
            entrega["observaciones"],
            entrega["tipo_apoyo"],
            entrega["tipo"],
        )

    @staticmethod
    def actualizar(entrega_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        columnas = {
            "solicitud_id",
            "voluntario_id",
            "fecha_asignacion",
            "fecha_entrega",
            "estado",
            "observaciones",
            "tipo_apoyo",
            "tipo",
        }
        cambios = {campo: valor for campo, valor in datos.items() if campo in columnas}
        if not cambios:
            return EntregaRepository.buscar_por_id(entrega_id)
        valores = {
            campo: (None if valor == 0 else valor)
            if campo == "voluntario_id"
            else valor
            for campo, valor in cambios.items()
        }
        asignaciones = ", ".join(f"{campo} = ?" for campo in valores)
        return query_one(
            f"""
            UPDATE dbo.entregas SET {asignaciones}
            OUTPUT INSERTED.id, INSERTED.solicitud_id,
                   COALESCE(INSERTED.voluntario_id, 0) AS voluntario_id,
                   INSERTED.fecha_asignacion, INSERTED.fecha_entrega,
                   INSERTED.estado, INSERTED.observaciones, INSERTED.tipo_apoyo, INSERTED.tipo
            WHERE id = ?
            """,
            *valores.values(),
            entrega_id,
        )

    @staticmethod
    def listar_pendientes() -> list[dict[str, Any]]:
        return query_all(
            f"{EntregaRepository._select()} WHERE e.estado = N'abierta' ORDER BY e.id"
        )

    @staticmethod
    def listar_por_voluntario(voluntario_id: int) -> list[dict[str, Any]]:
        return query_all(
            f"{EntregaRepository._select()} WHERE e.voluntario_id = ? ORDER BY e.id",
            voluntario_id,
        )

    @staticmethod
    def listar_por_comedor(comedor_id: int) -> list[dict[str, Any]]:
        return query_all(
            f"""
            {EntregaRepository._select()}
            WHERE s.comedor_id = ? ORDER BY e.id
            """,
            comedor_id,
        )

    @staticmethod
    def listar_abiertas(voluntario_id: int) -> list[dict[str, Any]]:
        return query_all(
            f"""
            {EntregaRepository._select()}
            WHERE e.estado = N'abierta'
              AND NOT EXISTS (
                  SELECT 1 FROM dbo.rechazos_mision r
                  WHERE r.entrega_id = e.id AND r.voluntario_id = ?
              )
            ORDER BY e.id
            """,
            voluntario_id,
        )

    @staticmethod
    def listar_abiertas_para(voluntario_id: int | None) -> list[dict[str, Any]]:
        if voluntario_id is None:
            return query_all(
                f"{EntregaRepository._select()} WHERE e.estado = N'abierta' ORDER BY e.id"
            )
        return EntregaRepository.listar_abiertas(voluntario_id)

    @staticmethod
    def listar_abiertas_para_comedor(comedor_id: int) -> list[dict[str, Any]]:
        return query_all(
            f"""
            {EntregaRepository._select()}
            WHERE e.estado = N'abierta' AND s.comedor_id = ?
            ORDER BY e.id
            """,
            comedor_id,
        )

    @staticmethod
    def listar_abiertas_para_negocio(negocio_id: int) -> list[dict[str, Any]]:
        return query_all(
            f"""
            {EntregaRepository._select()}
            WHERE e.estado = N'abierta' AND d.usuario_negocio_id = ?
            ORDER BY e.id
            """,
            negocio_id,
        )

    @staticmethod
    def contar_activas(voluntario_id: int) -> int:
        fila = query_one(
            """
            SELECT COUNT(*) AS total FROM dbo.entregas
            WHERE voluntario_id = ? AND estado IN
                (N'aceptada', N'recogida')
            """,
            voluntario_id,
        )
        return int(fila["total"]) if fila else 0

    @staticmethod
    def rechazar(entrega_id: int, voluntario_id: int) -> bool:
        return execute(
            """
            IF NOT EXISTS (
                SELECT 1 FROM dbo.rechazos_mision
                WHERE entrega_id = ? AND voluntario_id = ?
            )
            INSERT INTO dbo.rechazos_mision (entrega_id, voluntario_id)
            VALUES (?, ?)
            """,
            entrega_id,
            voluntario_id,
            entrega_id,
            voluntario_id,
        ) > 0

    @staticmethod
    def crear_aviso(usuario_id: int, entrega_id: int, mensaje: str) -> dict[str, Any] | None:
        return AvisoRepository.crear(usuario_id, "mision", mensaje, entrega_id)

    @staticmethod
    def listar_avisos(usuario_id: int) -> list[dict[str, Any]]:
        return AvisoRepository.listar(usuario_id)
