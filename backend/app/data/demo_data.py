from __future__ import annotations

from datetime import date, timedelta

from app.core.database import connection_scope
from app.core.seguridad import hash_password


def seed_demo_data() -> None:
    """Agrega las cuentas y los registros de demostración si la base está vacía."""
    hoy = date.today()
    usuarios = [
        ("Administrador", "Sistema", "admin@alimentosolidario.pe", "admin123", "987654321", "Jr. Puno 120", "admin"),
        ("Panadería", "San José", "negocio@panaderia.pe", "negocio123", "961234567", "Av. Real 320", "negocio"),
        ("Comedor", "Esperanza", "comedor@esperanza.pe", "comedor123", "991122334", "Jr. Progreso 80", "comedor"),
        ("Carlos", "Ruiz", "voluntario@correo.pe", "voluntario123", "965432100", "Urb. San Martín", "voluntario"),
    ]
    donaciones = [
        ("Pan de trigo", "Pan recién horneado en buen estado.", 40, "unidad", hoy + timedelta(days=30), "Av. Real 320", "08:00 - 10:00", "reservada"),
        ("Arroz", "Sacos de arroz sin daños en empaque.", 20, "kg", hoy + timedelta(days=45), "Av. Real 320", "09:00 - 12:00", "disponible"),
    ]

    with connection_scope() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM dbo.usuarios")
        if cursor.fetchone()[0]:
            return

        cursor.executemany(
            """
            INSERT INTO dbo.usuarios
                (nombres, apellidos, correo, password_hash, telefono, direccion, rol, disponible, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, N'activo')
            """,
            [
                (
                    *usuario[:3],
                    hash_password(usuario[3]),
                    *usuario[4:],
                    usuario[6] == "voluntario",
                )
                for usuario in usuarios
            ],
        )
        cursor.executemany(
            """
            INSERT INTO dbo.donaciones
                (nombre_alimento, descripcion, cantidad, unidad, fecha_vencimiento,
                 direccion_recojo, hora_disponible, estado, usuario_negocio_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 2)
            """,
            donaciones,
        )
        cursor.execute(
            """
            INSERT INTO dbo.solicitudes
                (donacion_id, comedor_id, cantidad_solicitada, estado)
            VALUES (1, 3, 10, N'aprobada')
            """
        )
        cursor.execute(
            """
            INSERT INTO dbo.entregas
                (solicitud_id, voluntario_id, fecha_asignacion, fecha_entrega,
                 estado, observaciones, tipo)
            VALUES (1, 4, ?, NULL, N'aceptada',
                    N'Entrega coordinada con la familia del comedor.', N'ambos')
            """,
            hoy,
        )
