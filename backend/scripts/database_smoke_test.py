"""Comprueba la conexión, escritura y lectura persistente de SQL Server.

Uso (desde ``backend``, con el servicio de SQL Server en ejecución):
    uv run python -m scripts.database_smoke_test
"""

from __future__ import annotations

from uuid import uuid4

from app.core.database import connection_scope, initialize_database, query_one
from app.core.seguridad import hash_password


def main() -> int:
    initialize_database()
    resultado = query_one(
        "SELECT DB_NAME() AS database_name, @@SERVERNAME AS server_name"
    )
    if resultado is None:
        raise RuntimeError("SQL Server no devolvió el resultado de la comprobación.")

    correo = f"db_smoke_{uuid4().hex}@example.test"
    usuario_id: int | None = None
    try:
        with connection_scope() as connection:
            row = connection.cursor().execute(
                """
                INSERT INTO dbo.usuarios
                    (nombres, apellidos, correo, password_hash,
                     telefono, direccion, rol, estado)
                OUTPUT INSERTED.id
                VALUES (N'Prueba', N'Conexión', ?, ?, N'000000000',
                        N'Prueba local', N'voluntario', N'activo')
                """,
                correo,
                hash_password(uuid4().hex),
            ).fetchone()
            if row is None:
                raise RuntimeError("SQL Server no devolvió el ID del registro de prueba.")
            usuario_id = int(row[0])

        guardado = query_one(
            "SELECT id, correo FROM dbo.usuarios WHERE id = ?",
            usuario_id,
        )
        if guardado is None or guardado["correo"] != correo:
            raise RuntimeError("El registro guardado no persistió entre conexiones.")
        print(
            "Conexión y persistencia SQL Server: OK "
            f"(servidor: {resultado['server_name']}, "
            f"base de datos: {resultado['database_name']})."
        )
        return 0
    finally:
        if usuario_id is not None:
            with connection_scope() as connection:
                connection.cursor().execute(
                    "DELETE FROM dbo.usuarios WHERE id = ?",
                    usuario_id,
                )


if __name__ == "__main__":
    raise SystemExit(main())
