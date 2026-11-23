from __future__ import annotations

from typing import Any

import pyodbc

from app.core.database import execute, query_all, query_one


class UsuarioCorreoDuplicado(Exception):
    pass


class UsuarioRepository:
    @staticmethod
    def listar(rol: str | None = None) -> list[dict[str, Any]]:
        consulta = """
            SELECT id, nombres, apellidos, correo, password_hash,
                   telefono, direccion, rol, disponible, estado
            FROM dbo.usuarios
        """
        if rol is not None:
            consulta += " WHERE rol = ?"
            return query_all(consulta + " ORDER BY id", rol)
        return query_all(consulta + " ORDER BY id")

    @staticmethod
    def buscar_por_id(usuario_id: int) -> dict[str, Any] | None:
        return query_one(
            """
            SELECT id, nombres, apellidos, correo, password_hash,
                   telefono, direccion, rol, disponible, estado
            FROM dbo.usuarios WHERE id = ?
            """,
            usuario_id,
        )

    @staticmethod
    def buscar_por_correo(correo: str) -> dict[str, Any] | None:
        return query_one(
            """
            SELECT id, nombres, apellidos, correo, password_hash,
                   telefono, direccion, rol, disponible, estado
            FROM dbo.usuarios WHERE correo = ?
            """,
            correo,
        )

    @staticmethod
    def crear(usuario: dict[str, Any]) -> dict[str, Any]:
        try:
            nuevo = query_one(
                """
                INSERT INTO dbo.usuarios
                    (nombres, apellidos, correo, password_hash,
                     telefono, direccion, rol, disponible, estado)
                OUTPUT INSERTED.id, INSERTED.nombres, INSERTED.apellidos,
                       INSERTED.correo, INSERTED.password_hash, INSERTED.telefono,
                       INSERTED.direccion, INSERTED.rol, INSERTED.disponible, INSERTED.estado
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                usuario["nombres"],
                usuario["apellidos"],
                usuario["correo"],
                usuario["password_hash"],
                usuario["telefono"],
                usuario["direccion"],
                usuario["rol"],
                usuario["disponible"],
                usuario["estado"],
            )
        except pyodbc.IntegrityError as error:
            if any(code in str(error) for code in ("2601", "2627")):
                raise UsuarioCorreoDuplicado from error
            raise
        if nuevo is None:
            raise RuntimeError("SQL Server no devolvió el usuario recién creado.")
        return nuevo

    @staticmethod
    def actualizar(usuario_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        columnas = {
            "nombres",
            "apellidos",
            "correo",
            "password_hash",
            "telefono",
            "direccion",
            "rol",
            "estado",
            "disponible",
        }
        cambios = {campo: valor for campo, valor in datos.items() if campo in columnas}
        if not cambios:
            return UsuarioRepository.buscar_por_id(usuario_id)
        asignaciones = ", ".join(f"{campo} = ?" for campo in cambios)
        return query_one(
            f"""
            UPDATE dbo.usuarios SET {asignaciones}
            OUTPUT INSERTED.id, INSERTED.nombres, INSERTED.apellidos,
                   INSERTED.correo, INSERTED.password_hash, INSERTED.telefono,
                   INSERTED.direccion, INSERTED.rol, INSERTED.disponible, INSERTED.estado
            WHERE id = ?
            """,
            *cambios.values(),
            usuario_id,
        )

    @staticmethod
    def eliminar(usuario_id: int) -> bool:
        return execute(
            "UPDATE dbo.usuarios SET estado = N'inactivo' WHERE id = ?",
            usuario_id,
        ) > 0
