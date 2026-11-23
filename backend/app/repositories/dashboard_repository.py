from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.core.database import query_one


class DashboardRepository:
    @staticmethod
    def resumen(usuario: dict[str, Any]) -> dict[str, int | bool]:
        rol = usuario["rol"]
        usuario_id = usuario["id"]
        hoy = date.today()

        if rol == "negocio":
            fila = query_one(
                """
                SELECT
                  (SELECT COUNT(*) FROM dbo.donaciones
                   WHERE usuario_negocio_id = ? AND estado = N'disponible') AS publicaciones_activas,
                  (SELECT COUNT(*) FROM dbo.solicitudes s
                   JOIN dbo.donaciones d ON d.id = s.donacion_id
                   WHERE d.usuario_negocio_id = ? AND s.estado = N'pendiente') AS solicitudes_por_aprobar,
                  (SELECT COALESCE(SUM(d.cantidad), 0)
                   FROM dbo.entregas e
                   JOIN dbo.solicitudes s ON s.id = e.solicitud_id
                   JOIN dbo.donaciones d ON d.id = s.donacion_id
                   WHERE d.usuario_negocio_id = ? AND e.estado = N'entregada'
                     AND e.fecha_entrega >= ? AND e.fecha_entrega < ?) AS kg_donados_mes,
                  (SELECT COUNT(*) FROM dbo.donaciones
                   WHERE usuario_negocio_id = ? AND estado = N'disponible'
                     AND fecha_vencimiento >= ? AND fecha_vencimiento < ?) AS por_vencer
                """,
                usuario_id,
                usuario_id,
                usuario_id,
                hoy.replace(day=1),
                (hoy.replace(day=28) + timedelta(days=4)).replace(day=1),
                usuario_id,
                hoy,
                hoy + timedelta(days=1),
            )
            return fila or {}

        if rol == "comedor":
            fila = query_one(
                """
                SELECT
                  (SELECT COUNT(*) FROM dbo.donaciones
                   WHERE estado = N'disponible' AND fecha_vencimiento >= ?) AS disponibles_ahora,
                  (SELECT COUNT(*) FROM dbo.solicitudes
                   WHERE comedor_id = ? AND estado IN (N'pendiente', N'aprobada')) AS mis_solicitudes_activas,
                  (SELECT COUNT(*) FROM dbo.entregas e
                   JOIN dbo.solicitudes s ON s.id = e.solicitud_id
                   WHERE s.comedor_id = ? AND e.estado = N'recogida') AS por_confirmar,
                  (SELECT COALESCE(SUM(d.cantidad), 0) FROM dbo.entregas e
                   JOIN dbo.solicitudes s ON s.id = e.solicitud_id
                   JOIN dbo.donaciones d ON d.id = s.donacion_id
                   WHERE s.comedor_id = ? AND e.estado = N'entregada') AS raciones_recibidas
                """,
                hoy,
                usuario_id,
                usuario_id,
                usuario_id,
            )
            return fila or {}

        if rol == "voluntario":
            fila = query_one(
                """
                SELECT
                  (SELECT CASE WHEN disponible = 1 THEN 1 ELSE 0 END
                   FROM dbo.usuarios WHERE id = ?) AS disponible_hoy,
                  (SELECT COUNT(*) FROM dbo.entregas e
                   WHERE e.estado = N'abierta'
                     AND NOT EXISTS (
                       SELECT 1 FROM dbo.rechazos_mision r
                       WHERE r.entrega_id = e.id AND r.voluntario_id = ?
                     )) AS misiones_abiertas,
                  (SELECT COUNT(*) FROM dbo.entregas
                   WHERE voluntario_id = ? AND estado IN (N'aceptada', N'recogida')) AS mi_mision_activa,
                  (SELECT COALESCE(SUM(d.cantidad), 0) FROM dbo.entregas e
                   JOIN dbo.solicitudes s ON s.id = e.solicitud_id
                   JOIN dbo.donaciones d ON d.id = s.donacion_id
                   WHERE e.voluntario_id = ? AND e.estado = N'entregada') AS kg_transportados
                """,
                usuario_id,
                usuario_id,
                usuario_id,
                usuario_id,
            )
            return fila or {}

        if rol == "admin":
            fila = query_one(
                """
                SELECT
                  (SELECT COUNT(*) FROM dbo.donaciones) AS total_donaciones,
                  (SELECT COUNT(*) FROM dbo.solicitudes) AS total_solicitudes,
                  (SELECT COUNT(*) FROM dbo.entregas) AS total_entregas,
                  (SELECT COUNT(*) FROM dbo.usuarios
                   WHERE rol = N'voluntario' AND disponible = 1) AS voluntarios_disponibles_hoy,
                  (SELECT COUNT(*) FROM dbo.entregas
                   WHERE estado = N'abierta' AND voluntario_id IS NULL) AS misiones_sin_voluntario
                """
            )
            return fila or {}

        return {}
